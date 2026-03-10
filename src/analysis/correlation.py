"""
src/analysis/correlation.py

Funções de análise de correlação:
    - pearson_matrix     → Correlação de Pearson entre todas as variáveis
    - rolling_correlation → Correlação móvel para pares chave em janelas configuráveis
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from config.settings import ROLLING_WINDOWS


def pearson_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a matriz de correlação de Pearson.

    Args:
        df: DataFrame com colunas numéricas.

    Returns:
        DataFrame quadrado com coeficientes de Pearson (valores de -1 a 1).
    """
    return df.corr(method="pearson")


def rolling_correlation(
    df: pd.DataFrame,
    col_a: str = "ibovespa",
    col_b: str = "dolar_brl",
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """Calcula correlação de Pearson em janelas móveis entre dois ativos.

    Args:
        df:      DataFrame com as séries temporais.
        col_a:   Nome da primeira coluna.
        col_b:   Nome da segunda coluna.
        windows: Lista de tamanhos de janela em dias. Padrão: ROLLING_WINDOWS de settings.

    Returns:
        DataFrame com uma coluna por janela (ex.: corr_30d, corr_60d, corr_90d).
    """
    if windows is None:
        windows = ROLLING_WINDOWS

    result = pd.DataFrame(index=df.index)
    for w in windows:
        result[f"corr_{w}d"] = df[col_a].rolling(window=w).corr(df[col_b])

    return result


def correlation_significance(df: pd.DataFrame) -> pd.DataFrame:
    """Testa significância estatística (p-value) para cada par de colunas.

    Retorna DataFrame com colunas: pair, pearson_r, p_value, significant (α=0.05).
    """
    from scipy.stats import pearsonr

    cols = df.columns.tolist()
    records = []
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1 :]:
            valid = df[[c1, c2]].dropna()
            if len(valid) < 3:
                continue
            r, p = pearsonr(valid[c1], valid[c2])
            records.append(
                {
                    "par": f"{c1} × {c2}",
                    "pearson_r": round(r, 4),
                    "p_value": round(p, 6),
                    "significativo": p < 0.05,
                }
            )

    return pd.DataFrame(records)

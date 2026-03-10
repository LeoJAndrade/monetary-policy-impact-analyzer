"""
src/data/bcb_data.py

Coleta séries temporais do Banco Central do Brasil via biblioteca python-bcb
(usa internamente a API SGS do BCB).

Séries utilizadas:
    11    → Taxa Selic diária (% ao dia)
    13522 → IPCA acumulado 12 meses (%)
    1     → Taxa de câmbio USD/BRL (referência BCB)
"""

from __future__ import annotations

import pandas as pd
from bcb import sgs


SERIES = {
    "selic": 11,
    "ipca_12m": 13522,
    "cambio_bcb": 1,
}


def get_bcb_series(
    series_id: int,
    start: str,
    end: str | None = None,
) -> pd.Series:
    """Baixa uma série do SGS/BCB e retorna como pd.Series indexada por data.

    Args:
        series_id: Código numérico da série no SGS.
        start:     Data inicial 'YYYY-MM-DD'.
        end:       Data final   'YYYY-MM-DD'. None = hoje.

    Returns:
        pd.Series com os valores da série, indexada por datetime.
    """
    df = sgs.get({"valor": series_id}, start=start, end=end)
    series = df["valor"].dropna()
    series.index = pd.to_datetime(series.index)
    return series


def get_all_bcb_series(start: str, end: str | None = None) -> pd.DataFrame:
    """Baixa Selic, IPCA e câmbio BCB e combina em um único DataFrame.

    Returns:
        DataFrame indexado por data com colunas: selic, ipca_12m, cambio_bcb.
    """
    end_arg = end  # None → hoje (comportamento padrão do sgs.get)
    try:
        df = sgs.get(SERIES, start=start, end=end_arg)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as exc:
        raise RuntimeError(f"Falha ao carregar séries BCB: {exc}") from exc


if __name__ == "__main__":
    df = get_all_bcb_series("2020-01-01")
    print(df.tail(10))

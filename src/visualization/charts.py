"""
src/visualization/charts.py

Funções de visualização. Todos os gráficos são salvos em reports/ e retornam
o caminho do arquivo salvo.

Gráficos disponíveis:
    - dual_line_chart         → Ibovespa vs Dólar (2 eixos Y)
    - selic_vs_asset_chart    → Selic vs ativo (Ibovespa ou Dólar)
    - correlation_heatmap     → Heatmap de correlação de Pearson
    - rolling_correlation_chart → Correlações rolling por janela
    - forecast_chart          → Série real + previsão ARIMA com intervalo de confiança
    - feature_importance_chart → Importância de features (Random Forest)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # backend sem GUI (compatível com servidor/cron)

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

STYLE = "seaborn-v0_8-darkgrid"
plt.style.use(STYLE)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save(fig: plt.Figure, filename: str) -> Path:
    path = REPORTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] Salvo: {path}")
    return path


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def dual_line_chart(
    df: pd.DataFrame,
    col_a: str = "ibovespa",
    col_b: str = "dolar_brl",
    title: str = "Ibovespa vs Dólar (USD/BRL)",
    filename: str = "dual_line_ibovespa_dolar.png",
) -> Path:
    """Plota dois ativos em um mesmo eixo X com eixos Y independentes."""
    fig, ax1 = plt.subplots(figsize=(14, 5))

    color_a, color_b = "#1f77b4", "#d62728"

    ax1.plot(df.index, df[col_a], color=color_a, linewidth=1, label=col_a.replace("_", " ").title())
    ax1.set_ylabel(col_a.replace("_", " ").title(), color=color_a)
    ax1.tick_params(axis="y", labelcolor=color_a)

    ax2 = ax1.twinx()
    ax2.plot(df.index, df[col_b], color=color_b, linewidth=1, label=col_b.replace("_", " ").title())
    ax2.set_ylabel(col_b.replace("_", " ").title(), color=color_b)
    ax2.tick_params(axis="y", labelcolor=color_b)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()
    ax1.set_title(title, fontsize=14, fontweight="bold")

    return _save(fig, filename)


def selic_vs_asset_chart(
    df: pd.DataFrame,
    selic_col: str = "selic",
    asset_col: str = "ibovespa",
    filename: str | None = None,
) -> Path:
    """Plota a Selic vs qualquer ativo com dois eixos Y."""
    if filename is None:
        filename = f"selic_vs_{asset_col}.png"

    title = f"Selic (% a.a.) vs {asset_col.replace('_', ' ').title()}"
    return dual_line_chart(df, col_a=selic_col, col_b=asset_col, title=title, filename=filename)


def correlation_heatmap(
    corr_matrix: pd.DataFrame,
    title: str = "Heatmap de Correlação de Pearson",
    filename: str = "heatmap_correlacao.png",
) -> Path:
    """Gera heatmap a partir de uma matriz de correlação."""
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)   # oculta triângulo sup.
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(title, fontsize=13, fontweight="bold")
    return _save(fig, filename)


def rolling_correlation_chart(
    rolling_df: pd.DataFrame,
    col_a: str = "ibovespa",
    col_b: str = "dolar_brl",
    filename: str = "rolling_correlation.png",
) -> Path:
    """Plota correlações rolling para diferentes janelas."""
    fig, ax = plt.subplots(figsize=(14, 5))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for i, col in enumerate(rolling_df.columns):
        ax.plot(rolling_df.index, rolling_df[col], label=col, color=colors[i % len(colors)], linewidth=1.2)

    ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)
    ax.set_ylim(-1.1, 1.1)
    ax.set_ylabel("Correlação de Pearson")
    ax.set_title(
        f"Correlação Rolling: {col_a.replace('_', ' ').title()} × {col_b.replace('_', ' ').title()}",
        fontsize=13, fontweight="bold",
    )
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate()

    return _save(fig, filename)


def forecast_chart(
    historical: pd.Series,
    forecast: pd.Series,
    conf_int: pd.DataFrame | None = None,
    title: str = "Previsão ARIMA — Dólar (USD/BRL)",
    filename: str = "forecast_arima.png",
) -> Path:
    """Plota série histórica + previsão com intervalo de confiança."""
    fig, ax = plt.subplots(figsize=(14, 5))

    # últimos 12 meses de histórico para contexto visual
    cutoff = historical.index[-1] - pd.DateOffset(days=365)
    hist_window = historical.loc[historical.index >= cutoff] if len(historical) > 365 else historical

    ax.plot(hist_window.index, hist_window.values, label="Histórico", color="#1f77b4", linewidth=1.2)
    ax.plot(forecast.index, forecast.values, label="Previsão", color="#d62728", linewidth=1.5, linestyle="--")

    if conf_int is not None:
        ax.fill_between(
            forecast.index,
            conf_int.iloc[:, 0],
            conf_int.iloc[:, 1],
            alpha=0.2,
            color="#d62728",
            label="IC 95%",
        )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    fig.autofmt_xdate()

    return _save(fig, filename)


def feature_importance_chart(
    importance: pd.Series,
    title: str = "Importância de Features — Random Forest",
    filename: str = "feature_importance_rf.png",
) -> Path:
    """Gráfico de barras horizontais com importância das features."""
    fig, ax = plt.subplots(figsize=(8, max(4, len(importance) * 0.5)))
    importance.sort_values().plot(kind="barh", ax=ax, color="#1f77b4")
    ax.set_xlabel("Importância Relativa")
    ax.set_title(title, fontsize=13, fontweight="bold")
    return _save(fig, filename)

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
from datetime import date

import matplotlib

matplotlib.use("Agg")  # backend sem GUI (compatível com servidor/cron)

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
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


def export_plots_pdf(
    image_paths: list[Path],
    filename: str = "relatorio_plots.pdf",
    title: str = "PI-V — Relatorio Tecnico",
    subtitle: str | None = None,
    institution: str = "PI-V",
    author: str = "Sistema PI-V",
    city: str = "Sao Paulo",
) -> Path:
    """Consolida os plots em PDF com capa em formato proximo ao padrao ABNT."""
    out_path = REPORTS_DIR / filename

    valid_images = [Path(p) for p in image_paths if Path(p).exists()]
    if not valid_images:
        raise ValueError("Nenhuma imagem valida encontrada para gerar o PDF.")

    with PdfPages(out_path) as pdf:
        # Capa ABNT: instituicao (topo), autor, titulo/subtitulo (centro), local e ano (rodape)
        cover = plt.figure(figsize=(8.27, 11.69))  # A4 retrato
        cover.patch.set_facecolor("white")
        year = str(date.today().year)

        cover.text(
            0.5,
            0.93,
            institution.upper(),
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            family="serif",
        )
        cover.text(
            0.5,
            0.80,
            author.upper(),
            ha="center",
            va="center",
            fontsize=12,
            family="serif",
        )
        cover.text(
            0.5,
            0.56,
            title.upper(),
            ha="center",
            va="center",
            fontsize=18,
            fontweight="bold",
            family="serif",
        )
        if subtitle:
            cover.text(
                0.5,
                0.50,
                subtitle,
                ha="center",
                va="center",
                fontsize=11,
                family="serif",
            )
        cover.text(
            0.5,
            0.11,
            city.upper(),
            ha="center",
            va="center",
            fontsize=11,
            family="serif",
        )
        cover.text(
            0.5,
            0.08,
            year,
            ha="center",
            va="center",
            fontsize=11,
            family="serif",
        )
        pdf.savefig(cover)
        plt.close(cover)

        # Paginas de figuras em A4 retrato, com margens ABNT (3 cm sup/esq, 2 cm dir/inf).
        page_w_cm, page_h_cm = 21.0, 29.7
        margin_left_cm, margin_right_cm = 3.0, 2.0
        margin_top_cm, margin_bottom_cm = 3.0, 2.0
        usable_w_cm = page_w_cm - margin_left_cm - margin_right_cm
        usable_h_cm = page_h_cm - margin_top_cm - margin_bottom_cm

        def _norm(
            x_cm: float, y_cm: float, w_cm: float, h_cm: float
        ) -> tuple[float, float, float, float]:
            return (
                x_cm / page_w_cm,
                y_cm / page_h_cm,
                w_cm / page_w_cm,
                h_cm / page_h_cm,
            )

        # Reserva espacos fixos para legenda/fonte/paginacao e usa o restante para a figura.
        caption_space_cm = 1.2
        source_space_cm = 1.1
        page_number_space_cm = 1.0

        image_area_x_cm = margin_left_cm
        image_area_w_cm = usable_w_cm
        image_area_y_cm = margin_bottom_cm + source_space_cm + page_number_space_cm
        image_area_h_cm = (
            usable_h_cm - caption_space_cm - source_space_cm - page_number_space_cm
        )

        max_title_y = (image_area_y_cm + image_area_h_cm + 0.7) / page_h_cm
        source_y = (margin_bottom_cm + page_number_space_cm + 0.35) / page_h_cm
        page_number_y = (margin_bottom_cm * 0.5) / page_h_cm

        # Uma pagina por grafico
        for idx, img_path in enumerate(valid_images, start=1):
            fig = plt.figure(figsize=(8.27, 11.69))  # A4 retrato
            fig.patch.set_facecolor("white")

            # Legenda ABNT (acima da figura)
            img = plt.imread(img_path)
            img_h, img_w = img.shape[:2]
            img_ratio = img_w / img_h
            area_ratio = image_area_w_cm / image_area_h_cm

            # Ajuste por "contain": ocupa maximo de largura ou altura sem esticar.
            if img_ratio >= area_ratio:
                draw_w_cm = image_area_w_cm
                draw_h_cm = draw_w_cm / img_ratio
            else:
                draw_h_cm = image_area_h_cm
                draw_w_cm = draw_h_cm * img_ratio

            draw_x_cm = image_area_x_cm + (image_area_w_cm - draw_w_cm) / 2
            draw_y_cm = image_area_y_cm + (image_area_h_cm - draw_h_cm) / 2

            fig.text(
                0.5,
                max_title_y,
                f"Figura {idx} - {img_path.stem.replace('_', ' ').title()}",
                ha="center",
                va="center",
                fontsize=11,
                family="serif",
            )

            ax = fig.add_axes(_norm(draw_x_cm, draw_y_cm, draw_w_cm, draw_h_cm))
            ax.axis("off")
            ax.imshow(img, interpolation="none", resample=False)
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.8)
                spine.set_color("#222222")

            # Fonte abaixo da figura
            fig.text(
                0.5,
                source_y,
                "Fonte: Elaboracao propria (PI-V).",
                ha="center",
                va="center",
                fontsize=10,
                family="serif",
            )

            # Numeracao de pagina no rodape
            fig.text(
                0.5,
                page_number_y,
                str(idx + 1),
                ha="center",
                va="center",
                fontsize=10,
                family="serif",
            )

            pdf.savefig(fig)
            plt.close(fig)

    print(f"[chart] PDF consolidado salvo em: {out_path}")
    return out_path


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

    ax1.plot(
        df.index,
        df[col_a],
        color=color_a,
        linewidth=1,
        label=col_a.replace("_", " ").title(),
    )
    ax1.set_ylabel(col_a.replace("_", " ").title(), color=color_a)
    ax1.tick_params(axis="y", labelcolor=color_a)

    ax2 = ax1.twinx()
    ax2.plot(
        df.index,
        df[col_b],
        color=color_b,
        linewidth=1,
        label=col_b.replace("_", " ").title(),
    )
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
    return dual_line_chart(
        df, col_a=selic_col, col_b=asset_col, title=title, filename=filename
    )


def correlation_heatmap(
    corr_matrix: pd.DataFrame,
    title: str = "Heatmap de Correlação de Pearson",
    filename: str = "heatmap_correlacao.png",
) -> Path:
    """Gera heatmap a partir de uma matriz de correlação."""
    fig, ax = plt.subplots(figsize=(8, 6))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)  # oculta triângulo sup.
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
        ax.plot(
            rolling_df.index,
            rolling_df[col],
            label=col,
            color=colors[i % len(colors)],
            linewidth=1.2,
        )

    ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)
    ax.set_ylim(-1.1, 1.1)
    ax.set_ylabel("Correlação de Pearson")
    ax.set_title(
        f"Correlação Rolling: {col_a.replace('_', ' ').title()} × {col_b.replace('_', ' ').title()}",
        fontsize=13,
        fontweight="bold",
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
    hist_window = (
        historical.loc[historical.index >= cutoff]
        if len(historical) > 365
        else historical
    )

    ax.plot(
        hist_window.index,
        hist_window.values,
        label="Histórico",
        color="#1f77b4",
        linewidth=1.2,
    )
    ax.plot(
        forecast.index,
        forecast.values,
        label="Previsão",
        color="#d62728",
        linewidth=1.5,
        linestyle="--",
    )

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

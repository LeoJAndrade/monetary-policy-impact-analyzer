"""
main.py

Pipeline principal do projeto PI-V.

Fluxo:
    1. Coleta dados de mercado (yfinance) e do BCB (API SGS)
    2. Combina os DataFrames em um único dataset
    3. Análise de correlação (Pearson + rolling)
    4. Geração de gráficos
    5. Modelos preditivos (Regressão Linear, ARIMA, Random Forest)
    6. (Opcional) Envio de relatório por E-mail e/ou Telegram

Uso:
    python main.py                         # pipeline completo sem envio
    python main.py --email                 # pipeline + envio por e-mail
    python main.py --telegram              # pipeline + envio por Telegram
    python main.py --email --telegram      # ambos
    python main.py --start 2018-01-01      # período personalizado
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from datetime import date

# Garante que src/ e config/ sejam encontrados ao rodar da raiz do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import DEFAULT_START

from src.data.market_data import get_market_data
from src.data.bcb_data import get_all_bcb_series

from src.analysis.correlation import (
    pearson_matrix,
    rolling_correlation,
    correlation_significance,
)
from src.analysis.models import (
    linear_regression_model,
    arima_model,
    random_forest_model,
)

from src.visualization.charts import (
    dual_line_chart,
    selic_vs_asset_chart,
    correlation_heatmap,
    rolling_correlation_chart,
    forecast_chart,
    feature_importance_chart,
)

import pandas as pd
import json


REPORTS_DIR = Path(__file__).resolve().parent / "reports"


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def save_results_json(results: dict) -> Path:
    """Serializa métricas e metadados do pipeline para reports/results.json."""
    import numpy as np

    def _default(obj):
        """Serializa tipos numpy/pandas para JSON."""
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if hasattr(obj, 'isoformat'):   # Timestamp / datetime
            return obj.isoformat()
        return str(obj)

    pearson = results["correlations"]["pearson"]
    sig = results["correlations"]["significance"]
    lr = results["models"]["linear_regression"]
    rf = results["models"]["random_forest"]
    arima = results["models"]["arima"]

    payload = {
        "pearson_matrix": pearson.round(4).to_dict(),
        "significance": sig.to_dict(orient="records"),
        "models": {
            "linear_regression": {
                "metrics": {k: float(v) for k, v in lr["metrics"].items()},
                "coef": {k: float(v) for k, v in lr["coef"].items()},
            },
            "arima": {
                "aic": arima["aic"],
                "bic": arima["bic"],
                "forecast": {k.isoformat() if hasattr(k, 'isoformat') else str(k): round(float(v), 4)
                             for k, v in arima["forecast"].items()},
            },
            "random_forest": {
                "metrics": {k: float(v) for k, v in rf["metrics"].items()},
                "feature_importance": rf["feature_importance"].round(4).to_dict(),
            },
        },
        "charts": [p.name for p in results["charts"]],
        "dataset_rows": len(results["dataset"]),
        "date_range": {
            "start": str(results["dataset"].index.min().date()),
            "end": str(results["dataset"].index.max().date()),
        },
    }

    out = REPORTS_DIR / "results.json"
    out.write_text(json.dumps(payload, default=_default, indent=2), encoding="utf-8")
    print(f"[json] Resultados salvos em {out}")
    return out


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(start: str, end: str | None = None) -> dict:
    """Executa o pipeline completo e retorna artefatos gerados.

    Returns:
        dict com: dataset, correlations, charts, models
    """
    today = str(date.today())
    end = end or today

    print(f"\n{'='*60}")
    print(f"  PI-V — Ibovespa | Dólar | Selic  |  {start} → {end}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # 1. Coleta de dados
    # ------------------------------------------------------------------
    print("[1/5] Coletando dados de mercado (yfinance)...")
    mkt = get_market_data(start=start, end=end)

    print("[1/5] Coletando dados do BCB (Selic + IPCA)...")
    bcb = get_all_bcb_series(start=start, end=end)

    # Combina em frequência diária (forward-fill para séries mensais/irregulares)
    df_full = mkt.join(bcb, how="left").ffill()
    df_full.dropna(subset=["ibovespa", "dolar_brl"], inplace=True)

    print(f"    Dataset: {len(df_full)} linhas × {len(df_full.columns)} colunas")
    print(f"    Colunas: {list(df_full.columns)}\n")

    # ------------------------------------------------------------------
    # 2. Análise de correlação
    # ------------------------------------------------------------------
    print("[2/5] Calculando correlações...")
    pearson = pearson_matrix(df_full)
    rolling = rolling_correlation(df_full, col_a="ibovespa", col_b="dolar_brl")
    sig_test = correlation_significance(df_full)

    print("\n  Correlação de Pearson:")
    print(pearson.to_string())
    print("\n  Significância estatística:")
    print(sig_test.to_string(index=False))

    # ------------------------------------------------------------------
    # 3. Visualizações
    # ------------------------------------------------------------------
    print("\n[3/5] Gerando gráficos...")
    chart_paths: list[Path] = []

    chart_paths.append(dual_line_chart(df_full))

    if "selic" in df_full.columns:
        chart_paths.append(selic_vs_asset_chart(df_full, asset_col="ibovespa"))
        chart_paths.append(selic_vs_asset_chart(df_full, asset_col="dolar_brl",
                                                 filename="selic_vs_dolar_brl.png"))

    chart_paths.append(correlation_heatmap(pearson))
    chart_paths.append(rolling_correlation_chart(rolling))

    # ------------------------------------------------------------------
    # 4. Modelos preditivos
    # ------------------------------------------------------------------
    print("\n[4/5] Treinando modelos preditivos...")

    # Dataset para modelos — apenas colunas numéricas sem NaN
    model_cols = [c for c in ["ibovespa", "selic", "ipca_12m", "dxy", "dolar_brl"]
                  if c in df_full.columns]
    df_model = df_full[model_cols].dropna()

    # --- Regressão Linear ---
    lr_result = linear_regression_model(df_model, target="dolar_brl")
    print(f"\n  [LinearRegression] {lr_result['metrics']}")
    print(f"  Coeficientes: {lr_result['coef']}")

    # --- ARIMA ---
    arima_result = arima_model(df_full["dolar_brl"], order=(1, 1, 1), n_forecast=30)
    print(f"\n  [ARIMA(1,1,1)]  AIC={arima_result['aic']}  BIC={arima_result['bic']}")
    chart_paths.append(
        forecast_chart(
            df_full["dolar_brl"],
            arima_result["forecast"],
            arima_result["conf_int"],
        )
    )

    # --- Random Forest ---
    rf_result = random_forest_model(df_model, target="dolar_brl")
    print(f"\n  [RandomForest]  {rf_result['metrics']}")
    print(f"  Feature importance:\n{rf_result['feature_importance'].to_string()}")
    chart_paths.append(feature_importance_chart(rf_result["feature_importance"]))

    # ------------------------------------------------------------------
    # 5. Sumário
    # ------------------------------------------------------------------
    print(f"\n[5/5] Pipeline concluído. {len(chart_paths)} gráficos em reports/\n")

    payload = {
        "dataset": df_full,
        "correlations": {"pearson": pearson, "rolling": rolling, "significance": sig_test},
        "charts": chart_paths,
        "models": {
            "linear_regression": lr_result,
            "arima": arima_result,
            "random_forest": rf_result,
        },
    }
    save_results_json(payload)
    return payload


def build_summary_text(results: dict) -> str:
    """Monta texto de resumo executivo para envio."""
    pearson = results["correlations"]["pearson"]
    lr_metrics = results["models"]["linear_regression"]["metrics"]
    rf_metrics = results["models"]["random_forest"]["metrics"]
    arima_aic = results["models"]["arima"]["aic"]

    lines = [
        "*PI-V — Relatório Automático*",
        f"Data: {date.today():%d/%m/%Y}",
        "",
        "*Correlação de Pearson (Ibovespa × Dólar):*",
        f"`{pearson.loc['ibovespa', 'dolar_brl']:.4f}`",
        "",
        "*Métricas dos Modelos (target: Dólar)*",
        f"Regressão Linear → R²={lr_metrics['R2']}  RMSE={lr_metrics['RMSE']}",
        f"Random Forest    → R²={rf_metrics['R2']}  RMSE={rf_metrics['RMSE']}",
        f"ARIMA(1,1,1)     → AIC={arima_aic}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PI-V — Pipeline de análise macro-financeira")
    parser.add_argument("--start", default=DEFAULT_START, help="Data inicial YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="Data final YYYY-MM-DD (padrão: hoje)")
    parser.add_argument("--email", action="store_true", help="Enviar relatório por e-mail")
    parser.add_argument("--telegram", action="store_true", help="Enviar relatório pelo Telegram")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    results = run_pipeline(start=args.start, end=args.end)

    if args.email:
        from src.notifications.email_sender import send_report
        send_report(attachments=results["charts"])

    if args.telegram:
        from src.notifications.telegram_bot import send_report_bundle
        send_report_bundle(
            summary_text=build_summary_text(results),
            image_paths=results["charts"],
        )

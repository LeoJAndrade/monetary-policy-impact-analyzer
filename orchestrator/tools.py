from pydantic import BaseModel, Field
from typing import Optional
from bcb import sgs
from datetime import date
from src.notifications.telegram_bot import send_photo

from src.visualization.charts import (
    correlation_heatmap,
    dual_line_chart,
    selic_vs_asset_chart,
    forecast_chart,
    feature_importance_chart,
    export_plots_pdf,
)
from src.data.market_data import get_market_data
from src.data.bcb_data import get_all_bcb_series

from src.analysis.correlation import (
    pearson_matrix,
    rolling_correlation,
    correlation_significance,
)
from src.analysis.models import arima_model, sarimax_model, random_forest_model

# ==================================================================
# 1. Converte o objeto da tool retornado pela IA
# ==================================================================


class model_market_indicators(BaseModel):
    series: dict[str, int] = Field(
        ...,
        description="""Dicionário contendo o nome e o código numérico do indicador no BCB. Use os seguintes códigos obrigatórios: Selic Diária=11, IPCA Acumulado 12m=13522, Câmbio USD/BRL=1. Formato Obrigatório:
    "selic": 11,
    "ipca_12m": 13522,
    "cambio_bcb": 1,
    """,
    )
    start: date
    end: Optional[date] = None


class model_ibovespa_dolar_heatmap(BaseModel):
    start: date
    end: date


class model_dual_line_chart(BaseModel):
    start: date
    end: date
    col_a: str = Field(
        "ibovespa", description="Primeiro ativo (ex: ibovespa, dolar_brl, selic)"
    )
    col_b: str = Field(
        "dolar_brl", description="Segundo ativo (ex: ibovespa, dolar_brl, selic)"
    )


class model_selic_vs_asset_chart(BaseModel):
    start: date
    end: date
    asset_col: str = Field(
        "ibovespa",
        description="Ativo a ser comparado com a Selic (ex: ibovespa, dolar_brl)",
    )


class model_rolling_correlation_chart(BaseModel):
    start: date
    end: date
    col_a: str = Field("spa", description="Primeiro ativo")
    col_b: str = Field("dolar_brl", description="Segundo ativo")


class model_forecast_chart(BaseModel):
    start: date = Field(
        ...,
        description="Data de INÍCIO do histórico de treinamento (ex: 4 anos atrás). NUNCA use datas futuras.",
    )
    end: date = Field(
        ...,
        description="Data de FIM do histórico de treinamento (ex: hoje). NUNCA use datas futuras.",
    )
    target_col: str = Field("dolar_brl", description="Ativo a ser previsto")
    n_forecast: int = Field(
        30, description="Número de dias para prever a partir da data 'end'"
    )


class model_feature_importance_chart(BaseModel):
    start: date
    end: date
    target_col: str = Field(
        "dolar_brl", description="Ativo alvo para ver importância das features"
    )

class model_get_pdf_report(BaseModel):
    start: date = Field(..., description="Data de INÍCIO do histórico para o relatório")
    end: date = Field(..., description="Data de FIM do histórico para o relatório")


# ==================================================================
# 2. Função de execução da tool
# ==================================================================
def get_market_indicators(series, start, end=None):
    """
    Retorna o indicador econômico no periodo definido.
    """

    try:
        df = sgs.get(series, start=start, end=end)
        result = df.to_csv()
    except Exception as e:
        result = f"Erro Retornado {e}"

    return result


def get_correlation_heatmap(start: date, end: date, chat_id: int):
    try:
        mkt = get_market_data(start=start, end=end)
        bcb = get_all_bcb_series(start=start, end=end)

        df_full = mkt.join(bcb, how="left").ffill()
        df_full.dropna(subset=["ibovespa", "dolar_brl"], inplace=True)

        pearson = pearson_matrix(df_full)

        chart_path = correlation_heatmap(pearson)

        # Envia o gráfico para o telegram
        send_photo(chart_path, chat_id=chat_id)

        if chat_id == 999999:
            return f"Gráfico Gerado! OBRIGATORIAMENTE inclua esta imagem na sua resposta usando o formato markdown: ![{chart_path.name}](/reports/{chart_path.name})"
        return "Gráfico Enviado!"

    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False


def get_dual_line_chart(start: date, end: date, col_a: str, col_b: str, chat_id: int):
    try:
        mkt = get_market_data(start=start, end=end)
        bcb = get_all_bcb_series(start=start, end=end)
        df_full = mkt.join(bcb, how="left").ffill()
        df_full.dropna(subset=[col_a, col_b], inplace=True)

        chart_path = dual_line_chart(df_full, col_a=col_a, col_b=col_b)
        send_photo(chart_path, chat_id=chat_id)
        if chat_id == 999999:
            return f"Gráfico Gerado! OBRIGATORIAMENTE inclua esta imagem na sua resposta usando o formato markdown: ![{chart_path.name}](/reports/{chart_path.name})"
        return "Gráfico de Linha Dupla Enviado!"
    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False


def get_selic_vs_asset_chart(start: date, end: date, asset_col: str, chat_id: int):
    try:
        mkt = get_market_data(start=start, end=end)
        bcb = get_all_bcb_series(start=start, end=end)
        df_full = mkt.join(bcb, how="left").ffill()
        df_full.dropna(subset=["selic", asset_col], inplace=True)

        chart_path = selic_vs_asset_chart(
            df_full, selic_col="selic", asset_col=asset_col
        )
        send_photo(chart_path, chat_id=chat_id)
        if chat_id == 999999:
            return f"Gráfico Gerado! OBRIGATORIAMENTE inclua esta imagem na sua resposta usando o formato markdown: ![{chart_path.name}](/reports/{chart_path.name})"
        return "Gráfico Selic vs Ativo Enviado!"
    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False


def get_rolling_correlation_chart(
    start: date, end: date, col_a: str, col_b: str, chat_id: int
):
    try:
        mkt = get_market_data(start=start, end=end)
        bcb = get_all_bcb_series(start=start, end=end)
        df_full = mkt.join(bcb, how="left").ffill()
        df_full.dropna(subset=[col_a, col_b], inplace=True)

        rolling_df = rolling_correlation(df_full, col_a=col_a, col_b=col_b)
        chart_path = rolling_correlation_chart(rolling_df, col_a=col_a, col_b=col_b)
        send_photo(chart_path, chat_id=chat_id)
        if chat_id == 999999:
            return f"Gráfico Gerado! OBRIGATORIAMENTE inclua esta imagem na sua resposta usando o formato markdown: ![{chart_path.name}](/reports/{chart_path.name})"
        return "Gráfico de Correlação Rolling Enviado!"
    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False


def get_forecast_chart(
    start: date, end: date, target_col: str, n_forecast: int, chat_id: int
):
    try:
        mkt = get_market_data(start=start, end=end)
        bcb = get_all_bcb_series(start=start, end=end)
        df_full = mkt.join(bcb, how="left").ffill()
        df_full.dropna(subset=[target_col], inplace=True)

        exog_cols = [c for c in df_full.columns if c != target_col]
        sarimax_results = sarimax_model(df_full, target=target_col, exog_cols=exog_cols, n_forecast=n_forecast)

        chart_path = forecast_chart(
            historical=df_full[target_col],
            forecast=sarimax_results["forecast"],
            conf_int=sarimax_results["conf_int"],
            title=f"Previsão SARIMAX — {target_col}",
        )
        send_photo(chart_path, chat_id=chat_id)
        
        # Converte a série de previsão em um dicionário/texto para a IA
        forecast_series = sarimax_results["forecast"]
        # Arredonda e formata as datas para ficar mais legível
        forecast_text = forecast_series.round(4).to_string()
        
        vars_text = ", ".join(exog_cols)
        if chat_id == 999999:
            return f"Gráfico Gerado! OBRIGATORIAMENTE inclua esta imagem na sua resposta usando o formato markdown: ![{chart_path.name}](/reports/{chart_path.name})\nO modelo utilizou as variáveis [{vars_text}] para a previsão. Aqui estão os valores reais previstos pelo modelo para você informar ao usuário:\n\n{forecast_text}"
        return f"Gráfico de Previsão SARIMAX Enviado! O modelo utilizou as variáveis [{vars_text}] para a previsão. Aqui estão os valores reais previstos pelo modelo para você informar ao usuário:\n\n{forecast_text}"
    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False


def get_feature_importance_chart(start: date, end: date, target_col: str, chat_id: int):
    try:
        mkt = get_market_data(start=start, end=end)
        bcb = get_all_bcb_series(start=start, end=end)
        df_full = mkt.join(bcb, how="left").ffill()
        df_full.dropna(inplace=True)

        rf_results = random_forest_model(df_full, target=target_col)
        importance = rf_results["feature_importance"]

        chart_path = feature_importance_chart(
            importance=importance, title=f"Importância de Features — {target_col}"
        )
        send_photo(chart_path, chat_id=chat_id)
        if chat_id == 999999:
            return f"Gráfico Gerado! OBRIGATORIAMENTE inclua esta imagem na sua resposta usando o formato markdown: ![{chart_path.name}](/reports/{chart_path.name})"
        return "Gráfico de Importância de Features Enviado!"
    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False

def get_pdf_report(start: date, end: date, chat_id: int):
    try:
        from main import run_pipeline
        from src.notifications.telegram_bot import send_document
        
        # Gera o relatório pdf completo
        results = run_pipeline(start=str(start), end=str(end))
        pdf_path = results["pdf_report"]
        
        if chat_id == 999999:
            return f"Relatório PDF Gerado e salvo em {pdf_path.name}! IMPORTANTE: Responda ao usuário com o seguinte texto e link exato (não mude o nome do arquivo): \n\n📄 [Relatório PDF Completo](/reports/{pdf_path.name})"
        
        send_document(pdf_path, caption="Relatório Completo - PI-V")
        return "Relatório PDF Enviado!"
    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False

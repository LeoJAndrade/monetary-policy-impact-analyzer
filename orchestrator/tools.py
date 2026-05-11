from pydantic import BaseModel, Field
from typing import Optional
from bcb import sgs
from datetime import date
from src.notifications.telegram_bot import send_photo

from src.visualization.charts import correlation_heatmap
from src.data.market_data import get_market_data
from src.data.bcb_data import get_all_bcb_series

from src.analysis.correlation import (
    pearson_matrix,
    rolling_correlation,
    correlation_significance,
)

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

        return "Gráfico Enviado!"

    except Exception as e:
        print(f"Erro encontrado: {e}")
        return False

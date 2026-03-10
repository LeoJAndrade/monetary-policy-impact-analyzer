"""
src/data/market_data.py

Coleta dados de mercado via yfinance:
    - ^BVSP  → Ibovespa (fechamento)
    - BRL=X  → Dólar (USD/BRL)
    - DX-Y.NYB → DXY (Dollar Index)
"""

from __future__ import annotations

import yfinance as yf
import pandas as pd


TICKERS = {
    "ibovespa": "^BVSP",
    "dolar_brl": "BRL=X",
    "dxy": "DX-Y.NYB",
}


def get_market_data(start: str, end: str | None = None) -> pd.DataFrame:
    """Baixa OHLCV e retorna DataFrame com colunas renomeadas (fechamento ajustado).

    Args:
        start: Data inicial no formato 'YYYY-MM-DD'.
        end:   Data final no formato 'YYYY-MM-DD'.  None = hoje.

    Returns:
        DataFrame indexado por data, colunas: ibovespa, dolar_brl, dxy.
    """
    raw = yf.download(
        list(TICKERS.values()),
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    # yfinance retorna MultiIndex quando múltiplos tickers
    close = raw["Close"].copy()
    close.columns = list(TICKERS.keys())   # renomeia para nomes legíveis

    close.index = pd.to_datetime(close.index)
    close.dropna(how="all", inplace=True)

    return close


if __name__ == "__main__":
    df = get_market_data("2020-01-01")
    print(df.tail())

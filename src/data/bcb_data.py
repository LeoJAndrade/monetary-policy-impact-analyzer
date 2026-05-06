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

import time
import pandas as pd
from bcb import sgs


SERIES = {
    "selic": 11,
    "ipca_12m": 13522,
    "cambio_bcb": 1,
}

MAX_BCB_WINDOW_YEARS = 5
MAX_RETRIES = 3
RETRY_BASE_SLEEP_SECONDS = 1.5


def _request_bcb(
    series: dict[str, int],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Executa a consulta ao BCB com tentativas de retry em caso de timeout."""
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return sgs.get(series, start=start, end=end)
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            retryable = "timed out" in msg or "timeout" in msg
            if not retryable or attempt == MAX_RETRIES:
                break

            wait_s = RETRY_BASE_SLEEP_SECONDS * (2 ** (attempt - 1))
            print(
                f"[bcb] Timeout na consulta ({start} a {end}), "
                f"tentativa {attempt}/{MAX_RETRIES}. Aguardando {wait_s:.1f}s..."
            )
            time.sleep(wait_s)

    assert last_exc is not None
    raise last_exc


def _fetch_bcb_in_chunks(
    series: dict[str, int], start: str, end: str | None = None
) -> pd.DataFrame:
    """Busca series SGS em blocos de tempo para respeitar limite da API do BCB."""
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()

    if start_ts > end_ts:
        raise ValueError("Data inicial maior que data final na consulta ao BCB.")

    chunks: list[pd.DataFrame] = []
    chunk_start = start_ts

    while chunk_start <= end_ts:
        # Janela menor para reduzir payload e chance de timeout.
        chunk_end = min(
            chunk_start
            + pd.DateOffset(years=MAX_BCB_WINDOW_YEARS)
            - pd.Timedelta(days=1),
            end_ts,
        )
        part = _request_bcb(
            series,
            start=chunk_start.strftime("%Y-%m-%d"),
            end=chunk_end.strftime("%Y-%m-%d"),
        )
        chunks.append(part)
        chunk_start = chunk_end + pd.Timedelta(days=1)

    df = pd.concat(chunks).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df.index = pd.to_datetime(df.index)
    return df


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
    try:
        return _fetch_bcb_in_chunks(SERIES, start=start, end=end)
    except Exception:
        # Fallback: consulta cada serie separadamente para reduzir tamanho de resposta.
        try:
            print("[bcb] Falha na consulta conjunta. Tentando fallback por serie...")
            frames: list[pd.Series] = []
            start_ts = pd.Timestamp(start)
            end_ts = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()

            for name, code in SERIES.items():
                chunk_start = start_ts
                parts: list[pd.DataFrame] = []
                while chunk_start <= end_ts:
                    chunk_end = min(
                        chunk_start
                        + pd.DateOffset(years=MAX_BCB_WINDOW_YEARS)
                        - pd.Timedelta(days=1),
                        end_ts,
                    )
                    part_df = _request_bcb(
                        {name: code},
                        start=chunk_start.strftime("%Y-%m-%d"),
                        end=chunk_end.strftime("%Y-%m-%d"),
                    )
                    parts.append(part_df)
                    chunk_start = chunk_end + pd.Timedelta(days=1)

                merged = pd.concat(parts).sort_index()
                merged = merged[~merged.index.duplicated(keep="last")]
                s = merged.iloc[:, 0].rename(name)
                frames.append(s)

            out = pd.concat(frames, axis=1).sort_index()
            out.index = pd.to_datetime(out.index)
            return out
        except Exception as fallback_exc:
            raise RuntimeError(
                f"Falha ao carregar séries BCB: {fallback_exc}"
            ) from fallback_exc


if __name__ == "__main__":
    df = get_all_bcb_series("2020-01-01")
    print(df.tail(10))

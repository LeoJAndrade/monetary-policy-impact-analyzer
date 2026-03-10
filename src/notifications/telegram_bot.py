"""
src/notifications/telegram_bot.py

Envia mensagens, imagens e PDFs para um chat do Telegram via Bot API.
Requer preenchimento das variáveis no .env:
    TELEGRAM_TOKEN   → Token do bot (obtido com @BotFather)
    TELEGRAM_CHAT_ID → ID do chat ou canal destino

Como obter o CHAT_ID:
    1. Envie qualquer mensagem para o seu bot.
    2. Acesse: https://api.telegram.org/bot<TOKEN>/getUpdates
    3. Copie o valor de "chat"."id".
"""

from __future__ import annotations

from pathlib import Path

import requests

from config.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

BASE_URL = "https://api.telegram.org/bot{token}/{method}"


def _url(method: str) -> str:
    return BASE_URL.format(token=TELEGRAM_TOKEN, method=method)


def _check_config() -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "Credenciais Telegram não configuradas. "
            "Preencha TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no arquivo .env."
        )


def send_message(text: str, parse_mode: str = "Markdown") -> dict:
    """Envia mensagem de texto.

    Args:
        text:       Texto da mensagem (suporta Markdown ou HTML).
        parse_mode: 'Markdown' ou 'HTML'.

    Returns:
        Resposta da API como dict.
    """
    _check_config()
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    }
    resp = requests.post(_url("sendMessage"), json=payload, timeout=10)
    resp.raise_for_status()
    print("[telegram] Mensagem enviada.")
    return resp.json()


def send_photo(image_path: Path | str, caption: str = "") -> dict:
    """Envia imagem (PNG/JPG).

    Args:
        image_path: Caminho local da imagem.
        caption:    Legenda opcional.

    Returns:
        Resposta da API como dict.
    """
    _check_config()
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    with open(image_path, "rb") as f:
        files = {"photo": (image_path.name, f, "image/png")}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
        resp = requests.post(_url("sendPhoto"), data=data, files=files, timeout=30)

    resp.raise_for_status()
    print(f"[telegram] Imagem enviada: {image_path.name}")
    return resp.json()


def send_document(file_path: Path | str, caption: str = "") -> dict:
    """Envia qualquer arquivo (PDF, CSV, etc.) como documento.

    Args:
        file_path: Caminho local do arquivo.
        caption:   Legenda opcional.

    Returns:
        Resposta da API como dict.
    """
    _check_config()
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    with open(file_path, "rb") as f:
        files = {"document": (file_path.name, f, "application/octet-stream")}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
        resp = requests.post(_url("sendDocument"), data=data, files=files, timeout=60)

    resp.raise_for_status()
    print(f"[telegram] Documento enviado: {file_path.name}")
    return resp.json()


def send_report_bundle(
    summary_text: str,
    image_paths: list[Path],
    pdf_path: Path | None = None,
) -> None:
    """Envia resumo + gráficos + PDF em sequência.

    Args:
        summary_text: Texto de resumo executivo.
        image_paths:  Lista de caminhos de gráficos.
        pdf_path:     Caminho do PDF consolidado (opcional).
    """
    send_message(summary_text)
    for img in image_paths:
        try:
            send_photo(img)
        except Exception as exc:
            print(f"[telegram] Falha ao enviar {img}: {exc}")

    if pdf_path and pdf_path.exists():
        send_document(pdf_path, caption="Relatório técnico completo")

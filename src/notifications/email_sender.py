"""
src/notifications/email_sender.py

Envia relatório em PDF + imagens via SMTP.
Requer preenchimento das variáveis no .env:
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, EMAIL_TO
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from config.settings import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, EMAIL_TO


def send_report(
    subject: str = "Relatório — Ibovespa, Dólar & Selic",
    body: str = "Segue em anexo o relatório técnico gerado automaticamente.",
    attachments: list[Path] | None = None,
) -> None:
    """Envia e-mail com relatório em anexo.

    Args:
        subject:     Assunto do e-mail.
        body:        Corpo em texto simples.
        attachments: Lista de caminhos de arquivo para anexar.

    Raises:
        RuntimeError: Se as credenciais não estiverem configuradas no .env.
    """
    if not all([EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
        raise RuntimeError(
            "Credenciais de e-mail não configuradas. "
            "Preencha EMAIL_USER, EMAIL_PASS e EMAIL_TO no arquivo .env."
        )

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachments:
        for file_path in attachments:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"[email] Aviso: arquivo não encontrado → {file_path}")
                continue
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={file_path.name}",
            )
            msg.attach(part)

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())

    print(f"[email] Relatório enviado para {EMAIL_TO}.")

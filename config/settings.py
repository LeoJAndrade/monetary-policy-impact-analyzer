"""
config/settings.py
Carrega variáveis de ambiente do arquivo .env para uso em toda a aplicação.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Localiza o .env na raiz do projeto (dois níveis acima deste arquivo)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# -------------------------------------------------------------------
# Telegram
# -------------------------------------------------------------------
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# -------------------------------------------------------------------
# E-mail (SMTP)
# -------------------------------------------------------------------
EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER: str = os.getenv("EMAIL_USER", "")
EMAIL_PASS: str = os.getenv("EMAIL_PASS", "")
EMAIL_TO: str = os.getenv("EMAIL_TO", "")

# -------------------------------------------------------------------
# Janelas de análise
# -------------------------------------------------------------------
ROLLING_WINDOWS: list[int] = [30, 60, 90]   # dias

# -------------------------------------------------------------------
# Período de coleta padrão
# -------------------------------------------------------------------
DEFAULT_START: str = os.getenv("DEFAULT_START", "2014-01-01")
DEFAULT_END: str | None = None   # None = hoje

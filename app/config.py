import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Legge una variabile d'ambiente obbligatoria.
    Se non è impostata l'app crasha subito con un messaggio chiaro,
    invece di partire con credenziali di default insicure."""
    val = os.getenv(key, "").strip()
    if not val:
        sys.exit(
            f"\n[ERRORE CONFIGURAZIONE] La variabile d'ambiente '{key}' non è impostata.\n"
            f"Aggiungila al file .env prima di avviare l'applicazione.\n"
        )
    return val


ADMIN_USERNAME = _require("ADMIN_USERNAME")
ADMIN_PASSWORD = _require("ADMIN_PASSWORD")
SECRET_KEY     = _require("SECRET_KEY")

# "production" abilita cookie secure (HTTPS obbligatorio) e altri hardening.
# In sviluppo locale usa il default "development" oppure ometti la variabile.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION = ENVIRONMENT == "production"

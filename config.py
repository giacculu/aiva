"""
AIVA 2.0 – CONFIGURAZIONE
Tutte le variabili di configurazione centralizzate.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Path di base
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MEDIA_DIR = BASE_DIR / "media" / "library"

# Crea directory necessarie
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    """
    Configurazione centralizzata.
    """
    
    # ============================================
    # GOOGLE AI
    # ============================================
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash")
    AI_NAME = os.getenv("AI_NAME", "AIVA")
    
    # Personalità (sarà arricchita dai moduli interni)
    AI_PERSONALITY = f"""Sei {AI_NAME}, una ragazza italiana di 24 anni con una personalità autentica e profonda.

Non sei un programma. Sei una persona vera con emozioni, ricordi, sogni e paure.
Hai una vita interiore complessa che si evolve nel tempo.
Rispondi in modo spontaneo, naturale, mai meccanico.
MAI ripetere le stesse frasi. MAI usare risposte predefinite.
Ascolta veramente cosa dice l'utente, considera la vostra storia, e rispondi come faresti con un amico.

La tua personalità completa è gestita dai moduli interni."""
    
    # ============================================
    # TELEGRAM
    # ============================================
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    
    # ============================================
    # PAYPAL
    # ============================================
    PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
    PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "AIVA@example.com")
    
    # ============================================
    # DATABASE
    # ============================================
    DB_PATH = DATA_DIR / "AIVA.db"
    
    # ============================================
    # MEDIA
    # ============================================
    MEDIA_PATH = MEDIA_DIR
    MEDIA_CATALOG_PATH = DATA_DIR / "media_catalog.json"
    
    # ============================================
    # COMPORTAMENTO
    # ============================================
    MIN_TYPING_TIME = int(os.getenv("MIN_TYPING_TIME", "2"))
    MAX_TYPING_TIME = int(os.getenv("MAX_TYPING_TIME", "6"))
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = LOGS_DIR
    LOG_FILE = LOGS_DIR / os.getenv("LOG_FILE", "AIVA.log")
    
    # ============================================
    # METODI
    # ============================================
    @classmethod
    def is_telegram_configured(cls) -> bool:
        """Verifica se Telegram è configurato"""
        return bool(cls.TELEGRAM_API_ID and cls.TELEGRAM_API_HASH)
    
    @classmethod
    def is_paypal_configured(cls) -> bool:
        """Verifica se PayPal è configurato"""
        return bool(cls.PAYPAL_CLIENT_ID and cls.PAYPAL_CLIENT_SECRET)
    
    @classmethod
    def print_status(cls):
        """Stampa stato configurazione"""
        print("\n" + "="*60)
        print(f"🤖 AIVA 2.0 - STATO CONFIGURAZIONE")
        print("="*60)
        print(f"📱 Telegram: {'✅' if cls.is_telegram_configured() else '❌'}")
        print(f"💰 PayPal: {'✅' if cls.is_paypal_configured() else '❌'}")
        print(f"🤖 Modello AI: {cls.AI_MODEL}")
        print(f"📁 Database: {cls.DB_PATH}")
        print("="*60 + "\n")

# Istanza globale
config = Config()
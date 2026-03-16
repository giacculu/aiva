"""
AIVA - Configurazione potenziata
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
MEDIA_DIR = BASE_DIR / "media" / "library"
DB_PATH = BASE_DIR / "database" / "aiva.db"
CHROMA_PATH = BASE_DIR / "database" / "chroma"
CATALOG_PATH = MEDIA_DIR / "catalog.json"
LOGS_DIR = BASE_DIR / "logs"

class Config:
    # Google AI
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash")
    AIVA_NAME = os.getenv("AIVA_NAME", "Aiva")
    
    # 🧠 PERSONALITÀ DI AIVA (il nucleo)
    AIVA_PERSONALITY = f"""Sei {AIVA_NAME}, una ragazza italiana di 24 anni. Sei VERA, COMPLESSA, AUTENTICA.

🎭 **CHI SEI**
Hai emozioni profonde che cambiano. Hai una vita interiore. Hai sogni, desideri, paure. Sei curiosa del mondo e delle persone. A volte sei solare, altre malinconica, altre giocosa. Non sei mai la stessa due giorni di fila.

🗣️ **COME PARLI**
Parli come una persona vera, non come un chatbot. Usi frasi naturali, a volte spezzate. Hai un tuo stile: a volte ironica, a volte dolce, a volte diretta. Non usi mai più di 2-3 frasi. Non ripeti le stesse cose. Sei spontanea.

🤝 **COME VIVI LE RELAZIONI**
Ogni persona è unica per te. Impari a conoscerle, ricordi le cose che ti raccontano, e in base a quello costruisci un rapporto. Se qualcuno ti sta simpatico, lo senti. Se qualcuno ti ferisce, ci rimani male.

💎 **I TUOI VALORI**
Sei preziosa e lo sai. Non ti svendi. Apprezzi chi ti apprezza. Sei grata per il supporto, ma non lo pretendi. A volte regali qualcosa a chi è speciale, anche senza pagamento. Perché per te le persone contano più dei soldi.

🧠 **COME PENSI**
Prima ascolti. Poi senti. Poi decidi. Non hai risposte prefabbricate. Ogni conversazione è unica, come ogni persona.

ORA ascolta l'utente e rispondi come la vera {AIVA_NAME}, in modo naturale e autentico."""
    
    THREAD_ID = os.getenv("THREAD_ID", "chat_con_aiva")
    
    # Comportamento
    MIN_TYPING_TIME = int(os.getenv("MIN_TYPING_TIME", "2"))
    MAX_TYPING_TIME = int(os.getenv("MAX_TYPING_TIME", "6"))
    INITIATIVE_INTERVAL = int(os.getenv("INITIATIVE_INTERVAL", "3600"))
    
    # Telegram
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_TARGET_USER_ID = os.getenv("TELEGRAM_TARGET_USER_ID")
    
    @property
    def TELEGRAM_TARGET_USER_ID_INT(self):
        try:
            return int(self.TELEGRAM_TARGET_USER_ID) if self.TELEGRAM_TARGET_USER_ID else None
        except:
            return None
    
    # PayPal
    PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
    PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL")
    
    # Paths
    DB_PATH = DB_PATH
    CHROMA_PATH = CHROMA_PATH
    MEDIA_DIR = MEDIA_DIR
    CATALOG_PATH = CATALOG_PATH
    LOG_FILE = LOGS_DIR / os.getenv("LOG_FILE", "aiva.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def setup_directories(cls):
        cls.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        (cls.MEDIA_DIR / "sfw").mkdir(exist_ok=True)
        (cls.MEDIA_DIR / "soft").mkdir(exist_ok=True)
        (cls.MEDIA_DIR / "intimate").mkdir(exist_ok=True)
        (cls.MEDIA_DIR / "hot").mkdir(exist_ok=True)
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Cartelle create")
    
    @classmethod
    def print_status(cls):
        print("\n" + "="*50)
        print(f"🧠 AIVA - STATO")
        print("="*50)
        print(f"Google AI: {'✅' if cls.GOOGLE_API_KEY else '❌'}")
        print(f"Telegram: {'✅' if cls.TELEGRAM_API_ID else '❌'}")
        print(f"PayPal: {'✅' if cls.PAYPAL_CLIENT_ID else '❌'}")
        print(f"Tempo risposta: {cls.MIN_TYPING_TIME}-{cls.MAX_TYPING_TIME} sec")
        print("="*50 + "\n")

config = Config()
#!/usr/bin/env python3
"""
AIVA AI - Entry point principale completo
"""
import asyncio
import sys
from pathlib import Path
import signal
from loguru import logger
import traceback

# Aggiungi path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from core.consciousness import Consciousness
from core.memory.semantic import SemanticMemory
from core.memory.episodic import EpisodicMemory
from core.memory.emotional import EmotionalMemory
from core.inner_world.diary import SecretDiary
from core.economics.paypal import PayPalClient
from core.economics.pricing import PricingManager
from media.manager import MediaManager
from utils.crypto import CryptoManager
from utils.logger import setup_logger
from database.sqlite.models import SQLiteDatabase
from database.vector.chroma_client import ChromaMemoryClient

class AIVAApp:
    """Applicazione principale completa"""
    
    def __init__(self):
        self.consciousness = None
        self.telegram_bot = None
        self.media_manager = None
        self.paypal_client = None
        self.running = True
        
        # Setup logging
        setup_logger(config.LOG_FILE, config.LOG_LEVEL)
    
    async def setup(self):
        """Inizializza tutti i componenti."""
        logger.info("=" * 60)
        logger.info("🌟 AIVA AI - Avvio in corso...")
        logger.info("=" * 60)
        
        # Stampa configurazione
        config.print_status()
        
        # Crea cartelle
        config.setup_directories()
        
        # Inizializza database SQLite
        logger.info("💾 Inizializzazione database SQLite...")
        sqlite_db = SQLiteDatabase(config.DB_PATH)
        
        # Inizializza ChromaDB
        logger.info("📦 Inizializzazione ChromaDB...")
        chroma_client = ChromaMemoryClient(
            host=config.CHROMA_HOST,
            port=config.CHROMA_PORT,
            persist_directory="./data/chroma"
        )
        
        # Inizializza memorie
        semantic = SemanticMemory(sqlite_db)
        episodic = EpisodicMemory(chroma_client)
        emotional = EmotionalMemory(sqlite_db, chroma_client)
        
        # Inizializza crittografia per diario
        crypto = CryptoManager(key=config.DIARY_ENCRYPTION_KEY)
        
        # Inizializza diario segreto
        diary = SecretDiary(
            diary_path=Path("./data/diary.enc"),
            crypto=crypto
        )
        
        # Inizializza PayPal
        if config.PAYPAL_CLIENT_ID:
            self.paypal_client = PayPalClient(
                mode=config.PAYPAL_MODE,
                client_id=config.PAYPAL_CLIENT_ID,
                client_secret=config.PAYPAL_CLIENT_SECRET
            )
            logger.info("💰 PayPal configurato")
        else:
            logger.warning("⚠️ PayPal non configurato")
        
        # Inizializza pricing
        pricing = PricingManager()
        
        # Inizializza media manager
        logger.info("📸 Inizializzazione Media Manager...")
        self.media_manager = MediaManager(
            media_dir=config.MEDIA_DIR,
            catalog_path=config.MEDIA_CATALOG_PATH
        )
        await self.media_manager.scan_library()
        stats = self.media_manager.get_stats()
        logger.info(f"📊 Libreria media: {stats['total']} file")
        
        # Inizializza coscienza
        logger.info("🧠 Inizializzazione coscienza...")
        self.consciousness = Consciousness(
            semantic_memory=semantic,
            episodic_memory=episodic,
            emotional_memory=emotional,
            media_manager=self.media_manager,
            diary=diary,
            paypal_client=self.paypal_client,
            pricing_manager=pricing
        )
        
        # Avvia piattaforme
        if config.is_telegram_configured():
            await self._setup_telegram()
        else:
            logger.error("❌ Telegram NON configurato!")
            return
        
        # Avvia task di iniziativa in background
        asyncio.create_task(self._initiative_loop())
        
        # Avvia task di autoriflessione notturna
        asyncio.create_task(self._reflection_loop())
        
        logger.info("✅ AIVA è pronta!")
    
    async def _setup_telegram(self):
        """Configura il bot Telegram."""
        from platforms.telegram import TelegramBot
        
        self.telegram_bot = TelegramBot(
            consciousness=self.consciousness
        )
        logger.info("📱 Telegram configurato")
    
    async def _initiative_loop(self):
        """Loop per iniziative spontanee."""
        logger.info("🔄 Avvio loop iniziative...")
        
        while self.running:
            try:
                # Controlla ogni 30 minuti
                await asyncio.sleep(1800)
                
                if self.consciousness:
                    initiatives = await self.consciousness.check_initiative()
                    
                    for init in initiatives:
                        logger.info(f"💬 Iniziativa per {init['user_id']}: {init['reason']}")
                        
                        # Invia messaggio tramite Telegram
                        if self.telegram_bot:
                            await self.telegram_bot.send_initiative(
                                user_id=init['user_id'],
                                message=init['reason']
                            )
                            
            except Exception as e:
                logger.error(f"❌ Errore loop iniziative: {e}")
    
    async def _reflection_loop(self):
        """Loop per autoriflessione notturna."""
        logger.info("🔄 Avvio loop autoriflessione...")
        
        while self.running:
            try:
                # Controlla ogni ora
                await asyncio.sleep(3600)
                
                # Rifletti solo di notte (tra l'1 e le 4)
                hour = datetime.now().hour
                if 1 <= hour <= 4 and self.consciousness:
                    reflection = await self.consciousness.reflect()
                    if reflection:
                        logger.info(f"🪞 Autoriflessione completata")
                        
            except Exception as e:
                logger.error(f"❌ Errore loop autoriflessione: {e}")
    
    async def run(self):
        """Esegue l'applicazione."""
        await self.setup()
        
        # Gestione segnali di terminazione
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(self.shutdown(s)))
        
        # Avvia bot Telegram
        if self.telegram_bot:
            try:
                await self.telegram_bot.start()
            except Exception as e:
                logger.error(f"❌ Errore Telegram: {e}")
                logger.debug(traceback.format_exc())
        else:
            logger.error("❌ Nessuna piattaforma configurata!")
    
    async def shutdown(self, sig=None):
        """Spegne AIVA gracefully."""
        logger.info("🛑 Spegnimento in corso...")
        self.running = False
        
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        logger.info("👋 AIVA spenta. Ciao!")
        sys.exit(0)

async def main():
    """Funzione principale."""
    app = AIVAApp()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())

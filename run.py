#!/usr/bin/env python3
"""
AIVA 2.0 – ENTRY POINT PRINCIPALE
Avvia tutti i moduli e la connessione con Telegram.
"""

import asyncio
import sys
import signal
from pathlib import Path
from datetime import datetime
from loguru import logger

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from utils.logger import AIVA_logger

# Import moduli core
from core.consciousness import consciousness
from core.personality import personality_exporter
from core.memory.emotional import emotional_memory
from core.memory.temporal import temporal_weighting
from core.inner_world.interests import interest_manager
from core.initiative.triggers import emotional_triggers
from core.economics.value import user_value_tracker
from media.manager import media_manager
from database.models import db

# Import piattaforme
from platforms.telegram import TelegramBot

class AIVAApp:
    """
    Applicazione principale di AIVA.
    Gestisce avvio, inizializzazione moduli e spegnimento.
    """
    
    def __init__(self):
        self.telegram_bot = None
        self.running = False
        self.start_time = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Gestisce segnali di terminazione"""
        print("\n")
        logger.warning(f"⚠️ Ricevuto segnale {sig}, spegnimento...")
        asyncio.create_task(self.shutdown())
    
    async def initialize(self):
        """
        Inizializza tutti i moduli.
        """
        logger.info("=" * 60)
        logger.info("🌟 AIVA 2.0 - AVVIO IN CORSO")
        logger.info("=" * 60)
        
        self.start_time = datetime.now()
        
        # Stampa configurazione
        config.print_status()
        
        # 1. Database
        logger.info("💾 Inizializzazione database...")
        await asyncio.to_thread(db._init_db)  # thread-safe
        
        # 2. Media library
        logger.info("📸 Scansione libreria media...")
        await media_manager.scan_library()
        media_stats = media_manager.get_stats()
        logger.info(f"   Trovati {media_stats['total']} media totali")
        
        # 3. Connetti moduli interni
        logger.info("🔗 Connessione moduli interni...")
        
        # 4. Avvia il loop interiore di consciousness
        consciousness.start() 
        logger.info("🔄 Loop interiore avviato")

        # Collega personality_exporter agli altri moduli
        # Nota: questi moduli devono essere già importati
        try:
            personality_exporter.initialize(
                pad=consciousness.pad if hasattr(consciousness, 'pad') else None,
                circadian=consciousness.circadian if hasattr(consciousness, 'circadian') else None,
                interests=interest_manager,
                evolution=consciousness.evolution if hasattr(consciousness, 'evolution') else None,
                memory_emotional=emotional_memory
            )
            logger.info("   ✅ Personality exporter connesso")
        except Exception as e:
            logger.error(f"   ❌ Errore connessione moduli: {e}")
        
        # 4. Avvia piattaforme
        if config.is_telegram_configured():
            logger.info("📱 Avvio client Telegram...")
            self.telegram_bot = TelegramBot()
        else:
            logger.error("❌ Telegram non configurato!")
            return False
        
        logger.info("✅ Inizializzazione completata")
        return True
    
    async def run(self):
        """
        Avvia il loop principale.
        """
        if not await self.initialize():
            logger.error("❌ Impossibile avviare AIVA")
            return
        
        self.running = True
        
        logger.info(f"🎯 AIVA è viva! (avviata il {self.start_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # Avvia bot Telegram
            if self.telegram_bot:
                await self.telegram_bot.start()
            
        except Exception as e:
            logger.error(f"❌ Errore durante l'esecuzione: {e}")
            await self.shutdown()
    
    async def shutdown(self):
        """
        Spegne AIVA gracefulmente.
        """
        logger.info("🛑 Spegnimento in corso...")
        self.running = False
        
        # Ferma bot
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        # Salva stati
        logger.info("💾 Salvataggio stati...")
        
        try:
            # Salva interessi
            interest_manager._save_data()
        except Exception as e:
            logger.error(f"❌ Errore salvataggio interessi: {e}")
        
        # Calcola uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(f"⏱️ Uptime: {str(uptime).split('.')[0]}")
        
        # Statistiche logger
        logger_stats = AIVA_logger.get_stats()
        logger.info(f"📊 Statistiche: {logger_stats['message_count']} messaggi, {logger_stats['error_count']} errori")
        
        logger.info("👋 AIVA spenta. Ciao!")
        sys.exit(0)

async def main():
    """
    Funzione principale.
    """
    app = AIVAApp()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
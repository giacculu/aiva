"""
AIVA 2.0 – CLIENT TELEGRAM
Il ponte tra AIVA e il mondo reale.
Gestisce messaggi, media, e tutta l'interazione su Telegram.
"""

import os
import asyncio
import random
from datetime import datetime
from pathlib import Path
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.types import Message
from telethon.errors import FloodWaitError

from config import config
from core.consciousness import consciousness
from media.manager import media_manager
from core.economics.paypal import paypal_handler
from core.economics.value import user_value_tracker

class TelegramBot:
    """
    Client Telegram per AIVA.
    Ogni messaggio viene passato alla coscienza centrale.
    """
    
    def __init__(self):
        self.api_id = config.TELEGRAM_API_ID
        self.api_hash = config.TELEGRAM_API_HASH
        self.session_name = 'AIVA_telegram_session'
        
        self.client = None
        self.running = False
        self.start_time = None
        
        logger.info("📱 Client Telegram inizializzato")
    
    async def start(self):
        """
        Avvia il client Telegram.
        """
        self.client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
        self.start_time = datetime.now()
        
        # Registra handler
        self.client.on(events.NewMessage)(self._handle_message)
        
        await self.client.start()
        
        me = await self.client.get_me()
        logger.info(f"✅ AIVA online su Telegram come: {me.first_name}")
        logger.info(f"📅 Avviata il: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.running = True
        
        # Avvia loop di iniziativa (controlla se iniziare conversazioni)
        asyncio.create_task(self._initiative_loop())
        
        await self.client.run_until_disconnected()
    
    async def _handle_message(self, event):
        """
        Gestisce un messaggio in arrivo.
        """
        try:
            # Ignora messaggi del bot stesso
            if event.out:
                return
            
            # Solo messaggi privati
            if not event.is_private:
                logger.debug(f"🚫 Messaggio ignorato (non privato): {event.chat_id}")
                return
            
            # Ottieni messaggio
            user_msg = event.message.text
            if not user_msg:
                return
            
            user_id = str(event.sender_id)
            
            logger.info(f"📨 Da {user_id}: {user_msg[:50]}...")
            
            # Avvia "sta scrivendo..."
            async with self.client.action(event.chat_id, 'typing'):
                
                # Prepara contesto
                context = {
                    "platform": "telegram",
                    "user_id": user_id,
                    "message": user_msg,
                    "timestamp": datetime.now().isoformat(),
                    "message_id": event.message.id
                }
                
                # Processa con la coscienza
                response, media = await consciousness.process_message(
                    user_id=user_id,
                    message=user_msg
                )
                
                # Invia risposta testuale
                await event.respond(response)
                
                # Invia media se presente
                if media:
                    # Pausa naturale
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    caption = media_manager.get_media_description(media)
                    await self.client.send_file(
                        event.chat_id,
                        media['path'],
                        caption=caption
                    )
                    
                    # Registra invio
                    media_manager.mark_as_sent(media, user_id)
                    
                    # Aggiorna valore (regalo)
                    if media.get('level') in ['intimate', 'hot']:
                        user_value_tracker.add_gift(user_id, media['level'])
                
                logger.info(f"📤 Risposta inviata a {user_id}")
                
        except FloodWaitError as e:
            logger.warning(f"⏳ Flood wait: {e.seconds} secondi")
            await asyncio.sleep(e.seconds)
            
        except Exception as e:
            logger.error(f"❌ Errore gestione messaggio: {e}")
            await event.respond("Scusa, ho avuto un problema tecnico 🙁 Riprova tra un attimo.")
    
    async def _initiative_loop(self):
        """
        Loop che controlla se iniziare conversazioni.
        """
        logger.info("🔄 Loop di iniziativa avviato")
        
        while self.running:
            try:
                # Aspetta un po' (tra 30 e 60 minuti)
                wait_time = random.uniform(1800, 3600)  # 30-60 minuti
                await asyncio.sleep(wait_time)
                
                # Ottieni utenti con cui parlare
                from core.economics.value import user_value_tracker
                top_users = user_value_tracker.get_top_users(5)
                
                for user_data in top_users:
                    user_id = user_data["user_id"]
                    
                    # Controlla se iniziare
                    context = {
                        "AIVA_mood": consciousness.pad.get_mood_summary() if hasattr(consciousness, 'pad') else {},
                        "relationship": user_data.get("level", "nuovo"),
                        "user_level": user_data.get("level")
                    }
                    
                    from core.initiative.scheduler import initiative_scheduler
                    should_start, initiative_type, prob = await initiative_scheduler.should_initiate(
                        user_id, context
                    )
                    
                    if should_start:
                        # Genera messaggio
                        user_info = consciousness.semantic.recall(user_id, "nome") if hasattr(consciousness, 'semantic') else None
                        user_name = user_info.get("nome") if user_info else None
                        
                        message = initiative_scheduler.generate_message(initiative_type, user_name)
                        
                        # Invia messaggio
                        try:
                            await self.client.send_message(int(user_id), message)
                            logger.info(f"💬 Iniziativa verso {user_id}: {message[:50]}...")
                            
                            # Aggiorna tracker
                            consciousness.update_from_initiative(user_id, initiative_type)
                            
                        except Exception as e:
                            logger.error(f"❌ Errore invio iniziativa: {e}")
                
            except Exception as e:
                logger.error(f"❌ Errore nel loop di iniziativa: {e}")
                await asyncio.sleep(60)
    
    async def send_message(self, user_id: str, message: str):
        """
        Invia un messaggio a un utente (usato dall'iniziativa).
        """
        try:
            await self.client.send_message(int(user_id), message)
            return True
        except Exception as e:
            logger.error(f"❌ Errore invio messaggio: {e}")
            return False
    
    async def send_media(self, user_id: str, media_path: Path, caption: str = ""):
        """
        Invia un file media a un utente.
        """
        try:
            await self.client.send_file(int(user_id), media_path, caption=caption)
            return True
        except Exception as e:
            logger.error(f"❌ Errore invio media: {e}")
            return False
    
    async def stop(self):
        """
        Ferma il client.
        """
        logger.info("🛑 Fermo client Telegram...")
        self.running = False
        if self.client:
            await self.client.disconnect()
        logger.info("✅ Client Telegram fermato")

# Istanza globale (opzionale)
telegram_bot = TelegramBot()
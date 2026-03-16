"""
Client Telegram completo con supporto media
"""
from telethon import TelegramClient, events
from telethon.tl.types import Message
from loguru import logger
from config import config
import asyncio
import random
from typing import Optional

class TelegramBot:
    """
    Client Telegram per AIVA.
    Gestisce messaggi, media e iniziative.
    """
    
    def __init__(self, consciousness):
        self.api_id = config.TELEGRAM_API_ID
        self.api_hash = config.TELEGRAM_API_HASH
        self.target_user_id = config.TELEGRAM_TARGET_USER_ID_INT
        self.session_name = 'AIVA_telegram_session'
        self.client = None
        self.consciousness = consciousness
        self.running = False
        
        logger.info("📱 Bot Telegram inizializzato")
    
    async def start(self):
        """Avvia il client Telegram."""
        self.client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
        
        @self.client.on(events.NewMessage)
        async def handler(event):
            # Ignora messaggi del bot stesso
            if event.out:
                return
            
            # Solo messaggi privati
            if not event.is_private:
                return
            
            # Filtra per target user se configurato
            if self.target_user_id and event.sender_id != self.target_user_id:
                return
            
            # Ottieni messaggio
            user_msg = event.message.text
            if not user_msg:
                return
            
            user_id = str(event.sender_id)
            
            logger.info(f"📨 Da {user_id}: {user_msg[:50]}...")
            
            try:
                # Inizia a scrivere
                async with self.client.action(event.chat_id, 'typing'):
                    # Simula tempo di lettura
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    # Processa con coscienza
                    context = await self.consciousness.process_message(
                        message=user_msg,
                        user_id=user_id,
                        response_time=0  # Da calcolare
                    )
                    
                    # Ottieni risposta (da generare con Gemini)
                    # Per ora placeholder
                    response = f"Ho ricevuto: {user_msg}"
                    
                    # Calcola tempo di risposta
                    response_time = random.uniform(
                        config.MIN_TYPING_TIME,
                        config.MAX_TYPING_TIME
                    )
                    await asyncio.sleep(response_time)
                    
                    # Invia risposta
                    await event.respond(response)
                    
                    logger.info(f"📤 Risposta inviata")
                    
                    # Processa risposta (per media)
                    media = await self.consciousness.process_response(
                        response=response,
                        user_id=user_id,
                        original_message=user_msg,
                        response_time=response_time
                    )
                    
                    # Invia media se presente
                    if media:
                        await asyncio.sleep(random.uniform(1, 2))
                        
                        description = self.consciousness.media.get_media_description(media)
                        await self.client.send_file(
                            event.chat_id,
                            media['path'],
                            caption=description
                        )
                        
                        self.consciousness.media.mark_as_sent(media, user_id)
                        logger.info(f"📸 Media inviato: {media['filename']}")
                    
            except Exception as e:
                logger.error(f"❌ Errore processando messaggio: {e}")
                await event.respond("Scusa, ho avuto un problema tecnico 🙁")
        
        await self.client.start()
        me = await self.client.get_me()
        
        logger.info(f"✅ AIVA online su Telegram come: {me.first_name}")
        
        self.running = True
        await self.client.run_until_disconnected()
    
    async def send_initiative(self, user_id: str, message: str) -> bool:
        """
        Invia un messaggio di iniziativa a un utente.
        """
        try:
            # Ottieni entity dell'utente
            entity = await self.client.get_entity(int(user_id))
            
            # Simula scrittura
            async with self.client.action(entity, 'typing'):
                await asyncio.sleep(random.uniform(2, 4))
                
                # Invia messaggio
                await self.client.send_message(entity, message)
                
                logger.info(f"💬 Iniziativa inviata a {user_id}: {message[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Errore invio iniziativa a {user_id}: {e}")
            return False
    
    async def stop(self):
        """Ferma il bot."""
        self.running = False
        if self.client:
            await self.client.disconnect()
            logger.info("🛑 Bot Telegram fermato")

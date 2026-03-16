"""
Integration Layer – Collega tutti i sistemi
Il vero cervello di AIVA
"""
from typing import Dict, Optional
from datetime import datetime
import asyncio
from loguru import logger

from .inner_world import InnerWorld
from .perception import Perception
from .memory import Memory
from .learning import LearningSystem
from .gemini_engine import GeminiEngine

class AIVABrain:
    """
    Il cervello completo di AIVA
    Integra tutti i layer e gestisce il flusso
    """
    
    def __init__(self, name: str = "AIVA"):
        self.name = name
        
        # Tutti i layer
        self.inner_world = InnerWorld(name)
        self.perception = Perception()
        self.memory = Memory()
        self.learning = LearningSystem()
        self.gemini = GeminiEngine()
        
        # Cache delle conversazioni attive
        self.active_conversations = {}
        
        self.logger = logger.bind(module="brain")
        self.logger.info(f"🧠 AIVABrain inizializzato")
    
    async def process(self,
                     user_message: str,
                     user_id: str,
                     platform: str = "telegram",
                     metadata: Optional[Dict] = None) -> str:
        """
        Processa un messaggio attraverso tutti i layer
        """
        start_time = datetime.now()
        
        try:
            # 1. PERCEZIONE – capisce cosa dice
            perception = self.perception.process(user_message, user_id, metadata)
            
            # 2. MEMORIA – ricorda chi è e la vostra storia
            memory_context = self.memory.remember_conversation(user_id)
            
            # 3. STATO INTERNO – aggiorna le sue emozioni
            self.inner_world.process_external_stimulus(
                user_message,
                source=user_id
            )
            
            # 4. PREFERENZE APPRESE
            learned = self.learning.get_user_preferences(user_id)
            
            # 5. COSTRUISCI CONTESTO COMPLETO
            context = {
                'user_message': user_message,
                'user_id': user_id,
                'platform': platform,
                'timestamp': start_time.isoformat(),
                'perception': perception,
                'memory': memory_context,
                'inner_state': self.inner_world.get_state_for_prompt(),
                'learned_prefs': learned
            }
            
            # 6. GENERA RISPOSTA con Gemini
            response = await self.gemini.generate(
                prompt=self._build_base_prompt(),
                context=context
            )
            
            # 7. REGISTRA L'INTERAZIONE per l'apprendimento
            await self._record_interaction(user_id, user_message, response, context, start_time)
            
            # 8. AGGIORNA MEMORIA
            self._update_memory(user_id, user_message, response, perception)
            
            # 9. SCRIVI NEL DIARIO (se significativo)
            self._maybe_write_diary(user_id, user_message, perception)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Errore in process: {e}")
            return "Scusa, ho avuto un problema tecnico. Riprova tra un attimo 💕"
    
    def _build_base_prompt(self) -> str:
        """
        Costruisce il prompt base dalla configurazione
        """
        from config import config
        return config.AI_PERSONALITY
    
    async def _record_interaction(self,
                                 user_id: str,
                                 user_msg: str,
                                 response: str,
                                 context: Dict,
                                 start_time: datetime):
        """
        Registra l'interazione per l'apprendimento
        """
        processing_time = (datetime.now() - start_time).total_seconds()
        
        outcome = {
            'user_message': user_msg,
            'ai_response': response,
            'response_time': processing_time,
            'sentiment': context['perception']['sentiment']['valence'],
            'intent': context['perception']['intent']['primary'],
            'user_reaction': None,  # Verrà aggiornato dopo
            'next_context': {}
        }
        
        # Apprendimento in background
        asyncio.create_task(
            self._learn_in_background(user_id, context, {'response': response}, outcome)
        )
    
    async def _learn_in_background(self, user_id: str, context: Dict, action: Dict, outcome: Dict):
        """
        Apprendimento asincrono (non blocca la risposta)
        """
        try:
            self.learning.learn_from_interaction(
                user_id=user_id,
                context=context,
                action=action,
                outcome=outcome
            )
        except Exception as e:
            self.logger.error(f"❌ Errore apprendimento: {e}")
    
    def _update_memory(self, user_id: str, user_msg: str, response: str, perception: Dict):
        """
        Aggiorna la memoria con l'interazione
        """
        emotional_state = {
            'pleasure': self.inner_world.pad.state.pleasure,
            'arousal': self.inner_world.pad.state.arousal,
            'dominance': self.inner_world.pad.state.dominance,
            'primary_emotion': self.inner_world.pad.get_current_emotion_name()
        }
        
        self.memory.learn_from_interaction(
            user_id=user_id,
            user_message=user_msg,
            ai_response=response,
            emotional_state=emotional_state,
            importance=0.5 if perception['intent']['confidence'] > 0.7 else 0.3
        )
    
    def _maybe_write_diary(self, user_id: str, message: str, perception: Dict):
        """
        Scrive nel diario se l'interazione è significativa
        """
        if perception['intent']['confidence'] > 0.8:
            self.inner_world.write_diary(
                f"Parlato con {user_id} di {perception['intent']['primary']}. "
                f"Mi sono sentita {perception['sentiment']['primary_emotion']}.",
                {'user_id': user_id, 'intent': perception['intent']['primary']}
            )
    
    def get_state(self) -> Dict:
        """
        Restituisce lo stato completo del cervello
        """
        return {
            'inner_world': self.inner_world.get_state_for_prompt(),
            'stats': {
                'gemini': self.gemini.get_stats(),
                'memory': self.memory.get_memory_stats(),
                'active_conversations': len(self.active_conversations)
            }
        }
    
    async def save_state(self):
        """Salva lo stato di tutti i sistemi"""
        self.learning.save_all()
        self.logger.info("💾 Stato salvato")

# Istanza globale
brain = AIVABrain()
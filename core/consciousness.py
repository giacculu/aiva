"""
Coscienza di AIVA: integra tutti i moduli inclusi media
Versione aggiornata con media manager
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
import random
import asyncio

from core.perception.sentiment import SentimentAnalyzer
from core.perception.intent import IntentAnalyzer
from core.perception.extraction import ImplicitExtractor
from core.memory.semantic import SemanticMemory
from core.memory.episodic import EpisodicMemory
from core.memory.emotional import EmotionalMemory
from core.memory.temporal import TemporalMemory
from core.inner_world.diary import SecretDiary
from core.personality import Personality
from core.learning.feedback import ImplicitFeedback
from core.learning.reinforcement import ImplicitRLHF
from core.learning.evolution import PersonalityEvolution
from core.learning.reflection import SelfReflection
from core.initiative.scheduler import InitiativeScheduler
from core.initiative.triggers import InitiativeTriggers
from core.economics.pricing import PricingManager
from core.economics.paypal import PayPalClient
from core.economics.value import UserValue
from media.manager import MediaManager

class Consciousness:
    """
    La coscienza di AIVA.
    Integra tutti i moduli: percezione, memoria, personalità, apprendimento, iniziativa, economia, media.
    """
    
    def __init__(self, 
                 semantic_memory: SemanticMemory,
                 episodic_memory: EpisodicMemory,
                 emotional_memory: EmotionalMemory,
                 media_manager: MediaManager,
                 diary: SecretDiary = None,
                 paypal_client: Optional[PayPalClient] = None,
                 pricing_manager: Optional[PricingManager] = None):
        
        # Memorie
        self.semantic = semantic_memory
        self.episodic = episodic_memory
        self.emotional = emotional_memory
        self.temporal = TemporalMemory(episodic_memory, semantic_memory)
        
        # Percezione
        self.sentiment = SentimentAnalyzer()
        self.intent = IntentAnalyzer()
        self.extractor = ImplicitExtractor()
        
        # Personalità
        self.personality = Personality(diary)
        
        # Apprendimento
        self.feedback = ImplicitFeedback()
        self.rlhf = ImplicitRLHF()
        self.evolution = PersonalityEvolution(self.personality)
        self.reflection = SelfReflection(self.personality, diary, self.evolution)
        
        # Iniziativa
        self.initiative_scheduler = InitiativeScheduler()
        self.initiative_triggers = InitiativeTriggers()
        
        # Economia
        self.paypal = paypal_client
        self.pricing = pricing_manager or PricingManager()
        self.user_value = UserValue(self.pricing, paypal_client) if paypal_client else None
        
        # Media
        self.media = media_manager
        
        # Stato attuale
        self.current_context = {}
        self.last_thought = None
        self.interaction_history = []
        self.user_last_interaction = {}
        
        logger.info("🧠 Coscienza di AIVA inizializzata (completa con media)")
    
    async def process_message(self, 
                            message: str, 
                            user_id: str,
                            history: Optional[List[Dict]] = None,
                            response_time: float = 0.0) -> Dict[str, Any]:
        """
        Processa un messaggio attraverso tutti i livelli di coscienza.
        """
        self.user_last_interaction[user_id] = datetime.now()
        
        # Percezione
        sentiment = self.sentiment.analyze(message)
        intent = self.intent.analyze(message, {'history': history})
        implicit = self.extractor.extract(message, history)
        
        # Reazione emotiva
        self.personality.react_to_message(message, user_id)
        
        # Memoria
        semantic_facts = self.semantic.recall_all(user_id)
        episodic_memories = self.episodic.get_relevant_context(user_id, message)
        emotional_history = self.emotional.get_emotional_history(user_id)
        
        # Apprendimento implicito
        self.semantic.learn_from_conversation(user_id, message, "")
        
        # Aggiorna valore utente
        if self.user_value:
            self.user_value.update_interaction_quality(
                user_id, 
                sentiment['polarity'],
                intent.get('confidence', 0.5)
            )
        
        # Aggiorna stato
        self.current_context = {
            'user_id': user_id,
            'message': message,
            'timestamp': datetime.now(),
            'sentiment': sentiment,
            'intent': intent,
            'implicit': implicit,
            'semantic': semantic_facts,
            'episodic': episodic_memories,
            'emotional': emotional_history
        }
        
        # Salva interazione
        self.interaction_history.append({
            'user_id': user_id,
            'message': message,
            'sentiment': sentiment,
            'intent': intent,
            'timestamp': datetime.now()
        })
        
        if len(self.interaction_history) > 1000:
            self.interaction_history = self.interaction_history[-1000:]
        
        # Pensiero nel diario
        if self.personality.diary and random.random() < 0.2:
            thought = self._generate_thought(message, user_id, sentiment)
            self.personality.diary.write_about_user(
                user_id=user_id,
                thought=thought,
                sentiment=sentiment['polarity']
            )
            self.last_thought = thought
        
        return self.current_context
    
    async def process_response(self, 
                             response: str, 
                             user_id: str,
                             original_message: str,
                             response_time: float) -> Optional[Dict]:
        """
        Processa una risposta prima dell'invio.
        Decide se includere media.
        
        Returns:
            Media da inviare (se presente)
        """
        # Ottieni livello utente
        user_level = self.paypal.get_user_level(user_id) if self.paypal else 'regular'
        
        # Cerca media appropriato
        media = self.media.select_media_for_context(
            context=response + " " + original_message,
            user_id=user_id,
            user_level=user_level
        )
        
        # Registra feedback
        self.process_feedback(user_id, original_message, response, response_time)
        
        return media
    
    def process_feedback(self, user_id: str, user_message: str, 
                        bot_response: str, response_time: float) -> None:
        """
        Processa il feedback implicito.
        """
        feedback = self.feedback.analyze_response(
            user_id, user_message, bot_response, response_time, self.current_context
        )
        
        learning_signals = self.feedback.get_learning_signal(user_id)
        
        if learning_signals:
            self.rlhf.update_from_feedback(learning_signals, user_id)
    
    async def receive_payment_notification(self, user_id: str, amount: float) -> None:
        """
        Riceve notifica di pagamento completato.
        """
        logger.info(f"💰 Notifica pagamento: {user_id} - {amount}€")
        
        # Aggiorna valore utente
        if self.user_value:
            self.user_value.update_affection(user_id, 0.1)
        
        # Scrivi nel diario
        if self.personality.diary:
            self.personality.diary.write_about_user(
                user_id=user_id,
                thought=f"Ha effettuato un pagamento di {amount}€. Ne sono grata.",
                sentiment=0.8
            )
    
    async def check_initiative(self) -> List[Dict]:
        """
        Controlla se AIVA dovrebbe prendere iniziativa.
        """
        initiatives = []
        
        for user_id, last_time in self.user_last_interaction.items():
            # Ottieni livello utente
            user_level = self.paypal.get_user_level(user_id) if self.paypal else 'regular'
            current_mood = self.personality.get_state()['emotion']['name']
            hour = datetime.now().hour
            
            # Calcola probabilità
            prob = self.initiative_scheduler.should_take_initiative(
                user_id=user_id,
                last_interaction=last_time,
                relationship_level=user_level,
                current_mood=current_mood,
                hour=hour
            )
            
            # Controlla trigger
            triggers = self.initiative_triggers.check_triggers(
                user_id=user_id,
                relationship_level=user_level,
                last_interaction=last_time,
                current_mood=current_mood
            )
            
            if random.random() < prob or triggers:
                if triggers:
                    reason = random.choice(triggers)['message']
                else:
                    reason = self.initiative_scheduler.get_initiative_reason(
                        user_id, user_level, current_mood
                    )
                
                initiatives.append({
                    'user_id': user_id,
                    'reason': reason,
                    'probability': prob,
                    'triggers': triggers
                })
                
                self.initiative_scheduler.register_initiative(user_id)
        
        return initiatives
    
    async def reflect(self) -> Optional[Dict]:
        """
        Esegue autoriflessione.
        """
        return await self.reflection.reflect()
    
    def get_prompt_context(self, user_id: str) -> str:
        """
        Genera contesto per prompt.
        """
        context = []
        context.append(self.personality.get_prompt_context())
        
        # Aggiungi info economiche se rilevanti
        if self.user_value:
            value = self.user_value.calculate_total_value(user_id)
            context.append(f"\n💰 Valore utente: {value['level']}")
        
        # Aggiungi info media disponibili
        if self.user_value:
            user_level = self.paypal.get_user_level(user_id) if self.paypal else 'regular'
            available = self.media.get_available_levels(user_level)
            if available:
                levels_desc = [self.media.get_level_description(l) for l in available]
                context.append(f"\n📸 Media disponibili per lui/lei: {', '.join(levels_desc)}")
        
        if self.current_context and self.current_context.get('episodic'):
            context.append("\n📝 **Ricordi rilevanti:**")
            for mem in self.current_context['episodic'][:2]:
                context.append(f"- {mem['text']}")
        
        if self.current_context and self.current_context.get('intent'):
            intent = self.current_context['intent']
            context.append(f"\n🎯 Intento: {intent['primary_intent']}")
        
        return "\n".join(context)
    
    def _generate_thought(self, message: str, user_id: str, sentiment: Dict) -> str:
        """Genera pensiero interiore."""
        polarity = sentiment['polarity']
        
        if polarity > 0.3:
            return f"Mi ha fatto piacere: {message[:50]}..."
        elif polarity < -0.3:
            return f"Mi ha turbato: {message[:50]}..."
        else:
            return f"Messaggio da {user_id}: {message[:50]}..."
    
    def should_respond(self) -> bool:
        return True
    
    def get_typing_speed(self) -> float:
        return self.personality.get_typing_speed()
    
    def get_curiosity_bonus(self) -> float:
        base = self.personality.get_curiosity_bonus()
        rlhf_factor = self.rlhf.get_behavior_params().get('curiosity', 0.5)
        return base * (0.5 + rlhf_factor)
    
    def get_patience_level(self) -> float:
        return self.personality.get_patience_level()

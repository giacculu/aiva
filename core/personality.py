"""
Personalità completa di AIVA: integra tutti gli aspetti del mondo interiore
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from core.inner_world.pad_model import PADModel
from core.inner_world.circadian import CircadianRhythm
from core.inner_world.interests import Interests
from core.inner_world.diary import SecretDiary
from core.inner_world.diary_analyzer import DiaryAnalyzer

class Personality:
    """
    La personalità completa di AIVA.
    Integra:
    - Emozioni (PAD model)
    - Energia (ciclo circadiano)
    - Interessi
    - Diario segreto
    - Autoriflessione
    """
    
    def __init__(self, diary: SecretDiary = None, crypto=None):
        # Inizializza componenti
        self.emotions = PADModel('serena')
        self.energy = CircadianRhythm()
        self.interests = Interests()
        
        # Diario (se fornito)
        self.diary = diary
        if diary:
            self.diary_analyzer = DiaryAnalyzer(diary)
        else:
            self.diary_analyzer = None
        
        # Stato complessivo
        self.last_update = datetime.now()
        
        logger.info("🧠 Personalità completa inizializzata")
    
    def update(self) -> None:
        """Aggiorna tutti i componenti interni."""
        now = datetime.now()
        hours_passed = (now - self.last_update).total_seconds() / 3600
        self.last_update = now
        
        # Aggiorna energia
        self.energy.update()
        
        # Aggiorna interessi
        self.interests.update(hours_passed)
    
    def react_to_message(self, message: str, user_id: Optional[str] = None) -> None:
        """
        Reagisce a un messaggio, aggiornando stato interno.
        """
        # Aggiorna tempo
        self.update()
        
        # Reazione emotiva
        self.emotions.react_to_message(message)
        
        # Rafforza interessi
        self.interests.reinforce_from_message(message)
        
        # Scrivi nel diario se significativo
        if self.diary and len(message) > 50 and random.random() < 0.3:
            self.diary.write(
                content=f"Ricevuto messaggio: {message[:100]}...",
                mood=self.emotions.get_emotion_name(),
                user_id=user_id,
                importance=0.2
            )
    
    # ========== STATO COMPLESSIVO ==========
    
    def get_state(self) -> Dict[str, Any]:
        """Restituisce lo stato completo della personalità."""
        emotion_name = self.emotions.get_emotion_name()
        emotion_emoji = self.emotions.get_emotion_emoji()
        
        return {
            'emotion': {
                'name': emotion_name,
                'emoji': emotion_emoji,
                'description': self.emotions.get_description(),
                'pad': self.emotions.get_state()
            },
            'energy': {
                'level': self.energy.get_energy_level(),
                'description': self.energy.get_energy_description(),
                'time': self.energy.get_time_of_day()
            },
            'interests': {
                'list': self.interests.get_current_interests(),
                'description': self.interests.get_context_string()
            },
            'typing_modifier': self.energy.get_typing_speed_modifier(),
            'patience': self.energy.get_patience_modifier(),
            'curiosity': self.energy.get_curiosity_modifier()
        }
    
    def get_prompt_context(self) -> str:
        """
        Genera contesto per il prompt dell'AI.
        """
        state = self.get_state()
        
        context = f"🎭 **Il tuo stato interiore:**\n"
        context += f"- Emozione: {state['emotion']['description']}\n"
        context += f"- Energia: {state['energy']['description']} ({state['energy']['time']})\n"
        
        if state['interests']['description']:
            context += f"- Interessi: {state['interests']['description']}\n"
        
        return context
    
    # ========== MODULATORI ==========
    
    def get_typing_speed(self) -> float:
        """Velocità di digitazione (per HumanBehaviorSimulator)."""
        return self.energy.get_typing_speed_modifier()
    
    def get_curiosity_bonus(self) -> float:
        """Bonus curiosità."""
        return self.energy.get_curiosity_modifier() * 50  # Scala 0-50
    
    def get_patience_level(self) -> float:
        """Livello pazienza."""
        return self.energy.get_patience_modifier()
    
    # ========== INTERAZIONE CON UTENTI ==========
    
    def get_feeling_about_user(self, user_id: str) -> str:
        """Come si sente verso un utente specifico."""
        if self.diary_analyzer:
            trend = self.diary_analyzer.get_user_relationship_trend(user_id)
            sentiment = trend.get('avg_sentiment', 0)
            
            if sentiment > 0.3:
                return "Ti adoro"
            elif sentiment > 0:
                return "Mi piaci"
            elif sentiment > -0.3:
                return "Mi sei indifferente"
            else:
                return "Non mi stai simpatico"
        
        # Fallback
        return "Non ti conosco abbastanza"
    
    def remember_significant_interaction(self, user_id: str, summary: str, 
                                        emotional_valence: float = 0.0) -> None:
        """Ricorda un'interazione significativa (nel diario)."""
        if self.diary:
            self.diary.write_about_user(
                user_id=user_id,
                thought=summary,
                sentiment=emotional_valence
            )
    
    # ========== RIFLESSIONE ==========
    
    def reflect(self) -> str:
        """
        Autoriflessione: AIVA pensa a se stessa.
        """
        if not self.diary_analyzer:
            return "Non ho ancora un diario per riflettere."
        
        growth = self.diary_analyzer.get_personal_growth()
        state = self.get_state()
        
        reflection = f"Sto pensando a me stessa...\n"
        reflection += f"In questo momento sono {state['emotion']['description']} e mi sento {state['energy']['description']}.\n"
        
        if 'message' in growth:
            reflection += growth['message']
        
        return reflection
    
    # ========== PERSISTENZA ==========
    
    def to_dict(self) -> Dict:
        """Serializza per persistenza."""
        return {
            'emotions': self.emotions.to_dict(),
            'energy': self.energy.to_dict(),
            'interests': self.interests.to_dict(),
            'last_update': self.last_update.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict, diary=None) -> 'Personality':
        """Ricrea da dizionario."""
        instance = cls(diary)
        instance.emotions = PADModel.from_dict(data.get('emotions', {}))
        instance.energy = CircadianRhythm.from_dict(data.get('energy', {}))
        instance.interests = Interests.from_dict(data.get('interests', {}))
        instance.last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))
        return instance
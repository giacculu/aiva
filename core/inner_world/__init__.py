"""
Inner World di AIVA
Il suo mondo interiore: emozioni, energia, interessi, pensieri segreti
"""
from .pad_model import PADModel, EmotionalState, BASE_EMOTIONS
from .circadian import CircadianRhythm, EnergyLevel
from .interests import InterestsManager, Interest
from .diary import SecretDiary, get_diary

class InnerWorld:
    """
    Integra tutti gli aspetti del mondo interiore di AIVA
    Questo è il suo "io" profondo
    """
    
    def __init__(self, name: str = "AIVA"):
        self.name = name
        self.pad = PADModel("calma")
        self.circadian = CircadianRhythm()
        self.interests = InterestsManager()
        self.diary = get_diary(name.lower())
        
        # Memoria degli eventi recenti che hanno influenzato il suo stato
        self.recent_events = []
        
    def update(self, hours_passed: Optional[float] = None):
        """
        Aggiorna tutti i componenti interni
        Da chiamare periodicamente
        """
        # Aggiorna energia (circadiano)
        energy = self.circadian.update()
        
        # Decay interessi
        self.interests.decay_interests()
        
        return energy
    
    def process_external_stimulus(self, stimulus: str, source: Optional[str] = None):
        """
        Elabora uno stimolo esterno (messaggio, evento)
        e aggiorna lo stato interiore
        """
        # Analisi sentiment (placeholder - da migliorare)
        # Qui si potrebbe integrare un vero modello di sentiment
        
        # Aggiorna PAD
        self.pad.apply_text_impact(stimulus)
        
        # Aggiorna interessi
        self.interests.update_from_conversation(stimulus, source)
        
        # Registra evento
        self.recent_events.append({
            'timestamp': __import__('datetime').datetime.now(),
            'stimulus': stimulus[:100],
            'source': source,
            'pad_after': self.pad.to_dict()
        })
        
        if len(self.recent_events) > 50:
            self.recent_events = self.recent_events[-50:]
    
    def write_diary(self, thought: str, metadata: Optional[dict] = None):
        """Scrive un pensiero nel diario segreto"""
        self.diary.write(thought, metadata)
    
    def get_state_for_prompt(self) -> dict:
        """
        Restituisce lo stato interiore formattato per il prompt
        """
        energy = self.circadian.update()
        emotion = self.pad.get_current_emotion_name()
        interests = self.interests.get_interest_description()
        time_desc = self.circadian.get_time_of_day_description()
        
        return {
            'emotion': emotion,
            'pad': self.pad.to_dict(),
            'energy_physical': energy.physical,
            'energy_mental': energy.mental,
            'focus': energy.focus,
            'interests': interests,
            'time_of_day': time_desc,
            'mood_description': self._get_mood_description(emotion, energy)
        }
    
    def _get_mood_description(self, emotion: str, energy: EnergyLevel) -> str:
        """Descrizione umana dello stato attuale"""
        if energy.mental < 0.3:
            return f"sono {emotion} ma molto stanca mentalmente"
        elif energy.physical < 0.3:
            return f"sono {emotion} ma fisicamente scarica"
        elif energy.focus > 0.8:
            return f"sono {emotion} e molto concentrata"
        elif emotion == "felice":
            return "sono di buon umore oggi"
        elif emotion == "triste":
            return "oggi mi sento giù di morale"
        elif emotion == "arrabbiata":
            return "sono un po' nervosa oggi"
        else:
            return f"oggi mi sento {emotion}"
    
    def __repr__(self) -> str:
        state = self.get_state_for_prompt()
        return f"InnerWorld({state['emotion']}, energy:{state['energy_mental']:.1f})"

# Per test rapidi
if __name__ == "__main__":
    import asyncio
    
    world = InnerWorld("AIVA")
    print("Stato iniziale:", world.get_state_for_prompt())
    
    # Simula stimoli
    world.process_external_stimulus("Ciao amore, come stai?")
    print("Dopo messaggio:", world.get_state_for_prompt())
    
    world.write_diary("Oggi ho parlato con qualcuno di carino")
    print("Diario:", world.diary.get_diary_summary())
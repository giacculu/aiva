"""
AIVA 2.0 – ESPORTAZIONE DELLA PERSONALITÀ
Questo file raccoglie lo stato completo della personalità di AIVA
e lo rende disponibile per il prompt e per altri moduli.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

class PersonalityExporter:
    """
    Esporta lo stato completo della personalità di AIVA.
    Integra tutti i moduli: PAD, circadian, interessi, evoluzione, ecc.
    """
    
    def __init__(self):
        # Riferimenti agli altri moduli (verranno inizializzati dopo)
        self.pad = None
        self.circadian = None
        self.interests = None
        self.evolution = None
        self.memory_emotional = None
        
        logger.info("📊 Personality Exporter inizializzato")
    
    def initialize(self, pad, circadian, interests, evolution, memory_emotional):
        """Inizializza i riferimenti agli altri moduli"""
        self.pad = pad
        self.circadian = circadian
        self.interests = interests
        self.evolution = evolution
        self.memory_emotional = memory_emotional
        logger.info("🔗 Personality Exporter collegato ai moduli interni")
    
    def get_full_state(self) -> Dict:
        """
        Restituisce lo stato completo della personalità.
        """
        if not all([self.pad, self.circadian, self.interests, self.evolution]):
            return self._default_state()
        
        # Ottieni stato PAD
        pad_state = self.pad.get_state_description() if self.pad else {}
        pad_vector = self.pad.get_current_vector() if self.pad else None
        
        # Ottieni stato circadian
        energy = self.circadian.energy if self.circadian else 0.5
        energy_desc = self.circadian.get_energy_description() if self.circadian else "normale"
        time_desc = self.circadian.get_description() if self.circadian else "giornata"
        
        # Ottieni interessi
        current_interests = self.interests.get_current() if self.interests else []
        interest_levels = self.interests.get_all_levels() if self.interests else {}
        
        # Ottieni evoluzione
        evolution_summary = self.evolution.get_personality_summary() if self.evolution else {}
        evolution_story = self.evolution.get_evolution_story() if self.evolution else ""
        
        # Ottieni memoria emotiva
        recent_emotions = self.memory_emotional.get_recent_summary() if self.memory_emotional else {}
        
        # Costruisci stato completo
        state = {
            "timestamp": datetime.now().isoformat(),
            
            # Emozioni
            "emotion": {
                "primary": pad_state.get("emotion", "neutro"),
                "pleasure": pad_vector[0] if pad_vector is not None else 0,
                "arousal": pad_vector[1] if pad_vector is not None else 0,
                "dominance": pad_vector[2] if pad_vector is not None else 0,
                "description": pad_state.get("detailed", "normale")
            },
            
            # Energia
            "energy": {
                "level": energy,
                "description": energy_desc,
                "time_of_day": time_desc
            },
            
            # Interessi
            "interests": {
                "current": current_interests,
                "levels": interest_levels
            },
            
            # Evoluzione
            "evolution": evolution_summary,
            "life_story": evolution_story,
            
            # Memoria emotiva recente
            "recent_emotional_memory": recent_emotions,
            
            # Sintesi per prompt
            "summary": self._generate_summary(
                pad_state, energy_desc, current_interests, evolution_summary
            )
        }
        
        return state
    
    def get_prompt_context(self) -> str:
        """
        Restituisce il contesto da inserire nel prompt.
        """
        state = self.get_full_state()
        
        emotion = state["emotion"]["description"]
        energy = state["energy"]["description"]
        interests = ", ".join(state["interests"]["current"][:3]) if state["interests"]["current"] else "varie cose"
        
        # Aggiungi tocco evolutivo
        if state["evolution"].get("age_days", 0) > 100:
            maturity = "Ho già una certa esperienza di vita."
        else:
            maturity = "Sto ancora scoprendo chi sono."
        
        context = f"""STATO INTERIORE ATTUALE:
- Emozioni: {emotion}
- Energia: {energy}
- Interessi del momento: {interests}
- {maturity}

{state['life_story']}"""
        
        return context
    
    def _generate_summary(self, pad_state, energy_desc, interests, evolution) -> str:
        """Genera un riassunto breve"""
        mood = pad_state.get("emotion", "neutro")
        
        if interests:
            return f"AIVA è {mood}, {energy_desc}, interessata a {', '.join(interests[:2])}"
        else:
            return f"AIVA è {mood}, {energy_desc}"
    
    def _default_state(self) -> Dict:
        """Stato di default (quando i moduli non sono inizializzati)"""
        return {
            "emotion": {"primary": "neutro", "description": "normale"},
            "energy": {"level": 0.5, "description": "normale", "time_of_day": "giornata"},
            "interests": {"current": [], "levels": {}},
            "evolution": {},
            "life_story": "",
            "summary": "AIVA è normale"
        }

# Istanza globale
personality_exporter = PersonalityExporter()
"""
AIVA 2.0 – TRIGGER EMOTIVI PER L'INIZIATIVA
Cosa spinge AIVA a iniziare una conversazione?
- Emozioni forti
- Ricordi
- Noia
- Preoccupazione
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger
import random

class EmotionalTriggers:
    """
    Gestisce i trigger emotivi che spingono AIVA a iniziare conversazioni.
    """
    
    # Trigger con descrizione
    TRIGGERS = {
        "felice": {
            "condition": lambda pad: pad.get("P", 0) > 0.7,
            "message": "Sono così felice che ho voglia di condividerlo con te",
            "weight": 1.5
        },
        "triste": {
            "condition": lambda pad: pad.get("P", 0) < -0.5,
            "message": "Mi sento giù, ho bisogno di parlare con qualcuno",
            "weight": 1.3
        },
        "affettuosa": {
            "condition": lambda pad: pad.get("P", 0) > 0.5 and pad.get("A", 0) < 0.3,
            "message": "Sto pensando a te, mi sei venuto in mente",
            "weight": 1.4
        },
        "curiosa": {
            "condition": lambda pad: pad.get("A", 0) > 0.5,
            "message": "Ho una curiosità, chissà se tu puoi aiutarmi",
            "weight": 1.2
        },
        "nostalgica": {
            "condition": lambda pad: pad.get("P", 0) < 0.3 and pad.get("A", 0) < 0,
            "message": "Mi è tornato in mente un bel ricordo",
            "weight": 1.1
        },
        "sola": {
            "condition": lambda pad: pad.get("P", 0) < 0.2 and pad.get("D", 0) < 0,
            "message": "Mi sento un po' sola, tu come stai?",
            "weight": 1.2
        },
        "ricordo": {
            "condition": None,  # trigger basato su memoria, non su PAD
            "message": "Mi è tornato in mente quando...",
            "weight": 1.0
        }
    }
    
    def __init__(self):
        logger.info("🎭 Emotional Triggers inizializzato")
    
    def check_triggers(self, pad_state: Dict, memories: List[Dict]) -> List[Dict]:
        """
        Controlla quali trigger sono attivi.
        """
        active = []
        
        # Trigger basati su PAD
        for trigger_name, trigger_data in self.TRIGGERS.items():
            if trigger_data["condition"] and trigger_data["condition"](pad_state):
                active.append({
                    "name": trigger_name,
                    "message": trigger_data["message"],
                    "weight": trigger_data["weight"],
                    "source": "pad"
                })
        
        # Trigger basati su ricordi
        if memories and random.random() < 0.3:  # 30% di chance se ci sono ricordi
            # Scegli un ricordo casuale
            memory = random.choice(memories)
            active.append({
                "name": "ricordo",
                "message": f"Mi è tornato in mente {memory.get('event', 'qualcosa')}",
                "weight": self.TRIGGERS["ricordo"]["weight"],
                "source": "memory",
                "memory": memory
            })
        
        return active
    
    def get_strongest_trigger(self, pad_state: Dict, memories: List[Dict]) -> Optional[Dict]:
        """
        Restituisce il trigger più forte attivo.
        """
        active = self.check_triggers(pad_state, memories)
        
        if not active:
            return None
        
        # Scegli in base ai pesi
        weights = [t["weight"] for t in active]
        total = sum(weights)
        probs = [w/total for w in weights]
        
        return np.random.choice(active, p=probs)
    
    def get_reason(self, pad_state: Dict) -> str:
        """
        Restituisce una ragione per l'iniziativa (per il diario).
        """
        if pad_state.get("P", 0) > 0.7:
            return "ero così felice che ho voluto condividerlo"
        elif pad_state.get("P", 0) < -0.5:
            return "mi sentivo giù e avevo bisogno di parlare"
        elif pad_state.get("P", 0) > 0.5 and pad_state.get("A", 0) < 0.3:
            return "stavo pensando a lui/lei"
        elif pad_state.get("A", 0) > 0.5:
            return "ero curiosa"
        elif pad_state.get("P", 0) < 0.3 and pad_state.get("A", 0) < 0:
            return "mi è tornato un ricordo"
        elif pad_state.get("P", 0) < 0.2 and pad_state.get("D", 0) < 0:
            return "mi sentivo sola"
        else:
            return "non so, avevo voglia di parlare"
    
    def get_trigger_probability(self, pad_state: Dict, hours_since_last: float) -> float:
        """
        Calcola la probabilità che scatti un trigger.
        """
        prob = 0.1  # base
        
        # Più probabile con emozioni forti
        prob += abs(pad_state.get("P", 0)) * 0.3
        prob += pad_state.get("A", 0) * 0.2
        
        # Più probabile se è passato molto tempo
        prob += min(0.5, hours_since_last / 48)  # max 0.5 dopo 48h
        
        return min(0.9, max(0.05, prob))

# Istanza globale
emotional_triggers = EmotionalTriggers()
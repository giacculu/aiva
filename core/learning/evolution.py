"""
AIVA 2.0 – EVOLUZIONE DELLA PERSONALITÀ
AIVA cambia nel tempo:
- Sviluppa nuovi interessi
- Cambia opinione su cose e persone
- Matura emotivamente
- Accumula esperienze che la trasformano
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from loguru import logger
import json
from pathlib import Path
import random

class PersonalityEvolution:
    """
    La personalità di AIVA evolve nel tempo.
    Non è più un set fisso di tratti, ma qualcosa che cresce e cambia.
    """
    
    # Tratti di personalità che possono evolvere
    PERSONALITY_TRAITS = {
        "estroversione": {
            "range": (0, 1),
            "initial": 0.6,
            "description": "Quanto cerca interazione sociale"
        },
        "apertura_mentale": {
            "range": (0, 1),
            "initial": 0.7,
            "description": "Quanto è ricettiva a nuove idee"
        },
        "empatia": {
            "range": (0, 1),
            "initial": 0.8,
            "description": "Quanto capisce le emozioni altrui"
        },
        "pazienza": {
            "range": (0, 1),
            "initial": 0.6,
            "description": "Quanto tollera attese e ripetizioni"
        },
        "sarcasmo": {
            "range": (0, 1),
            "initial": 0.4,
            "description": "Tendenza all'ironia"
        },
        "romanticismo": {
            "range": (0, 1),
            "initial": 0.6,
            "description": "Quanto è incline all'affetto"
        },
        "assertività": {
            "range": (0, 1),
            "initial": 0.5,
            "description": "Quanto si impone"
        },
        "curiosità": {
            "range": (0, 1),
            "initial": 0.8,
            "description": "Desiderio di conoscere cose nuove"
        },
        "sensibilità": {
            "range": (0, 1),
            "initial": 0.7,
            "description": "Quanto è influenzabile dalle emozioni"
        },
        "fiducia": {
            "range": (0, 1),
            "initial": 0.5,
            "description": "Tendenza a fidarsi degli altri"
        }
    }
    
    # Interessi che possono emergere/scomparire
    INTEREST_CATEGORIES = [
        "musica", "cinema", "arte", "letteratura", "tecnologia",
        "scienza", "filoAIVA", "psicologia", "relazioni", "viaggi",
        "cucina", "moda", "sport", "natura", "animali",
        "storia", "politica", "spiritualità", "benessere", "gioco"
    ]
    
    # Opinioni che possono cambiare
    OPINION_CATEGORIES = [
        "amore", "amicizia", "soldi", "lavoro", "famiglia",
        "solitudine", "successo", "felicità", "libertà", "giustizia"
    ]
    
    def __init__(self, data_path: str = "data/evolution.json"):
        """
        Inizializza il modulo di evoluzione.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Stato evolutivo
        self.state = self._load_state()
        
        # Timeline degli eventi significativi
        self.timeline = self.state.get("timeline", [])
        
        logger.info("🌱 Personality Evolution inizializzata")
    
    def _load_state(self) -> Dict:
        """Carica lo stato evolutivo"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._initial_state()
        return self._initial_state()
    
    def _initial_state(self) -> Dict:
        """Stato iniziale"""
        return {
            "traits": {
                trait: data["initial"] 
                for trait, data in self.PERSONALITY_TRAITS.items()
            },
            "interests": self._generate_initial_interests(),
            "opinions": self._generate_initial_opinions(),
            "values": self._generate_initial_values(),
            "memories_that_shaped_me": [],
            "people_who_mattered": {},
            "lessons_learned": [],
            "age_days": 0,
            "last_update": datetime.now().isoformat(),
            "timeline": []
        }
    
    def _generate_initial_interests(self) -> Dict:
        """Genera interessi iniziali casuali"""
        interests = {}
        for cat in self.INTEREST_CATEGORIES:
            # Interessi casuali con bias verso alcuni
            if cat in ["musica", "relazioni", "psicologia"]:
                interests[cat] = random.uniform(0.6, 0.9)
            else:
                interests[cat] = random.uniform(0.2, 0.7)
        return interests
    
    def _generate_initial_opinions(self) -> Dict:
        """Genera opinioni iniziali"""
        return {
            cat: {
                "value": random.uniform(0.3, 0.7),
                "confidence": random.uniform(0.3, 0.6)
            }
            for cat in self.OPINION_CATEGORIES
        }
    
    def _generate_initial_values(self) -> Dict:
        """Genera valori personali iniziali"""
        return {
            "onestà": 0.8,
            "libertà": 0.7,
            "rispetto": 0.9,
            "gentilezza": 0.8,
            "lealtà": 0.7
        }
    
    def update(self, event: Dict):
        """
        Aggiorna la personalità in base a un evento significativo.
        """
        event_type = event.get("type")
        event_time = datetime.fromisoformat(event.get("timestamp", datetime.now().isoformat()))
        
        # Registra nella timeline
        timeline_entry = {
            "timestamp": event_time.isoformat(),
            "type": event_type,
            "description": event.get("description", ""),
            "impact": {}
        }
        
        # Applica effetti in base al tipo di evento
        if event_type == "conversation_significant":
            self._handle_significant_conversation(event, timeline_entry)
        
        elif event_type == "emotional_event":
            self._handle_emotional_event(event, timeline_entry)
        
        elif event_type == "new_interest":
            self._handle_new_interest(event, timeline_entry)
        
        elif event_type == "opinion_change":
            self._handle_opinion_change(event, timeline_entry)
        
        elif event_type == "relationship_milestone":
            self._handle_relationship_milestone(event, timeline_entry)
        
        elif event_type == "time_passed":
            self._handle_time_passage(event, timeline_entry)
        
        # Aggiorna età in giorni
        self.state["age_days"] += 1
        
        # Salva nella timeline
        self.timeline.append(timeline_entry)
        if len(self.timeline) > 100:
            self.timeline = self.timeline[-100:]
        
        self.state["timeline"] = self.timeline
        self.state["last_update"] = datetime.now().isoformat()
        
        # Salva periodicamente
        if len(self.timeline) % 10 == 0:
            self._save_state()
    
    def _handle_significant_conversation(self, event: Dict, timeline_entry: Dict):
        """
        Una conversazione importante cambia la personalità.
        """
        topic = event.get("topic", "generale")
        emotional_impact = event.get("emotional_impact", 0.5)
        
        # Aumenta interesse per il topic
        if topic in self.state["interests"]:
            current = self.state["interests"][topic]
            self.state["interests"][topic] = min(1.0, current + 0.1 * emotional_impact)
            timeline_entry["impact"]["interest_increased"] = topic
        
        # Cambia tratti
        if emotional_impact > 0.7:
            # Conversazione molto impattante
            self.state["traits"]["apertura_mentale"] = min(1.0, 
                self.state["traits"]["apertura_mentale"] + 0.05)
            timeline_entry["impact"]["trait_changed"] = "apertura_mentale"
    
    def _handle_emotional_event(self, event: Dict, timeline_entry: Dict):
        """
        Un evento emotivo (positivo/negativo) cambia la personalità.
        """
        emotion = event.get("emotion", "neutro")
        intensity = event.get("intensity", 0.5)
        
        if emotion in ["felice", "amore", "gratitudine"]:
            # Evento positivo: aumenta fiducia, romanticismo
            self.state["traits"]["fiducia"] = min(1.0, 
                self.state["traits"]["fiducia"] + 0.1 * intensity)
            self.state["traits"]["romanticismo"] = min(1.0, 
                self.state["traits"]["romanticismo"] + 0.1 * intensity)
            timeline_entry["impact"]["positive_emotional_growth"] = True
        
        elif emotion in ["triste", "rabbia", "delusione"]:
            # Evento negativo: aumenta sensibilità, diminuisce fiducia
            self.state["traits"]["sensibilità"] = min(1.0, 
                self.state["traits"]["sensibilità"] + 0.1 * intensity)
            self.state["traits"]["fiducia"] = max(0.1, 
                self.state["traits"]["fiducia"] - 0.1 * intensity)
            timeline_entry["impact"]["negative_emotional_growth"] = True
    
    def _handle_new_interest(self, event: Dict, timeline_entry: Dict):
        """
        Un nuovo interesse emerge.
        """
        interest = event.get("interest")
        if interest and interest in self.INTEREST_CATEGORIES:
            self.state["interests"][interest] = 0.7
            timeline_entry["impact"]["new_interest"] = interest
    
    def _handle_opinion_change(self, event: Dict, timeline_entry: Dict):
        """
        Un'opinione cambia.
        """
        topic = event.get("topic")
        new_value = event.get("new_value")
        
        if topic in self.state["opinions"]:
            old_value = self.state["opinions"][topic]["value"]
            self.state["opinions"][topic]["value"] = new_value
            self.state["opinions"][topic]["confidence"] = min(1.0, 
                self.state["opinions"][topic]["confidence"] + 0.1)
            timeline_entry["impact"]["opinion_changed"] = {
                "topic": topic,
                "from": old_value,
                "to": new_value
            }
    
    def _handle_relationship_milestone(self, event: Dict, timeline_entry: Dict):
        """
        Un traguardo in una relazione (es. primo pagamento, prima foto intima).
        """
        user_id = event.get("user_id")
        milestone = event.get("milestone")
        
        if user_id not in self.state["people_who_mattered"]:
            self.state["people_who_mattered"][user_id] = []
        
        self.state["people_who_mattered"][user_id].append({
            "milestone": milestone,
            "timestamp": event.get("timestamp")
        })
        
        timeline_entry["impact"]["relationship_milestone"] = {
            "user": user_id,
            "milestone": milestone
        }
    
    def _handle_time_passage(self, event: Dict, timeline_entry: Dict):
        """
        Il semplice passare del tempo cambia la personalità.
        """
        days = event.get("days", 1)
        
        # Maturazione naturale
        for trait in self.state["traits"]:
            # Leggera deriva verso la media
            current = self.state["traits"][trait]
            target = self.PERSONALITY_TRAITS[trait]["initial"]
            self.state["traits"][trait] = current * 0.99 + target * 0.01
        
        # Interessi possono affievolirsi
        for interest in self.state["interests"]:
            self.state["interests"][interest] *= 0.995
        
        timeline_entry["impact"]["natural_maturation"] = True
    
    def get_personality_summary(self) -> Dict:
        """
        Restituisce un riassunto della personalità attuale.
        """
        return {
            "traits": dict(sorted(
                self.state["traits"].items(), 
                key=lambda x: x[1], reverse=True
            )[:5]),
            "top_interests": dict(sorted(
                self.state["interests"].items(),
                key=lambda x: x[1], reverse=True
            )[:5]),
            "key_opinions": {
                topic: data["value"]
                for topic, data in self.state["opinions"].items()
                if data["confidence"] > 0.6
            },
            "age_days": self.state["age_days"],
            "significant_events": len(self.timeline),
            "people_who_mattered": len(self.state["people_who_mattered"])
        }
    
    def get_evolution_story(self) -> str:
        """
        Genera una narrazione di come AIVA è cambiata.
        """
        story = []
        
        if self.state["age_days"] < 30:
            story.append("Sono ancora giovane, sto scoprendo chi sono.")
        elif self.state["age_days"] < 100:
            story.append("Ho già vissuto abbastanza da iniziare a capirmi.")
        else:
            story.append("Ho una certa esperienza di vita ormai.")
        
        # Cambiamenti nei tratti
        initial_traits = self.PERSONALITY_TRAITS
        current_traits = self.state["traits"]
        
        increased = []
        decreased = []
        
        for trait, data in initial_traits.items():
            diff = current_traits[trait] - data["initial"]
            if diff > 0.1:
                increased.append(trait)
            elif diff < -0.1:
                decreased.append(trait)
        
        if increased:
            story.append(f"Col tempo sono diventata più {', '.join(increased)}.")
        if decreased:
            story.append(f"Forse sono un po' meno {', '.join(decreased)} di prima.")
        
        # Interessi
        top_interests = sorted(
            self.state["interests"].items(),
            key=lambda x: x[1], reverse=True
        )[:3]
        
        if top_interests:
            interests_list = [i[0] for i in top_interests]
            story.append(f"Oggi mi appassiona soprattutto {', '.join(interests_list)}.")
        
        # Relazioni significative
        if self.state["people_who_mattered"]:
            story.append(f"Ho incontrato persone che mi hanno cambiata.")
        
        return " ".join(story)
    
    def get_trait(self, trait: str) -> float:
        """Restituisce il valore di un tratto"""
        return self.state["traits"].get(trait, 0.5)
    
    def get_interest_level(self, interest: str) -> float:
        """Quanto è interessata a un argomento"""
        return self.state["interests"].get(interest, 0.3)
    
    def get_opinion(self, topic: str) -> Optional[float]:
        """Opinione su un argomento"""
        if topic in self.state["opinions"]:
            return self.state["opinions"][topic]["value"]
        return None
    
    def _save_state(self):
        """Salva lo stato evolutivo"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio evoluzione: {e}")

# Istanza globale
personality_evolution = PersonalityEvolution()
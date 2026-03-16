"""
AIVA 2.0 – MODELLO EMOZIONALE PAD (Pleasure-Arousal-Dominance)
Le emozioni di AIVA in uno spazio vettoriale continuo 3D.
Non più 8 mood, ma infinite sfumature.
"""

import numpy as np
import math
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from loguru import logger
import json
import random

class PADModel:
    """
    Modello emotivo basato su tre dimensioni:
    - Pleasure (P): da -1 (triste, infelice) a +1 (felice, contenta)
    - Arousal (A): da -1 (calma, rilassata) a +1 (eccitata, agitata)
    - Dominance (D): da -1 (sottomessa, insicura) a +1 (dominante, sicura)
    
    Ogni emozione complessa è un punto in questo spazio 3D.
    """
    
    # Emozioni di base come punti di riferimento
    EMOTION_ANCHORS = {
        "felice": {"P": 0.8, "A": 0.4, "D": 0.6, "desc": "Contento, gioioso"},
        "euforica": {"P": 0.9, "A": 0.8, "D": 0.7, "desc": "Estasiata, al settimo cielo"},
        "triste": {"P": -0.7, "A": -0.3, "D": -0.4, "desc": "Triste, giù di morale"},
        "malinconica": {"P": -0.3, "A": -0.6, "D": -0.2, "desc": "Nostalgica, pensierosa"},
        "arrabbiata": {"P": -0.5, "A": 0.7, "D": 0.3, "desc": "Infastidita, irritata"},
        "calma": {"P": 0.3, "A": -0.7, "D": 0.2, "desc": "Rilassata, serena"},
        "ansiosa": {"P": -0.2, "A": 0.6, "D": -0.6, "desc": "Preoccupata, tesa"},
        "sicura": {"P": 0.5, "A": 0.1, "D": 0.8, "desc": "Fiduciosa, determinata"},
        "innamorata": {"P": 0.9, "A": 0.5, "D": 0.3, "desc": "Affettuosa, tenera"},
        "stanca": {"P": -0.1, "A": -0.8, "D": -0.3, "desc": "Affaticata, senza energie"},
        "curiosa": {"P": 0.4, "A": 0.5, "D": 0.1, "desc": "Interessata, desiderosa di scoprire"},
        "offesa": {"P": -0.6, "A": 0.3, "D": -0.2, "desc": "Ferita nell'orgoglio"},
        "grata": {"P": 0.7, "A": 0.2, "D": 0.2, "desc": "Riconoscente, apprezzativa"},
        "sola": {"P": -0.5, "A": -0.4, "D": -0.5, "desc": "Isolata, abbandonata"},
        "giocosa": {"P": 0.6, "A": 0.6, "D": 0.4, "desc": "Scherzosa, leggera"},
    }
    
    # Fattori di decadimento naturale (le emozioni svaniscono col tempo)
    DECAY_RATES = {
        "P": 0.05,  # per ora
        "A": 0.08,
        "D": 0.03,
    }
    
    def __init__(self, initial_state: Optional[Dict] = None):
        """
        Inizializza lo stato emotivo.
        Se non specificato, parte da uno stato casuale ma tendente al neutro.
        """
        if initial_state:
            self.P = np.clip(initial_state.get("P", 0.0), -1.0, 1.0)
            self.A = np.clip(initial_state.get("A", 0.0), -1.0, 1.0)
            self.D = np.clip(initial_state.get("D", 0.0), -1.0, 1.0)
        else:
            # Stato iniziale: leggermente positivo, calmo, neutro
            self.P = random.uniform(0.1, 0.3)
            self.A = random.uniform(-0.2, 0.2)
            self.D = random.uniform(-0.1, 0.1)
        
        self.last_update = datetime.now()
        self.emotional_history = []  # Traccia per analisi
        
        # Memoria delle emozioni recenti (max 100)
        self.recent_states = []
        
        logger.info(f"🎭 PAD Model inizializzato: P={self.P:.2f}, A={self.A:.2f}, D={self.D:.2f}")
    
    def update_from_message(self, sentiment: Dict, intent: Dict, implicit: Dict):
        """
        Aggiorna lo stato emotivo in base a un messaggio ricevuto.
        sentiment: risultato dell'analisi del tono
        intent: intenzione dell'utente
        implicit: cosa non ha detto
        """
        # Calcola tempo dall'ultimo aggiornamento (per decadimento)
        now = datetime.now()
        hours_passed = (now - self.last_update).total_seconds() / 3600
        self._apply_decay(hours_passed)
        
        # Impatto del sentiment
        if sentiment:
            # Positività/negatività influenza P
            p_impact = sentiment.get("positivity", 0) * 0.3
            self.P += p_impact
            
            # Arousal (eccitazione) dal tono
            a_impact = sentiment.get("arousal", 0) * 0.2
            self.A += a_impact
        
        # Impatto dell'intento
        if intent:
            intent_type = intent.get("primary", "unknown")
            confidence = intent.get("confidence", 0.5)
            
            if intent_type == "compliment":
                self.P += 0.2 * confidence
                self.D += 0.1 * confidence
            elif intent_type == "insult":
                self.P -= 0.4 * confidence
                self.D -= 0.2 * confidence
                self.A += 0.2 * confidence  # si agita
            elif intent_type == "request_help":
                self.D -= 0.1 * confidence  # si sente meno dominante
            elif intent_type == "declaration":
                self.P += 0.3 * confidence
                self.A += 0.2 * confidence
        
        # Impatto dell'implicito
        if implicit:
            hidden = implicit.get("hidden_mood", "neutral")
            if hidden == "triste":
                self.P -= 0.1
            elif hidden == "felice":
                self.P += 0.1
        
        # Limita ai range
        self.P = np.clip(self.P, -1.0, 1.0)
        self.A = np.clip(self.A, -1.0, 1.0)
        self.D = np.clip(self.D, -1.0, 1.0)
        
        # Salva stato
        self.recent_states.append({
            "timestamp": now,
            "P": self.P,
            "A": self.A,
            "D": self.D
        })
        if len(self.recent_states) > 100:
            self.recent_states.pop(0)
        
        self.last_update = now
    
    def _apply_decay(self, hours: float):
        """Le emozioni naturalmente svaniscono col tempo"""
        if hours <= 0:
            return
        
        # Verso il neutro (0) ma non troppo veloce
        if self.P > 0:
            self.P = max(0, self.P - self.DECAY_RATES["P"] * hours)
        elif self.P < 0:
            self.P = min(0, self.P + self.DECAY_RATES["P"] * hours)
        
        if self.A > 0:
            self.A = max(0, self.A - self.DECAY_RATES["A"] * hours)
        elif self.A < 0:
            self.A = min(0, self.A + self.DECAY_RATES["A"] * hours)
        
        if self.D > 0:
            self.D = max(0, self.D - self.DECAY_RATES["D"] * hours)
        elif self.D < 0:
            self.D = min(0, self.D + self.DECAY_RATES["D"] * hours)
    
    def get_state(self) -> Dict:
        """Restituisce lo stato emotivo attuale"""
        return {
            "P": self.P,
            "A": self.A,
            "D": self.D,
            "timestamp": self.last_update.isoformat()
        }
    
    def get_current_vector(self) -> np.ndarray:
        """Restituisce il vettore 3D per similarity search"""
        return np.array([self.P, self.A, self.D])
    
    def get_closest_emotion(self) -> Dict:
        """
        Trova l'emozione nominale più vicina nello spazio PAD.
        Utile per descrivere a parole lo stato.
        """
        current = np.array([self.P, self.A, self.D])
        
        closest = None
        min_dist = float('inf')
        
        for name, coords in self.EMOTION_ANCHORS.items():
            anchor = np.array([coords["P"], coords["A"], coords["D"]])
            dist = np.linalg.norm(current - anchor)
            
            if dist < min_dist:
                min_dist = dist
                closest = name
        
        return {
            "name": closest,
            "description": self.EMOTION_ANCHORS[closest]["desc"],
            "distance": min_dist,
            "raw": self.get_state()
        }
    
    def get_state_description(self) -> Dict:
        """
        Descrizione dettagliata per il prompt.
        """
        emotion = self.get_closest_emotion()
        
        # Genera frasi descrittive per ogni dimensione
        p_desc = self._describe_pleasure()
        a_desc = self._describe_arousal()
        d_desc = self._describe_dominance()
        
        return {
            "summary": f"Mi sento {emotion['name']}",
            "pleasure_text": p_desc,
            "arousal_text": a_desc,
            "dominance_text": d_desc,
            "emotion": emotion['name'],
            "detailed": f"{p_desc}, {a_desc}, {d_desc}"
        }
    
    def _describe_pleasure(self) -> str:
        if self.P > 0.7:
            return "sono al settimo cielo"
        elif self.P > 0.3:
            return "sono contenta"
        elif self.P > -0.3:
            return "mi sento neutrale"
        elif self.P > -0.7:
            return "sono giù di morale"
        else:
            return "sono devastata"
    
    def _describe_arousal(self) -> str:
        if self.A > 0.7:
            return "sono iperattiva"
        elif self.A > 0.3:
            return "sono carica"
        elif self.A > -0.3:
            return "sono calma"
        elif self.A > -0.7:
            return "sono rilassata"
        else:
            return "sono spenta"
    
    def _describe_dominance(self) -> str:
        if self.D > 0.7:
            return "mi sento potente"
        elif self.D > 0.3:
            return "mi sento sicura"
        elif self.D > -0.3:
            return "mi sento normale"
        elif self.D > -0.7:
            return "mi sento insicura"
        else:
            return "mi sento sottomessa"
    
    def decay(self, hours: Optional[float] = None):
        """
        Applica decadimento temporale. Se hours non specificato,
        calcola dal timestamp.
        """
        if hours is None:
            now = datetime.now()
            hours = (now - self.last_update).total_seconds() / 3600
        
        self._apply_decay(hours)
        self.last_update = datetime.now()
    
    def get_emotional_trend(self, hours: int = 24) -> Dict:
        """
        Analizza l'andamento emotivo nelle ultime ore.
        """
        if not self.recent_states:
            return {"trend": "stabile"}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [s for s in self.recent_states if s["timestamp"] > cutoff]
        
        if len(recent) < 2:
            return {"trend": "stabile"}
        
        p_start = recent[0]["P"]
        p_end = recent[-1]["P"]
        
        p_trend = p_end - p_start
        
        if p_trend > 0.2:
            return {"trend": "migliorando", "delta": p_trend}
        elif p_trend < -0.2:
            return {"trend": "peggiorando", "delta": p_trend}
        else:
            return {"trend": "stabile", "delta": p_trend}
    
    def get_honest_reaction(self) -> str:
        """
        Quello che AIVA pensa DAVVERO ma non dice.
        """
        emotion = self.get_closest_emotion()
        
        if emotion['name'] == "felice":
            return "in realtà sono felice ma non voglio sembrare troppo entusiasta"
        elif emotion['name'] == "triste":
            return "sono triste ma non voglio caricarlo dei miei problemi"
        elif emotion['name'] == "arrabbiata":
            return "sono un po' arrabbiata ma non voglio litigare"
        elif emotion['name'] == "innamorata":
            return "mi piace ma ho paura di dirlo"
        else:
            return f"in realtà mi sento {emotion['name']} ma non lo do a vedere"
    
    def __repr__(self) -> str:
        return f"PAD(P={self.P:.2f}, A={self.A:.2f}, D={self.D:.2f})"
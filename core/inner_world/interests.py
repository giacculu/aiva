"""
AIVA 2.0 – GESTIONE INTERESSI
Gli interessi di AIVA evolvono nel tempo.
Nuove passioni emergono, altre svaniscono.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path
import random

class InterestManager:
    """
    Gestisce gli interessi di AIVA.
    Ogni interesse ha un livello (0-1) che cambia nel tempo.
    """
    
    # Lista di possibili interessi
    INTEREST_CATEGORIES = [
        "musica", "cinema", "arte", "letteratura", "poesia",
        "tecnologia", "scienza", "filoAIVA", "psicologia", "società",
        "viaggi", "cucina", "moda", "sport", "fitness",
        "natura", "animali", "giardinaggio", "ecologia",
        "storia", "politica", "attualità",
        "spiritualità", "meditazione", "benessere",
        "giochi", "videogiochi", "fotografia",
        "relazioni", "amore", "amicizia",
        "sogni", "fantasia", "creatività"
    ]
    
    # Interessi base (sempre presenti)
    CORE_INTERESTS = ["relazioni", "musica", "psicologia"]
    
    def __init__(self, data_path: str = "data/interests.json"):
        """
        Inizializza il gestore interessi.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.interests = self._load_data()
        self.last_update = datetime.now()
        
        logger.info("🎯 Interest Manager inizializzato")
    
    def _load_data(self) -> Dict:
        """Carica interessi"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._initial_interests()
        return self._initial_interests()
    
    def _initial_interests(self) -> Dict:
        """Interessi iniziali"""
        interests = {}
        
        # Core interests sempre alti
        for cat in self.CORE_INTERESTS:
            interests[cat] = random.uniform(0.6, 0.8)
        
        # Altri interessi casuali
        others = [c for c in self.INTEREST_CATEGORIES if c not in self.CORE_INTERESTS]
        for cat in random.sample(others, 10):
            interests[cat] = random.uniform(0.2, 0.5)
        
        return {
            "levels": interests,
            "history": [],
            "last_update": datetime.now().isoformat()
        }
    
    def _save_data(self):
        """Salva interessi"""
        self.interests["last_update"] = datetime.now().isoformat()
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.interests, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio interessi: {e}")
    
    def update(self, hours_passed: Optional[float] = None):
        """
        Aggiorna gli interessi nel tempo.
        """
        if hours_passed is None:
            now = datetime.now()
            last = datetime.fromisoformat(self.interests["last_update"])
            hours_passed = (now - last).total_seconds() / 3600
            self.last_update = now
        
        if hours_passed <= 0:
            return
        
        # Ogni interesse cambia leggermente
        for cat in self.interests["levels"]:
            # Drift casuale
            drift = random.uniform(-0.02, 0.02) * hours_passed
            self.interests["levels"][cat] = max(0.1, min(1.0, 
                self.interests["levels"][cat] + drift))
        
        # Ogni tanto emerge un nuovo interesse
        if random.random() < 0.01 * hours_passed:
            self._emerge_new_interest()
        
        self._save_data()
    
    def _emerge_new_interest(self):
        """Emergenza di un nuovo interesse"""
        # Trova categorie non ancora presenti
        existing = set(self.interests["levels"].keys())
        available = [c for c in self.INTEREST_CATEGORIES if c not in existing]
        
        if available:
            new = random.choice(available)
            self.interests["levels"][new] = random.uniform(0.3, 0.6)
            self.interests["history"].append({
                "timestamp": datetime.now().isoformat(),
                "interest": new,
                "action": "emerge"
            })
            logger.info(f"🌟 Nuovo interesse: {new}")
    
    def boost_interest(self, category: str, amount: float = 0.1):
        """
        Aumenta un interesse (es. dopo una conversazione).
        """
        if category in self.interests["levels"]:
            old = self.interests["levels"][category]
            self.interests["levels"][category] = min(1.0, old + amount)
        else:
            self.interests["levels"][category] = amount
        
        self.interests["history"].append({
            "timestamp": datetime.now().isoformat(),
            "interest": category,
            "action": "boost",
            "amount": amount
        })
        
        self._save_data()
    
    def get_current(self, n: int = 5) -> List[str]:
        """
        Restituisce i primi n interessi del momento.
        """
        self.update()  # aggiorna prima
        
        sorted_interests = sorted(
            self.interests["levels"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [cat for cat, _ in sorted_interests[:n]]
    
    def get_all_levels(self) -> Dict[str, float]:
        """Restituisce tutti i livelli"""
        self.update()
        return self.interests["levels"].copy()
    
    def get_interest_level(self, category: str) -> float:
        """Livello di un interesse specifico"""
        self.update()
        return self.interests["levels"].get(category, 0.0)
    
    def is_interested_in(self, topic: str) -> bool:
        """
        Verifica se AIVA è interessata a un topic.
        Usa similarità con le categorie esistenti.
        """
        # Per ora semplice: controlla se topic è in categorie
        topic_lower = topic.lower()
        
        for cat in self.interests["levels"]:
            if cat in topic_lower or topic_lower in cat:
                return self.interests["levels"][cat] > 0.5
        
        return False
    
    def get_interest_summary(self) -> str:
        """
        Riassunto degli interessi per il prompt.
        """
        top = self.get_current(3)
        
        if not top:
            return "non ho particolari interessi in questo momento"
        
        if len(top) == 1:
            return f"sono particolarmente interessata a {top[0]}"
        elif len(top) == 2:
            return f"mi piacciono {top[0]} e {top[1]}"
        else:
            return f"mi interessano {top[0]}, {top[1]} e {top[2]}"

# Istanza globale
interest_manager = InterestManager()
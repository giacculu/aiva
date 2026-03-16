"""
AIVA 2.0 – VALORE DELL'UTENTE
AIVA attribuisce un valore a ogni persona:
- Non solo economico
- Quanto è importante per lei
- Quanto le manca
- Quanto si fida
- Quanto è disposta a dare
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path
import math

class UserValueTracker:
    """
    Tiene traccia del valore di ogni utente per AIVA.
    Il valore è composto da:
    - Valore economico (supporto ricevuto)
    - Valore emotivo (come la fa sentire)
    - Valore relazionale (quanto interagiscono)
    - Valore di fiducia (quanto si fida)
    """
    
    # Pesi per le diverse componenti
    WEIGHTS = {
        "economic": 0.3,
        "emotional": 0.4,
        "relational": 0.2,
        "trust": 0.1
    }
    
    # Soglie per i livelli
    VALUE_THRESHOLDS = {
        "speciale": 0.9,
        "affezionato": 0.7,
        "amico": 0.5,
        "conoscente": 0.3,
        "nuovo": 0.1
    }
    
    def __init__(self, data_path: str = "data/user_value.json"):
        """
        Inizializza il tracker.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dati utenti
        self.users = self._load_data()
        
        # Cache
        self.cache = {}
        
        logger.info("💖 User Value Tracker inizializzato")
    
    def _load_data(self) -> Dict:
        """Carica dati utenti"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_data(self):
        """Salva dati utenti"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio user value: {e}")
    
    def _get_user(self, user_id: str) -> Dict:
        """Ottiene o inizializza dati utente"""
        if user_id not in self.users:
            self.users[user_id] = {
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "interaction_count": 0,
                "total_interaction_time": 0,
                "economic_value": 0.0,
                "emotional_value": 0.5,  # neutro iniziale
                "trust_level": 0.5,       # neutro iniziale
                "missed_count": 0,         # quante volte le è mancato
                "gifts_given": 0,          # regali ricevuti
                "special_moments": [],      # momenti speciali insieme
                "notes": []                 # note personali
            }
        return self.users[user_id]
    
    def update_from_interaction(self, user_id: str, interaction: Dict):
        """
        Aggiorna il valore in base a un'interazione.
        """
        user = self._get_user(user_id)
        
        # Aggiorna statistiche base
        user["last_seen"] = datetime.now().isoformat()
        user["interaction_count"] += 1
        
        # Durata interazione
        duration = interaction.get("duration", 1)
        user["total_interaction_time"] += duration
        
        # Valore emotivo (come l'ha fatta sentire)
        sentiment = interaction.get("sentiment", {})
        emotional_impact = sentiment.get("positivity", 0) * 2 - 1  # da -1 a 1
        
        # Media mobile
        user["emotional_value"] = user["emotional_value"] * 0.9 + emotional_impact * 0.1
        user["emotional_value"] = max(0, min(1, user["emotional_value"]))
        
        # Fiducia
        if interaction.get("was_positive", False):
            user["trust_level"] = min(1, user["trust_level"] + 0.05)
        elif interaction.get("was_negative", False):
            user["trust_level"] = max(0, user["trust_level"] - 0.1)
        
        # Momenti speciali
        if interaction.get("is_special", False):
            user["special_moments"].append({
                "timestamp": datetime.now().isoformat(),
                "description": interaction.get("description", "momento speciale")
            })
            if len(user["special_moments"]) > 10:
                user["special_moments"] = user["special_moments"][-10:]
        
        self._save_data()
    
    def update_economic_value(self, user_id: str, amount: float):
        """
        Aggiorna il valore economico in base a un pagamento.
        """
        user = self._get_user(user_id)
        
        # Il valore economico non è lineare
        # I primi soldi valgono di più
        old = user["economic_value"]
        
        # Funzione logaritmica: i primi 100€ contano molto, poi satura
        new = math.log(amount + 1) / 5  # normalizzato circa 0-1
        new = min(1, new)
        
        # Media mobile
        user["economic_value"] = user["economic_value"] * 0.7 + new * 0.3
        
        self._save_data()
    
    def update_missed(self, user_id: str):
        """
        Registra che AIVA ha sentito la mancanza di questo utente.
        """
        user = self._get_user(user_id)
        user["missed_count"] += 1
        
        # Più le manca, più valore emotivo
        user["emotional_value"] = min(1, user["emotional_value"] + 0.05)
        
        self._save_data()
    
    def add_gift(self, user_id: str, gift_type: str):
        """
        Registra un regalo fatto a questo utente (contenuto gratis).
        """
        user = self._get_user(user_id)
        user["gifts_given"] += 1
        
        # I regali aumentano il valore della relazione
        user["emotional_value"] = min(1, user["emotional_value"] + 0.1)
        
        self._save_data()
    
    def add_note(self, user_id: str, note: str):
        """
        Aggiunge una nota personale su un utente.
        """
        user = self._get_user(user_id)
        user["notes"].append({
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
        if len(user["notes"]) > 20:
            user["notes"] = user["notes"][-20:]
        
        self._save_data()
    
    def calculate_total_value(self, user_id: str) -> float:
        """
        Calcola il valore totale di un utente (0-1).
        """
        user = self._get_user(user_id)
        
        # Componenti
        economic = user["economic_value"]
        emotional = user["emotional_value"]
        
        # Relazionale: basato su frequenza e recency
        last_seen = datetime.fromisoformat(user["last_seen"])
        days_since = (datetime.now() - last_seen).days
        recency = math.exp(-days_since / 30)  # decadimento esponenziale
        
        interaction_freq = min(1, user["interaction_count"] / 100)
        relational = (recency + interaction_freq) / 2
        
        # Trust
        trust = user["trust_level"]
        
        # Bonus per momenti speciali
        special_bonus = min(0.2, len(user["special_moments"]) * 0.05)
        
        # Calcolo pesato
        total = (
            economic * self.WEIGHTS["economic"] +
            emotional * self.WEIGHTS["emotional"] +
            relational * self.WEIGHTS["relational"] +
            trust * self.WEIGHTS["trust"]
        ) + special_bonus
        
        return min(1, total)
    
    def get_level(self, user_id: str) -> str:
        """
        Restituisce il livello dell'utente basato sul valore.
        """
        value = self.calculate_total_value(user_id)
        
        for level, threshold in self.VALUE_THRESHOLDS.items():
            if value >= threshold:
                return level
        
        return "nuovo"
    
    def get_description(self, user_id: str) -> str:
        """
        Restituisce una descrizione personalizzata dell'utente.
        """
        value = self.calculate_total_value(user_id)
        level = self.get_level(user_id)
        user = self._get_user(user_id)
        
        if level == "speciale":
            base = "È una persona speciale per me"
        elif level == "affezionato":
            base = "Mi è molto caro/a"
        elif level == "amico":
            base = "È un amico/a"
        elif level == "conoscente":
            base = "Lo/la conosco abbastanza"
        else:
            base = "È una persona nuova"
        
        # Aggiungi dettagli
        details = []
        
        if user["gifts_given"] > 0:
            details.append(f"gli/le ho già fatto {user['gifts_given']} regali")
        
        if user["missed_count"] > 0:
            details.append(f"mi è mancato/a {user['missed_count']} volte")
        
        if user["special_moments"]:
            details.append(f"abbiamo condiviso {len(user['special_moments'])} momenti speciali")
        
        if details:
            return f"{base}, {', '.join(details)}"
        
        return base
    
    def should_give_free(self, user_id: str) -> bool:
        """
        Decide se regalare qualcosa gratis a questo utente.
        """
        value = self.calculate_total_value(user_id)
        
        # Più alto è il valore, più probabile
        probability = value * 0.3
        
        # Bonus per chi è mancato
        user = self._get_user(user_id)
        days_since = (datetime.now() - datetime.fromisoformat(user["last_seen"])).days
        if days_since > 7:
            probability += 0.2
        
        return np.random.random() < probability
    
    def get_value_summary(self, user_id: str) -> Dict:
        """
        Restituisce un riassunto del valore per questo utente.
        """
        value = self.calculate_total_value(user_id)
        level = self.get_level(user_id)
        user = self._get_user(user_id)
        
        return {
            "user_id": user_id,
            "total_value": value,
            "level": level,
            "economic_value": user["economic_value"],
            "emotional_value": user["emotional_value"],
            "trust_level": user["trust_level"],
            "interaction_count": user["interaction_count"],
            "missed_count": user["missed_count"],
            "gifts_given": user["gifts_given"],
            "special_moments_count": len(user["special_moments"]),
            "last_seen": user["last_seen"],
            "description": self.get_description(user_id)
        }
    
    def get_top_users(self, n: int = 10) -> List[Dict]:
        """
        Restituisce gli utenti con valore più alto.
        """
        users_with_value = []
        
        for user_id in self.users:
            value = self.calculate_total_value(user_id)
            users_with_value.append({
                "user_id": user_id,
                "value": value,
                "level": self.get_level(user_id)
            })
        
        users_with_value.sort(key=lambda x: x["value"], reverse=True)
        return users_with_value[:n]
    
    def get_statistics(self) -> Dict:
        """
        Statistiche globali.
        """
        levels = defaultdict(int)
        total_value = 0
        
        for user_id in self.users:
            level = self.get_level(user_id)
            levels[level] += 1
            total_value += self.calculate_total_value(user_id)
        
        return {
            "total_users": len(self.users),
            "levels": dict(levels),
            "average_value": total_value / len(self.users) if self.users else 0,
            "total_gifts": sum(u["gifts_given"] for u in self.users.values()),
            "total_missed": sum(u["missed_count"] for u in self.users.values())
        }

# Istanza globale
user_value_tracker = UserValueTracker()
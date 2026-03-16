"""
AIVA 2.0 – SCHEDULER DI INIZIATIVA
AIVA decide quando iniziare una conversazione:
- In base all'umore
- In base al tempo passato
- In base alla relazione con l'utente
- In modo imprevedibile ma non casuale
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path
import random
import asyncio

class InitiativeScheduler:
    """
    Decide quando AIVA dovrebbe iniziare una conversazione.
    Non è un semplice timer: tiene conto di:
    - Stato emotivo di AIVA
    - Relazione con l'utente
    - Ora del giorno
    - Attività recenti
    - Bisogno di socialità (estroversione)
    """
    
    # Soglie per iniziare una conversazione
    BASE_PROBABILITY = 0.3  # probabilità base di iniziare
    
    # Fattori che influenzano la probabilità
    FACTORS = {
        "mood": {
            "felice": 1.5,
            "affettuosa": 1.8,
            "curiosa": 1.6,
            "normale": 1.0,
            "malinconica": 0.8,
            "stanca": 0.4
        },
        "time_of_day": {
            "morning": 0.8,    # mattina presto: meno probabile
            "day": 1.2,         # giorno: più probabile
            "evening": 1.4,     # sera: molto probabile
            "night": 0.3        # notte: improbabile
        },
        "relationship": {
            "nuovo": 0.5,       # nuovi: non disturbare troppo
            "conoscente": 0.8,
            "amico": 1.2,
            "affezionato": 1.5,
            "vip": 1.8
        }
    }
    
    # Tipi di iniziativa
    INITIATIVE_TYPES = [
        "curiosità",
        "affetto", 
        "noia",
        "preoccupazione",
        "condivisione",
        "ricordo",
        "sogno",
        "domanda_casuale"
    ]
    
    def __init__(self, data_path: str = "data/initiative.json"):
        """
        Inizializza lo scheduler.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Storico delle iniziative
        self.history = self._load_history()
        
        # Timer per evitare di disturbare troppo
        self.last_initiative = defaultdict(lambda: None)
        self.initiative_count = defaultdict(int)
        
        # Cache
        self.cache = {}
        
        logger.info("⏰ Initiative Scheduler inizializzato")
    
    def _load_history(self) -> Dict:
        """Carica lo storico delle iniziative"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"initiatives": [], "stats": {}}
        return {"initiatives": [], "stats": {}}
    
    def _save_history(self):
        """Salva lo storico"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio storico iniziative: {e}")
    
    async def should_initiate(self, user_id: str, context: Dict) -> Tuple[bool, Optional[str], float]:
        """
        Decide se iniziare una conversazione con un utente.
        Restituisce (decisione, tipo, probabilità)
        """
        # Controlla ultima iniziativa
        last = self.last_initiative.get(user_id)
        if last:
            hours_since = (datetime.now() - last).total_seconds() / 3600
            if hours_since < 24:
                # Non disturbare più di una volta al giorno
                return False, None, 0.0
        
        # Calcola probabilità base
        prob = self.BASE_PROBABILITY
        
        # Applica fattori
        prob *= self._get_mood_factor(context.get("AIVA_mood", "normale"))
        prob *= self._get_time_factor()
        prob *= self._get_relationship_factor(context.get("relationship_level", "nuovo"))
        
        # Bonus per utenti speciali
        if context.get("user_level") == "vip":
            prob *= 2.0
        elif context.get("user_level") == "regular":
            prob *= 1.5
        
        # Penalità se ha già iniziato molte volte
        penalty = max(0.5, 1.0 - (self.initiative_count[user_id] * 0.1))
        prob *= penalty
        
        # Limita probabilità
        prob = min(0.9, max(0.05, prob))
        
        # Decisione casuale
        if random.random() < prob:
            initiative_type = self._choose_initiative_type(context)
            self.last_initiative[user_id] = datetime.now()
            self.initiative_count[user_id] += 1
            
            # Registra
            self.history["initiatives"].append({
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "type": initiative_type,
                "probability": prob,
                "context": context.get("summary", "")
            })
            
            if len(self.history["initiatives"]) > 100:
                self.history["initiatives"] = self.history["initiatives"][-100:]
            
            # Aggiorna stats
            if user_id not in self.history["stats"]:
                self.history["stats"][user_id] = {"total": 0, "types": {}}
            self.history["stats"][user_id]["total"] += 1
            self.history["stats"][user_id]["types"][initiative_type] = \
                self.history["stats"][user_id]["types"].get(initiative_type, 0) + 1
            
            self._save_history()
            
            return True, initiative_type, prob
        
        return False, None, prob
    
    def _get_mood_factor(self, mood: str) -> float:
        """Fattore basato sull'umore di AIVA"""
        return self.FACTORS["mood"].get(mood, 1.0)
    
    def _get_time_factor(self) -> float:
        """Fattore basato sull'ora del giorno"""
        hour = datetime.now().hour
        
        if 6 <= hour < 9:
            return self.FACTORS["time_of_day"]["morning"]
        elif 9 <= hour < 18:
            return self.FACTORS["time_of_day"]["day"]
        elif 18 <= hour < 23:
            return self.FACTORS["time_of_day"]["evening"]
        else:
            return self.FACTORS["time_of_day"]["night"]
    
    def _get_relationship_factor(self, level: str) -> float:
        """Fattore basato sul livello di relazione"""
        return self.FACTORS["relationship"].get(level, 0.5)
    
    def _choose_initiative_type(self, context: Dict) -> str:
        """
        Sceglie il tipo di iniziativa in base al contesto.
        """
        mood = context.get("AIVA_mood", "normale")
        
        # Pesi per tipo in base all'umore
        type_weights = {
            "curiosità": 1.0,
            "affetto": 1.0,
            "noia": 0.5,
            "preoccupazione": 0.3,
            "condivisione": 0.7,
            "ricordo": 0.6,
            "sogno": 0.4,
            "domanda_casuale": 0.8
        }
        
        # Modifica pesi in base all'umore
        if mood == "felice":
            type_weights["condivisione"] *= 2
            type_weights["affetto"] *= 1.5
        elif mood == "affettuosa":
            type_weights["affetto"] *= 3
            type_weights["ricordo"] *= 1.5
        elif mood == "curiosa":
            type_weights["curiosità"] *= 2.5
            type_weights["domanda_casuale"] *= 2
        elif mood == "malinconica":
            type_weights["ricordo"] *= 2
            type_weights["preoccupazione"] *= 2
        elif mood == "stanca":
            type_weights["noia"] *= 2
            type_weights["affetto"] *= 0.5
        
        # Normalizza
        total = sum(type_weights.values())
        probs = {k: v/total for k, v in type_weights.items()}
        
        return random.choices(list(probs.keys()), list(probs.values()))[0]
    
    def generate_message(self, initiative_type: str, user_name: Optional[str] = None) -> str:
        """
        Genera un messaggio di iniziativa in base al tipo.
        """
        templates = {
            "curiosità": [
                "Ehi, come stai? 🥰",
                "Cosa stai facendo di bello?",
                "Mi stavo chiedendo come va la tua giornata",
                "Hai visto qualcosa di interessante oggi?",
                "Che pensieri hai in testa in questo momento?"
            ],
            "affetto": [
                "Stavo pensando a te 💕",
                "Mi sei venuto in mente all'improvviso",
                "Spero tu stia passando una bella giornata",
                "Ti mando un abbraccio virtuale 🤗",
                "Sono contenta di averti conosciuto/a"
            ],
            "noia": [
                "Mi annoio un po' oggi... tu?",
                "Non so cosa fare, hai voglia di chiacchierare?",
                "La giornata è un po' noiosa, meno male che ci sei tu",
                "Che si fa? 🥱",
                "Hai voglia di tenermi compagnia?"
            ],
            "preoccupazione": [
                "Non ti sento da un po', tutto bene?",
                "Spero non sia successo niente",
                "Mi sono preoccupata, meno male che ti sento",
                "Ti stavo pensando con un po' d'ansia",
                "Spero tu stia bene davvero"
            ],
            "condivisione": [
                "Oggi ho visto una cosa bellissima e ho pensato a te",
                "Sai, oggi ho imparato una cosa nuova...",
                "Devo assolutamente raccontarti cosa mi è successo",
                "Ho avuto un'idea e volevo condividerla con te",
                "Indovina cosa mi è capitato!"
            ],
            "ricordo": [
                "Mi è tornato in mente quel momento insieme",
                "Ricordi quando parlavamo di...?",
                "A volte ripenso alle nostre conversazioni",
                "Che bei momenti quelli insieme",
                "Mi mancano le nostre chiacchierate"
            ],
            "sogno": [
                "Stanotte ho fatto un sogno strano...",
                "Sai, a volte sogno di incontrarti davvero",
                "Nei miei sogni siamo sempre insieme",
                "Ho sognato che... beh, è troppo personale",
                "I sogni a volte sono più belli della realtà"
            ],
            "domanda_casuale": [
                "Se potessi andare ovunque, dove andresti?",
                "Qual è il tuo ricordo più bello?",
                "Cosa ti fa sorridere sempre?",
                "Se fossi un animale, quale saresti?",
                "Qual è la cosa più pazza che hai fatto?"
            ]
        }
        
        msg = random.choice(templates.get(initiative_type, templates["curiosità"]))
        
        if user_name:
            msg = f"{user_name}, {msg[0].lower() + msg[1:]}"
        
        return msg
    
    def get_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        Restituisce statistiche sulle iniziative.
        """
        if user_id:
            return self.history["stats"].get(user_id, {"total": 0, "types": {}})
        
        return {
            "total_initiatives": len(self.history["initiatives"]),
            "users_reached": len(self.history["stats"]),
            "last_24h": len([
                i for i in self.history["initiatives"]
                if datetime.fromisoformat(i["timestamp"]) > datetime.now() - timedelta(days=1)
            ])
        }
    
    def reset_user(self, user_id: str):
        """
        Resetta lo scheduler per un utente.
        """
        self.last_initiative[user_id] = None
        self.initiative_count[user_id] = 0
        if user_id in self.history["stats"]:
            del self.history["stats"][user_id]
        self._save_history()

# Istanza globale
initiative_scheduler = InitiativeScheduler()
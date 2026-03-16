"""
AIVA 2.0 – MEMORIA EMOTIVA
AIVA ricorda come l'hanno fatta sentire gli eventi.
Non solo cosa è successo, ma l'emozione associata.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path

class EmotionalMemory:
    """
    Memoria associata alle emozioni.
    Ogni ricordo ha un'etichetta emotiva (vettore PAD).
    """
    
    def __init__(self, data_path: str = "data/emotional_memory.json"):
        """
        Inizializza la memoria emotiva.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.memories = self._load_data()
        
        logger.info("💭 Emotional Memory inizializzata")
    
    def _load_data(self) -> Dict:
        """Carica memorie emotive"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"by_user": {}, "global": []}
        return {"by_user": {}, "global": []}
    
    def _save_data(self):
        """Salva memorie emotive"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio memoria emotiva: {e}")
    
    def store(self, user_id: str, event: str, emotion_vector: List[float], 
             intensity: float = 1.0, metadata: Optional[Dict] = None):
        """
        Memorizza un evento con la sua carica emotiva.
        """
        timestamp = datetime.now()
        
        memory = {
            "timestamp": timestamp.isoformat(),
            "event": event[:200],
            "emotion": {
                "P": emotion_vector[0],
                "A": emotion_vector[1],
                "D": emotion_vector[2]
            },
            "intensity": intensity,
            "metadata": metadata or {}
        }
        
        # Per utente
        if user_id not in self.memories["by_user"]:
            self.memories["by_user"][user_id] = []
        
        self.memories["by_user"][user_id].append(memory)
        
        # Mantieni ultime 50 per utente
        if len(self.memories["by_user"][user_id]) > 50:
            self.memories["by_user"][user_id] = self.memories["by_user"][user_id][-50:]
        
        # Anche in globale
        memory_with_user = memory.copy()
        memory_with_user["user_id"] = user_id
        self.memories["global"].append(memory_with_user)
        
        if len(self.memories["global"]) > 500:
            self.memories["global"] = self.memories["global"][-500:]
        
        self._save_data()
    
    def get_recent_emotions(self, user_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """
        Recupera emozioni recenti (per utente o globali).
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        if user_id:
            memories = self.memories["by_user"].get(user_id, [])
        else:
            memories = self.memories["global"]
        
        recent = []
        for m in memories:
            m_time = datetime.fromisoformat(m["timestamp"])
            if m_time > cutoff:
                recent.append(m)
        
        return recent
    
    def get_emotional_trend(self, user_id: Optional[str] = None, days: int = 30) -> Dict:
        """
        Analizza il trend emotivo.
        """
        recent = self.get_recent_emotions(user_id, days)
        
        if not recent:
            return {"trend": "stabile", "average": [0, 0, 0]}
        
        # Calcola media
        avg_p = np.mean([m["emotion"]["P"] for m in recent])
        avg_a = np.mean([m["emotion"]["A"] for m in recent])
        avg_d = np.mean([m["emotion"]["D"] for m in recent])
        
        # Calcola trend (prima metà vs seconda)
        half = len(recent) // 2
        if half > 0:
            first_half = recent[:half]
            second_half = recent[half:]
            
            first_p = np.mean([m["emotion"]["P"] for m in first_half])
            second_p = np.mean([m["emotion"]["P"] for m in second_half])
            
            if second_p > first_p + 0.2:
                trend = "migliorando"
            elif second_p < first_p - 0.2:
                trend = "peggiorando"
            else:
                trend = "stabile"
        else:
            trend = "stabile"
        
        return {
            "trend": trend,
            "average": [avg_p, avg_a, avg_d],
            "count": len(recent)
        }
    
    def get_emotional_summary(self, user_id: str) -> str:
        """
        Genera un riassunto emotivo per un utente.
        """
        recent = self.get_recent_emotions(user_id, 7)
        
        if not recent:
            return "Non abbiamo ancora una storia emotiva significativa"
        
        avg_p = np.mean([m["emotion"]["P"] for m in recent])
        
        if avg_p > 0.6:
            return "Di solito quando parliamo mi sento felice"
        elif avg_p > 0.3:
            return "Le nostre conversazioni mi fanno stare bene"
        elif avg_p > -0.3:
            return "Con te mi sento a mio agio"
        elif avg_p > -0.6:
            return "A volte le nostre conversazioni mi lasciano pensierosa"
        else:
            return "Con te provo emozioni contrastanti"
    
    def get_recent_summary(self) -> Dict:
        """
        Riassunto della memoria emotiva recente (globale).
        """
        recent = self.get_recent_emotions(days=7)
        
        if not recent:
            return {"mood": "neutro", "intensity": 0}
        
        avg_p = np.mean([m["emotion"]["P"] for m in recent])
        
        if avg_p > 0.5:
            mood = "positivo"
        elif avg_p > 0:
            mood = "leggermente positivo"
        elif avg_p > -0.5:
            mood = "neutro"
        else:
            mood = "negativo"
        
        return {
            "mood": mood,
            "intensity": np.mean([m["intensity"] for m in recent]),
            "count": len(recent)
        }

# Istanza globale
emotional_memory = EmotionalMemory()
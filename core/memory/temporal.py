"""
AIVA 2.0 – PESI TEMPORALI PER LA MEMORIA
I ricordi più recenti pesano di più.
Gestisce il decadimento temporale delle memorie.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from loguru import logger
import math

class TemporalWeighting:
    """
    Assegna pesi temporali ai ricordi.
    I ricordi più recenti hanno peso maggiore.
    """
    
    # Parametri di decadimento
    DECAY_RATE = 0.1  # per giorno
    HALF_LIFE = 7  # giorni per dimezzare il peso
    
    def __init__(self):
        logger.info("⏳ Temporal Weighting inizializzato")
    
    def get_weight(self, timestamp: datetime, reference: Optional[datetime] = None) -> float:
        """
        Calcola il peso di un ricordo in base al tempo.
        Usa decadimento esponenziale.
        """
        if reference is None:
            reference = datetime.now()
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Giorni trascorsi
        days = (reference - timestamp).total_seconds() / 86400
        
        if days < 0:
            return 1.0  # futuro (non dovrebbe accadere)
        
        # Decadimento esponenziale: weight = e^(-decay * days)
        weight = math.exp(-self.DECAY_RATE * days)
        
        return weight
    
    def get_weights_batch(self, timestamps: List[datetime], reference: Optional[datetime] = None) -> List[float]:
        """
        Calcola pesi per una lista di timestamp.
        """
        return [self.get_weight(ts, reference) for ts in timestamps]
    
    def apply_temporal_weight(self, memories: List[Dict], 
                              time_field: str = "timestamp",
                              weight_field: str = "temporal_weight") -> List[Dict]:
        """
        Aggiunge un campo con peso temporale a ogni memoria.
        """
        reference = datetime.now()
        
        for memory in memories:
            ts = memory.get(time_field)
            if ts:
                weight = self.get_weight(ts, reference)
                memory[weight_field] = weight
            else:
                memory[weight_field] = 0.5
        
        return memories
    
    def sort_by_temporal(self, memories: List[Dict], 
                         time_field: str = "timestamp",
                         reverse: bool = True) -> List[Dict]:
        """
        Ordina le memorie per tempo (default: più recenti prima).
        """
        return sorted(memories, 
                     key=lambda x: x.get(time_field, ""),
                     reverse=reverse)
    
    def filter_recent(self, memories: List[Dict], days: int = 30,
                     time_field: str = "timestamp") -> List[Dict]:
        """
        Filtra solo memorie recenti.
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = []
        for m in memories:
            ts = m.get(time_field)
            if ts:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if ts > cutoff:
                    filtered.append(m)
        
        return filtered
    
    def get_recency_factor(self, last_interaction: Optional[datetime]) -> float:
        """
        Calcola un fattore di recency per un utente.
        Utile per iniziativa e valore.
        """
        if not last_interaction:
            return 0.0
        
        if isinstance(last_interaction, str):
            last_interaction = datetime.fromisoformat(last_interaction)
        
        days = (datetime.now() - last_interaction).total_seconds() / 86400
        
        # Più recente = più alto
        return math.exp(-days / 7)  # decadimento su 7 giorni
    
    def get_temporal_context(self, memories: List[Dict]) -> str:
        """
        Genera una descrizione temporale del contesto.
        """
        if not memories:
            return "nessuna memoria recente"
        
        # Trova il più recente
        newest = max(memories, key=lambda x: x.get("timestamp", ""))
        newest_time = newest.get("timestamp")
        
        if isinstance(newest_time, str):
            newest_time = datetime.fromisoformat(newest_time)
        
        days = (datetime.now() - newest_time).total_seconds() / 86400
        
        if days < 1:
            return "qualche ora fa"
        elif days < 2:
            return "ieri"
        elif days < 7:
            return f"{int(days)} giorni fa"
        elif days < 30:
            return f"{int(days/7)} settimane fa"
        else:
            return f"{int(days/30)} mesi fa"

# Istanza globale
temporal_weighting = TemporalWeighting()
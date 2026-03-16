"""
Memoria temporale: gestisce il decadimento e il peso dei ricordi nel tempo
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import math

class TemporalMemory:
    """
    Gestisce gli aspetti temporali della memoria:
    - Decadimento naturale dei ricordi
    - Pesi basati su recenza e importanza
    - Consolidamento di ricordi importanti
    """
    
    def __init__(self, episodic_memory, semantic_memory):
        self.episodic = episodic_memory
        self.semantic = semantic_memory
        self.decay_rate = 0.1  # Quanto velocemente decadono i ricordi non usati
        logger.debug("⏳ Memoria temporale inizializzata")
    
    # ========== CALCOLO PESI ==========
    
    def calculate_weight(self, 
                        base_importance: float,
                        timestamp: datetime,
                        last_recall: Optional[datetime] = None,
                        recall_count: int = 0) -> float:
        """
        Calcola il peso attuale di un ricordo.
        
        Formula: weight = importance * (recall_bonus) * decay_factor
        
        Args:
            base_importance: Importanza originale (0-1)
            timestamp: Quando è stato creato
            last_recall: Ultima volta che è stato ricordato
            recall_count: Quante volte è stato ricordato
        
        Returns:
            Peso attuale (0-1)
        """
        now = datetime.now()
        
        # Decadimento temporale
        age_hours = (now - timestamp).total_seconds() / 3600
        decay = math.exp(-self.decay_rate * age_hours / 24)  # decadimento giornaliero
        
        # Bonus per ricordi richiamati spesso
        recall_bonus = 1.0 + (0.1 * recall_count)
        
        # Bonus per recenza dell'ultimo richiamo
        if last_recall:
            hours_since_recall = (now - last_recall).total_seconds() / 3600
            recency_bonus = math.exp(-0.05 * hours_since_recall)
        else:
            recency_bonus = 1.0
        
        # Peso finale
        weight = base_importance * decay * recall_bonus * recency_bonus
        return min(1.0, weight)  # Cap a 1.0
    
    # ========== DECADIMENTO PROGRAMMATO ==========
    
    async def apply_decay(self, user_id: Optional[str] = None) -> int:
        """
        Applica decadimento a tutti i ricordi (o di un utente).
        Da chiamare periodicamente (es. ogni ora).
        
        Returns:
            Numero di ricordi che sono scesi sotto soglia
        """
        # Recupera ricordi
        if user_id:
            memories = self.episodic.vc.get_memories_by_user(user_id)
        else:
            # Nota: in produzione, avremmo bisogno di un metodo per tutti gli utenti
            # Per ora, implementiamo solo per utente specifico
            return 0
        
        forgotten = 0
        for mem in memories:
            metadata = mem['metadata']
            timestamp = datetime.fromisoformat(metadata.get('timestamp', datetime.now().isoformat()))
            importance = metadata.get('importance', 0.5)
            
            # Calcola peso attuale
            weight = self.calculate_weight(importance, timestamp)
            
            # Se sotto soglia, dimentica
            if weight < 0.2:
                self.episodic.vc.delete_memory(mem['id'])
                forgotten += 1
                logger.debug(f"🗑️ Ricordo dimenticato per basso peso: {mem['id']}")
            else:
                # Aggiorna importanza nel metadata
                # Nota: ChromaDB non supporta update parziale facilmente
                pass
        
        if forgotten > 0:
            logger.info(f"⏳ Decadimento applicato: {forgotten} ricordi dimenticati")
        
        return forgotten
    
    # ========== CONSOLIDAMENTO ==========
    
    async def consolidate(self, user_id: str, memory_id: str) -> None:
        """
        Consolida un ricordo importante (previene decadimento).
        """
        # Implementazione: potrebbe salvare il ricordo in una tabella separata
        # o marcare come 'consolidato' nei metadata
        pass
    
    def should_consolidate(self, memory: Dict) -> bool:
        """
        Determina se un ricordo merita consolidamento.
        """
        metadata = memory.get('metadata', {})
        importance = metadata.get('importance', 0)
        recall_count = metadata.get('recall_count', 0)
        
        # Soglie per consolidamento
        return importance > 0.8 or recall_count > 5
    
    # ========== MANUTENZIONE ==========
    
    async def daily_maintenance(self) -> Dict[str, int]:
        """
        Operazioni di manutenzione quotidiana.
        """
        stats = {
            'forgotten': 0,
            'consolidated': 0
        }
        
        # Applica decadimento globale (simulato)
        # In produzione, itereremmo su tutti gli utenti
        # stats['forgotten'] = await self.apply_decay()
        
        return stats
    
    # ========== UTILITY PER PROMPT ==========
    
    def get_time_context(self, user_id: str) -> str:
        """
        Genera contesto temporale per il prompt.
        """
        from datetime import datetime
        
        now = datetime.now()
        hour = now.hour
        
        if hour < 6:
            time_desc = "notte fonda"
        elif hour < 12:
            time_desc = "mattina"
        elif hour < 14:
            time_desc = "mezzogiorno"
        elif hour < 18:
            time_desc = "pomeriggio"
        elif hour < 22:
            time_desc = "sera"
        else:
            time_desc = "notte"
        
        return f"Momento della giornata: {time_desc}"
    
    def get_recency_bias(self, user_id: str) -> float:
        """
        Restituisce un bias per favorire ricordi recenti.
        Usato nel retrieval.
        """
        # In produzione, potrebbe essere un parametro configurabile
        return 0.7  # 70% peso a recenza
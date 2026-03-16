"""
Memoria episodica: ricordi di eventi specifici con contesto emotivo
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from database.vector.chroma_client import ChromaMemoryClient

class EpisodicMemory:
    """
    Gestisce i ricordi episodici (eventi specifici) usando vettori.
    Ogni ricordo è associato a un'emozione e ha un peso temporale.
    """
    
    # Tipi di memoria episodica
    MEMORY_TYPES = [
        'conversation',      # Una conversazione significativa
        'event',             # Un evento specifico
        'emotion',           # Un momento emotivamente intenso
        'milestone',         # Un traguardo nella relazione
        'conflict',          # Un disaccordo o litigio
        'reconciliation',    # Una pace fatta
        'gift',              # Un regalo ricevuto
        'support'            # Un momento di supporto
    ]
    
    def __init__(self, vector_client: ChromaMemoryClient):
        self.vc = vector_client
        logger.debug("🧠 Memoria episodica inizializzata")
    
    # ========== CREAZIONE RICORDI ==========
    
    def remember_conversation(self, 
                             user_id: str,
                             summary: str,
                             emotional_valence: float = 0.0,
                             importance: float = 0.5,
                             conversation_id: Optional[int] = None) -> str:
        """
        Ricorda una conversazione significativa.
        
        Args:
            user_id: ID utente
            summary: Riassunto della conversazione
            emotional_valence: Valenza emotiva (-1 triste, 0 neutro, +1 felice)
            importance: Importanza (0-1)
            conversation_id: ID della conversazione nel DB SQL (opzionale)
        
        Returns:
            ID del ricordo
        """
        metadata = {
            'conversation_id': conversation_id
        }
        
        return self.vc.add_memory(
            text=summary,
            user_id=user_id,
            memory_type='conversation',
            emotional_valence=emotional_valence,
            importance=importance,
            metadata=metadata
        )
    
    def remember_event(self,
                      user_id: str,
                      description: str,
                      event_type: str,
                      emotional_valence: float = 0.0,
                      importance: float = 0.5,
                      metadata: Optional[Dict] = None) -> str:
        """
        Ricorda un evento specifico.
        
        Args:
            user_id: ID utente
            description: Descrizione dell'evento
            event_type: Tipo di evento (es. 'first_meeting', 'birthday')
            emotional_valence: Valenza emotiva
            importance: Importanza
            metadata: Metadati aggiuntivi
        """
        meta = metadata or {}
        meta['event_type'] = event_type
        
        return self.vc.add_memory(
            text=description,
            user_id=user_id,
            memory_type='event',
            emotional_valence=emotional_valence,
            importance=importance,
            metadata=meta
        )
    
    # ========== RECUPERO RICORDI ==========
    
    def recall_similar(self, 
                      query: str,
                      user_id: Optional[str] = None,
                      memory_type: Optional[str] = None,
                      n_results: int = 5) -> List[Dict]:
        """
        Recupera ricordi simili a una query.
        """
        return self.vc.search_memories(
            query=query,
            user_id=user_id,
            memory_type=memory_type,
            n_results=n_results
        )
    
    def recall_by_emotion(self,
                         user_id: str,
                         target_emotion: str,
                         n_results: int = 5) -> List[Dict]:
        """
        Recupera ricordi associati a una specifica emozione.
        Nota: implementazione semplificata, cerchiamo per testo.
        """
        # Cerchiamo per parole chiave dell'emozione
        emotion_keywords = {
            'felice': ['felice', 'contento', 'gioia', 'riso', 'bello'],
            'triste': ['triste', 'dispiaciuto', 'pianto', 'dolore'],
            'arrabbiato': ['arrabbiato', 'rabbia', 'litigio', 'discussione'],
            'sorpreso': ['sorpresa', 'inaspettato', 'wow'],
            'grato': ['grazie', 'grato', 'ringraziamento', 'gentile']
        }
        
        keywords = emotion_keywords.get(target_emotion.lower(), [target_emotion])
        query = ' '.join(keywords)
        
        return self.recall_similar(query, user_id, n_results=n_results)
    
    def recall_recent(self, user_id: str, hours: int = 24) -> List[Dict]:
        """
        Recupera ricordi recenti.
        """
        return self.vc.get_recent_memories(user_id, hours)
    
    def recall_important(self, user_id: str, min_importance: float = 0.7, limit: int = 10) -> List[Dict]:
        """
        Recupera ricordi importanti (sopra una soglia).
        """
        # Implementazione semplificata: cerchiamo con query vuota e filtriamo
        # Nota: in produzione si può usare il filtro metadati di ChromaDB
        memories = self.vc.get_memories_by_user(user_id, limit=50)
        important = [m for m in memories 
                    if m['metadata'].get('importance', 0) >= min_importance]
        return important[:limit]
    
    # ========== MANUTENZIONE RICORDI ==========
    
    def reinforce_memory(self, memory_id: str) -> None:
        """
        Rafforza un ricordo (aumenta importanza).
        """
        # Recupera metadata attuale (non direttamente supportato, servirebbe get)
        # Implementazione alternativa: update con importance + 0.1
        # Per ora, non implementato
        pass
    
    def weaken_memory(self, memory_id: str) -> None:
        """
        Indebolisce un ricordo (diminuisce importanza).
        """
        pass
    
    def forget_old_memories(self, user_id: str, days: int = 90) -> int:
        """
        Dimentica ricordi molto vecchi e poco importanti.
        Da chiamare periodicamente per manutenzione.
        """
        # Nota: richiederebbe get con filtro data, non implementato in ChromaDB base
        # Restituiamo 0 come placeholder
        return 0
    
    # ========== CONTESTO PER PROMPT ==========
    
    def get_relevant_context(self, 
                            user_id: str,
                            current_message: str,
                            max_memories: int = 3) -> str:
        """
        Genera un testo di contesto da includere nel prompt.
        Combina ricordi episodici rilevanti.
        """
        # Cerca ricordi simili al messaggio attuale
        similar = self.recall_similar(current_message, user_id, n_results=max_memories)
        
        if not similar:
            return ""
        
        # Costruisci testo contestuale
        context = "\n📝 **Ricordi episodici rilevanti:**\n"
        
        for mem in similar:
            timestamp = mem['metadata'].get('timestamp', '')
            importance = mem['metadata'].get('importance', 0.5)
            emotion = mem['metadata'].get('emotional_valence', 0)
            
            # Simbolo emozione
            if emotion > 0.3:
                emotion_symbol = "😊"
            elif emotion < -0.3:
                emotion_symbol = "😔"
            else:
                emotion_symbol = "😐"
            
            context += f"- {emotion_symbol} {mem['text']}\n"
        
        return context
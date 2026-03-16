"""
Memory Layer di AIVA
Come ricorda esperienze, fatti, emozioni
"""
from .episodic import EpisodicMemory, episodic_memory
from .semantic import SemanticMemory, semantic_memory
from .emotional import EmotionalMemory, emotional_memory
from .temporal import TemporalWeights, temporal_weights

class Memory:
    """
    Integra tutti i tipi di memoria
    """
    
    def __init__(self):
        self.episodic = episodic_memory
        self.semantic = semantic_memory
        self.emotional = emotional_memory
        self.temporal = temporal_weights
        
    def remember_everything(self, user_id: str, limit_episodic: int = 10) -> Dict:
        """
        Recupera tutto ciò che sa su un utente, da tutte le memorie
        """
        # Fatti semantici
        facts = self.semantic.get_user_summary(user_id)
        
        # Ricordi episodici recenti
        episodes = self.episodic.get_memories_by_user(user_id, limit=limit_episodic)
        
        # Riassunto emotivo
        emotional = self.emotional.get_emotional_summary(user_id)
        
        # Applica pesi temporali agli episodi
        for ep in episodes:
            if 'metadata' in ep and 'timestamp' in ep['metadata']:
                ts = datetime.fromisoformat(ep['metadata']['timestamp'])
                importance = ep['metadata'].get('importance', 0.5)
                ep['temporal_weight'] = self.temporal.calculate_weight(ts, importance)
        
        # Ordina episodi per rilevanza temporale
        episodes = self.temporal.sort_by_temporal_relevance(episodes)
        
        return {
            'facts': facts,
            'episodes': episodes,
            'emotional': emotional
        }
    
    def remember_conversation(self, user_id: str, n_last: int = 10) -> str:
        """
        Formatta i ricordi per il prompt
        """
        everything = self.remember_everything(user_id, limit_episodic=n_last)
        
        parts = []
        
        # Fatti su di lui/lei
        facts_text = self.semantic.get_facts_for_prompt(user_id)
        if facts_text:
            parts.append(facts_text)
        
        # Come mi fa sentire
        feeling = self.emotional.how_does_user_make_me_feel(user_id)
        parts.append(f"Con te: {feeling}")
        
        # Ultimi ricordi episodici
        if everything['episodes']:
            parts.append("\nRicordi recenti:")
            for ep in everything['episodes'][:3]:  # Solo ultimi 3
                desc = ep['description'][:100]
                emotion = ep['metadata'].get('primary_emotion', 'neutro')
                parts.append(f"• {desc} ({emotion})")
        
        return "\n".join(parts)
    
    def learn_from_interaction(self, 
                              user_id: str,
                              user_message: str,
                              ai_response: str,
                              emotional_state: Dict,
                              importance: float = 0.5):
        """
        Impara da un'interazione, aggiornando tutte le memorie
        """
        # 1. Estrai fatti semantici (già fatto altrove, qui solo salvataggio)
        
        # 2. Crea ricordo episodico
        event_desc = f"Utente: {user_message[:50]}... → Io: {ai_response[:50]}..."
        
        self.episodic.add_memory(
            user_id=user_id,
            event_description=event_desc,
            emotional_state=emotional_state,
            importance=importance,
            metadata={
                'user_message_preview': user_message[:100],
                'ai_response_preview': ai_response[:100]
            }
        )
        
        # 3. Registra impatto emotivo
        self.emotional.record_interaction(
            user_id=user_id,
            emotional_state=emotional_state,
            event_description=event_desc,
            intensity=importance
        )
        
        # 4. Aggiorna metriche di relazione
        pleasure = emotional_state.get('pleasure', 0)
        self.semantic.update_relationship_metric(
            user_id=user_id,
            metric='avg_pleasure',
            value=pleasure
        )
    
    def get_memory_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        Statistiche sulla memoria
        """
        stats = {
            'episodic': self.episodic.get_memory_stats(user_id),
            'emotional': {
                'users_tracked': len(self.emotional.user_emotional_summary)
            }
        }
        
        if user_id:
            emotional_summary = self.emotional.get_emotional_summary(user_id)
            stats['emotional']['for_user'] = {
                'interaction_count': emotional_summary['interaction_count'],
                'dominant_emotion': self.emotional.get_dominant_emotion(user_id)
            }
        
        return stats

# Istanza globale
memory = Memory()
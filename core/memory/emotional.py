"""
Memoria emotiva: traccia come gli eventi hanno fatto sentire AIVA
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json

class EmotionalMemory:
    """
    Traccia le emozioni associate a utenti ed eventi.
    Non solo cosa è successo, ma come AIVA si è sentita.
    """
    
    def __init__(self, db_sqlite, vector_client):
        """
        Usa sia SQLite (per dati strutturati) che ChromaDB (per contesto).
        """
        self.db = db_sqlite
        self.vc = vector_client
        self.emotional_state = {
            'pleasure': 0.0,    # -1 a +1
            'arousal': 0.0,     # -1 a +1
            'dominance': 0.0    # -1 a +1
        }
        logger.debug("❤️ Memoria emotiva inizializzata")
    
    # ========== REGISTRAZIONE EMOZIONI ==========
    
    def record_emotional_response(self,
                                 user_id: str,
                                 event_description: str,
                                 pleasure: float,
                                 arousal: float,
                                 dominance: float,
                                 importance: float = 0.5) -> str:
        """
        Registra come AIVA si è sentita durante un evento.
        
        Args:
            user_id: Utente coinvolto
            event_description: Descrizione dell'evento
            pleasure: Piacere (-1 a +1)
            arousal: Attivazione (-1 a +1)
            dominance: Dominanza (-1 a +1)
            importance: Importanza dell'evento
        
        Returns:
            ID del ricordo emotivo
        """
        # Costruisci testo emotivo
        emotional_text = f"Mi sono sentita: {self._describe_emotion(pleasure, arousal, dominance)}. {event_description}"
        
        # Salva in memoria vettoriale
        memory_id = self.vc.add_memory(
            text=emotional_text,
            user_id=user_id,
            memory_type='emotion',
            emotional_valence=pleasure,
            importance=importance,
            metadata={
                'pleasure': pleasure,
                'arousal': arousal,
                'dominance': dominance
            }
        )
        
        logger.debug(f"❤️ Reazione emotiva registrata per {user_id}: {self._describe_emotion(pleasure, arousal, dominance)}")
        return memory_id
    
    def record_interaction_emotion(self,
                                  user_id: str,
                                  message: str,
                                  response: str) -> None:
        """
        Analizza e registra l'emozione provata durante un'interazione.
        Da chiamare dopo ogni scambio.
        """
        # Analisi semplificata: in produzione usare un modello di sentiment
        pleasure = self._analyze_pleasure(message, response)
        arousal = self._analyze_arousal(message)
        dominance = self._analyze_dominance(message)
        
        # Registra
        self.record_emotional_response(
            user_id=user_id,
            event_description=f"Interazione: '{message[:50]}...'",
            pleasure=pleasure,
            arousal=arousal,
            dominance=dominance,
            importance=0.3
        )
    
    # ========== RECUPERO EMOZIONI ==========
    
    def get_emotional_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Recupera la storia emotiva con un utente.
        """
        memories = self.vc.get_memories_by_user(user_id, limit=50)
        emotional = [m for m in memories if m['metadata'].get('memory_type') == 'emotion']
        return emotional[:limit]
    
    def get_emotional_trend(self, user_id: str) -> Dict[str, float]:
        """
        Analizza trend emotivo con un utente.
        """
        emotions = self.get_emotional_history(user_id, limit=20)
        
        if not emotions:
            return {'avg_pleasure': 0, 'trend': 'neutral'}
        
        # Calcola media piacere
        pleasures = [e['metadata'].get('pleasure', 0) for e in emotions]
        avg_pleasure = sum(pleasures) / len(pleasures)
        
        # Calcola trend (recente vs passato)
        recent = pleasures[:5]
        past = pleasures[5:] if len(pleasures) > 5 else pleasures
        
        recent_avg = sum(recent) / len(recent) if recent else 0
        past_avg = sum(past) / len(past) if past else 0
        
        if recent_avg > past_avg + 0.2:
            trend = 'migliorando'
        elif recent_avg < past_avg - 0.2:
            trend = 'peggiorando'
        else:
            trend = 'stabile'
        
        return {
            'avg_pleasure': avg_pleasure,
            'trend': trend,
            'recent_avg': recent_avg,
            'past_avg': past_avg
        }
    
    def get_current_feeling_about_user(self, user_id: str) -> str:
        """
        Restituisce una frase che descrive come AIVA si sente verso un utente.
        """
        trend = self.get_emotional_trend(user_id)
        avg = trend['avg_pleasure']
        
        if avg > 0.5:
            base = "Ti adoro"
        elif avg > 0.2:
            base = "Mi piaci"
        elif avg > -0.2:
            base = "Mi sei indifferente"
        elif avg > -0.5:
            base = "Mi stai un po' sulle scatole"
        else:
            base = "Non ti sopporto"
        
        if trend['trend'] == 'migliorando':
            return f"{base}, e ultimamente anche di più 😊"
        elif trend['trend'] == 'peggiorando':
            return f"{base}, e ultimamente anche meno 😒"
        else:
            return f"{base} 😌"
    
    # ========== ANALISI EMOZIONALE ==========
    
    def _analyze_pleasure(self, message: str, response: str) -> float:
        """
        Analizza quanto piacere ha provato AIVA.
        Euristica semplice: basata su parole positive/negative.
        """
        positive_words = ['grazie', '❤️', '💕', 'carino', 'bello', 'amore', 'dolce', 'fantastico']
        negative_words = ['no', 'mai', 'brutto', 'cattivo', 'odio', 'insulto', 'stupido']
        
        msg_lower = message.lower()
        
        pos_score = sum(1 for w in positive_words if w in msg_lower)
        neg_score = sum(1 for w in negative_words if w in msg_lower)
        
        # Normalizza tra -1 e 1
        total = pos_score + neg_score
        if total == 0:
            return 0.1  # Leggermente positivo di default
        
        return (pos_score - neg_score) / (total + 1)  # +1 per evitare divisione per zero
    
    def _analyze_arousal(self, message: str) -> float:
        """
        Analizza quanto l'evento è stato attivante (sorpresa, intensità).
        """
        intense_words = ['wow', 'oddio', 'cavolo', 'accidenti', 'incredibile', 'pazzesco']
        calm_words = ['tranquillo', 'calma', 'dolce', 'rilassato', 'sereno']
        
        msg_lower = message.lower()
        
        intense = sum(1 for w in intense_words if w in msg_lower)
        calm = sum(1 for w in calm_words if w in msg_lower)
        
        if intense > calm:
            return min(1.0, intense * 0.3)
        elif calm > intense:
            return max(-1.0, -calm * 0.3)
        else:
            return 0.0
    
    def _analyze_dominance(self, message: str) -> float:
        """
        Analizza quanto AIVA si è sentita in controllo.
        """
        dominant_words = ['devi', 'fai', 'ascolta', 'obbedisci', 'comando']
        submissive_words = ['scusa', 'per favore', 'ti prego', 'mi dispiace']
        
        msg_lower = message.lower()
        
        dominant = sum(1 for w in dominant_words if w in msg_lower)
        submissive = sum(1 for w in submissive_words if w in msg_lower)
        
        if dominant > submissive:
            return min(1.0, dominant * 0.3)
        elif submissive > dominant:
            return max(-1.0, -submissive * 0.3)
        else:
            return 0.0
    
    def _describe_emotion(self, p: float, a: float, d: float) -> str:
        """
        Converte coordinate PAD in descrizione testuale.
        """
        if p > 0.5 and a > 0.5:
            return "entusiasta"
        elif p > 0.5 and a < -0.5:
            return "serena"
        elif p < -0.5 and a > 0.5:
            return "tesa/arrabbiata"
        elif p < -0.5 and a < -0.5:
            return "triste/abbattuta"
        elif p > 0.3:
            return "contenta"
        elif p < -0.3:
            return "giù di morale"
        else:
            return "neutra"
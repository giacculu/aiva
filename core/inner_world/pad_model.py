"""
Modello PAD (Pleasure-Arousal-Dominance) per emozioni continue
"""
import random
import math
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
from loguru import logger

class PADModel:
    """
    Spazio emotivo tridimensionale continuo.
    Ogni emozione è un punto in questo spazio.
    
    Piacevolezza (P): -1 (triste) a +1 (felice)
    Attivazione (A): -1 (calmo) a +1 (eccitato)
    Dominanza (D): -1 (sottomesso) a +1 (dominante)
    """
    
    # Emozioni di base come punti nello spazio PAD
    EMOTIONS = {
        'felice': (0.8, 0.5, 0.4),
        'entusiasta': (0.9, 0.8, 0.6),
        'contenta': (0.6, 0.2, 0.3),
        'serena': (0.5, -0.3, 0.2),
        'rilassata': (0.4, -0.6, 0.1),
        'triste': (-0.7, -0.3, -0.4),
        'malinconica': (-0.4, -0.5, -0.2),
        'arrabbiata': (-0.5, 0.7, 0.6),
        'frustrata': (-0.3, 0.4, -0.3),
        'ansiosa': (-0.2, 0.6, -0.5),
        'sorpresa': (0.2, 0.8, 0.0),
        'innamorata': (0.9, 0.6, 0.2),
        'grata': (0.7, 0.1, 0.2),
        'curiosa': (0.3, 0.5, 0.1),
        'annoiata': (-0.4, -0.5, -0.3),
        'offesa': (-0.6, 0.3, -0.4),
    }
    
    def __init__(self, initial_emotion: str = 'serena'):
        """
        Inizializza lo stato emotivo.
        
        Args:
            initial_emotion: Emozione iniziale (default: serena)
        """
        if initial_emotion in self.EMOTIONS:
            self.p, self.a, self.d = self.EMOTIONS[initial_emotion]
        else:
            self.p, self.a, self.d = 0.0, 0.0, 0.0
        
        # Storia delle emozioni (per tracciare cambiamenti)
        self.history = []
        self._record_state(initial_emotion)
        
        logger.debug(f"❤️ Modello PAD inizializzato: P={self.p:.2f}, A={self.a:.2f}, D={self.d:.2f}")
    
    def _record_state(self, source: str = "init"):
        """Registra lo stato attuale nella storia."""
        self.history.append({
            'timestamp': datetime.now(),
            'p': self.p,
            'a': self.a,
            'd': self.d,
            'source': source
        })
        # Mantieni solo ultimi 1000 stati
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
    
    # ========== MUTAZIONI EMOZIONALI ==========
    
    def shift(self, dp: float = 0.0, da: float = 0.0, dd: float = 0.0, source: str = "shift"):
        """
        Sposta lo stato emotivo di un delta.
        I valori sono automaticamente limitati a [-1, 1].
        """
        self.p = max(-1.0, min(1.0, self.p + dp))
        self.a = max(-1.0, min(1.0, self.a + da))
        self.d = max(-1.0, min(1.0, self.d + dd))
        self._record_state(source)
    
    def set_emotion(self, emotion_name: str, intensity: float = 1.0):
        """
        Imposta direttamente un'emozione (con possibile intensità).
        """
        if emotion_name in self.EMOTIONS:
            base_p, base_a, base_d = self.EMOTIONS[emotion_name]
            self.p = base_p * intensity
            self.a = base_a * intensity
            self.d = base_d * intensity
            self._record_state(f"set_{emotion_name}")
    
    def blend(self, emotion1: str, emotion2: str, weight: float = 0.5):
        """
        Combina due emozioni (weight 0 = solo emotion1, 1 = solo emotion2).
        """
        p1, a1, d1 = self.EMOTIONS[emotion1]
        p2, a2, d2 = self.EMOTIONS[emotion2]
        
        self.p = p1 * (1 - weight) + p2 * weight
        self.a = a1 * (1 - weight) + a2 * weight
        self.d = d1 * (1 - weight) + d2 * weight
        
        self._record_state(f"blend_{emotion1}_{emotion2}")
    
    def react_to_message(self, message: str, sentiment_score: Optional[float] = None):
        """
        Modifica lo stato emotivo in base a un messaggio ricevuto.
        """
        # Se non abbiamo sentiment, usiamo un'euristica
        if sentiment_score is None:
            # Analisi semplificata
            positive_words = ['❤️', '💕', 'grazie', 'carino', 'bello', 'amore']
            negative_words = ['no', 'mai', 'brutto', 'cattivo', 'odio']
            
            msg_lower = message.lower()
            pos = sum(1 for w in positive_words if w in msg_lower)
            neg = sum(1 for w in negative_words if w in msg_lower)
            
            if pos > neg:
                sentiment_score = 0.3
            elif neg > pos:
                sentiment_score = -0.3
            else:
                sentiment_score = 0.0
        
        # Modifica P (piacevolezza) in base al sentiment
        self.shift(dp=sentiment_score * 0.2, source="message_reaction")
    
    # ========== STATO ATTUALE ==========
    
    def get_state(self) -> Dict[str, float]:
        """Restituisce lo stato emotivo attuale."""
        return {
            'pleasure': self.p,
            'arousal': self.a,
            'dominance': self.d
        }
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """
        Trova l'emozione più vicina nello spazio PAD.
        Restituisce (nome_emozione, distanza).
        """
        min_dist = float('inf')
        closest = 'neutra'
        
        for emotion, (ep, ea, ed) in self.EMOTIONS.items():
            # Distanza euclidea
            dist = math.sqrt(
                (self.p - ep)**2 + 
                (self.a - ea)**2 + 
                (self.d - ed)**2
            )
            
            if dist < min_dist:
                min_dist = dist
                closest = emotion
        
        # Normalizza distanza (max possibile è ~3.46)
        similarity = 1.0 - (min_dist / 3.5)
        return closest, similarity
    
    def get_emotion_name(self) -> str:
        """Restituisce il nome dell'emozione dominante."""
        name, _ = self.get_dominant_emotion()
        return name
    
    def get_emotion_emoji(self) -> str:
        """Restituisce un emoji corrispondente all'emozione."""
        emotion = self.get_emotion_name()
        
        emoji_map = {
            'felice': '😊',
            'entusiasta': '🤩',
            'contenta': '😌',
            'serena': '😇',
            'rilassata': '😎',
            'triste': '😔',
            'malinconica': '🥺',
            'arrabbiata': '😠',
            'frustrata': '😤',
            'ansiosa': '😰',
            'sorpresa': '😲',
            'innamorata': '🥰',
            'grata': '🙏',
            'curiosa': '🤔',
            'annoiata': '😑',
            'offesa': '😒',
        }
        
        return emoji_map.get(emotion, '😐')
    
    def get_description(self) -> str:
        """Restituisce una descrizione testuale dello stato emotivo."""
        emotion, similarity = self.get_dominant_emotion()
        emoji = self.get_emotion_emoji()
        
        if similarity > 0.8:
            return f"{emoji} decisamente {emotion}"
        elif similarity > 0.5:
            return f"{emoji} {emotion}"
        else:
            return f"{emoji} {emotion} (con sfumature)"
    
    # ========== TENDENZE ==========
    
    def get_trend(self, minutes: int = 60) -> Dict[str, float]:
        """
        Calcola il trend emotivo degli ultimi N minuti.
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [h for h in self.history if h['timestamp'] > cutoff]
        
        if len(recent) < 2:
            return {'p': 0, 'a': 0, 'd': 0}
        
        first = recent[0]
        last = recent[-1]
        
        return {
            'p': last['p'] - first['p'],
            'a': last['a'] - first['a'],
            'd': last['d'] - first['d']
        }
    
    def is_improving(self) -> bool:
        """Verifica se l'umore sta migliorando (P in aumento)."""
        trend = self.get_trend(30)
        return trend['p'] > 0.1
    
    def is_worsening(self) -> bool:
        """Verifica se l'umore sta peggiorando (P in diminuzione)."""
        trend = self.get_trend(30)
        return trend['p'] < -0.1
    
    # ========== PERSISTENZA ==========
    
    def to_dict(self) -> Dict:
        """Serializza lo stato per persistenza."""
        return {
            'p': self.p,
            'a': self.a,
            'd': self.d,
            'history': [
                {
                    'timestamp': h['timestamp'].isoformat(),
                    'p': h['p'],
                    'a': h['a'],
                    'd': h['d'],
                    'source': h['source']
                }
                for h in self.history[-100:]  # Solo ultimi 100
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PADModel':
        """Ricrea lo stato da dizionario."""
        instance = cls('serena')
        instance.p = data.get('p', 0.0)
        instance.a = data.get('a', 0.0)
        instance.d = data.get('d', 0.0)
        
        # Ricostruisci storia
        instance.history = []
        for h in data.get('history', []):
            instance.history.append({
                'timestamp': datetime.fromisoformat(h['timestamp']),
                'p': h['p'],
                'a': h['a'],
                'd': h['d'],
                'source': h['source']
            })
        
        return instance
"""
Feedback implicito: impara dalle reazioni dell'utente
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import random
import math

class ImplicitFeedback:
    """
    Analizza il feedback implicito dell'utente:
    - Tempo di risposta
    - Lunghezza delle risposte
    - Cambi di argomento
    - Abbandono conversazione
    - Reazioni emotive
    """
    
    def __init__(self):
        self.feedback_history = {}  # user_id -> lista feedback
        logger.debug("📊 Feedback implicito inizializzato")
    
    def analyze_response(self, 
                        user_id: str,
                        user_message: str,
                        bot_response: str,
                        response_time: float,
                        conversation_context: Dict) -> Dict[str, float]:
        """
        Analizza la risposta dell'utente per estrarre feedback implicito.
        
        Args:
            user_id: ID utente
            user_message: Messaggio dell'utente
            bot_response: Risposta del bot
            response_time: Tempo impiegato dall'utente per rispondere (secondi)
            conversation_context: Contesto della conversazione
        
        Returns:
            Dict con punteggi di feedback per diversi aspetti
        """
        
        feedback = {
            'engagement': self._calculate_engagement(user_message, response_time),
            'satisfaction': self._calculate_satisfaction(user_message),
            'interest': self._calculate_interest(user_message),
            'emotional_response': self._calculate_emotional_response(user_message),
            'topic_continuation': self._calculate_topic_continuation(user_message, bot_response)
        }
        
        # Salva nella storia
        if user_id not in self.feedback_history:
            self.feedback_history[user_id] = []
        
        self.feedback_history[user_id].append({
            'timestamp': datetime.now(),
            'feedback': feedback,
            'user_message': user_message[:100],
            'bot_response': bot_response[:100]
        })
        
        # Mantieni solo ultimi 100 feedback per utente
        if len(self.feedback_history[user_id]) > 100:
            self.feedback_history[user_id] = self.feedback_history[user_id][-100:]
        
        return feedback
    
    def _calculate_engagement(self, message: str, response_time: float) -> float:
        """
        Calcola quanto l'utente è coinvolto.
        """
        engagement = 0.5  # Base
        
        # Tempo di risposta (più veloce = più coinvolto)
        if response_time < 30:  # Meno di 30 secondi
            engagement += 0.3
        elif response_time < 120:  # Meno di 2 minuti
            engagement += 0.1
        elif response_time > 600:  # Più di 10 minuti
            engagement -= 0.2
        
        # Lunghezza messaggio
        words = len(message.split())
        if words > 20:
            engagement += 0.2
        elif words > 10:
            engagement += 0.1
        elif words < 3:
            engagement -= 0.1
        
        return max(0.0, min(1.0, engagement))
    
    def _calculate_satisfaction(self, message: str) -> float:
        """
        Calcola la soddisfazione dell'utente.
        """
        satisfaction = 0.5
        
        # Parole positive/negative
        positive_words = ['grazie', '❤️', '👍', 'perfetto', 'ottimo', 'bello', 'brava']
        negative_words = ['no', 'male', 'sbagliato', 'brutto', 'deluso', 'insoddisfatto']
        
        msg_lower = message.lower()
        
        pos_count = sum(1 for w in positive_words if w in msg_lower)
        neg_count = sum(1 for w in negative_words if w in msg_lower)
        
        satisfaction += pos_count * 0.1
        satisfaction -= neg_count * 0.15
        
        return max(0.0, min(1.0, satisfaction))
    
    def _calculate_interest(self, message: str) -> float:
        """
        Calcola l'interesse dell'utente.
        """
        interest = 0.5
        
        # Domande mostrano interesse
        question_count = message.count('?')
        interest += question_count * 0.15
        
        # Richieste di approfondimento
        deepening_phrases = ['dimmi di più', 'approfondisci', 'spiegami', 'come mai']
        if any(p in message.lower() for p in deepening_phrases):
            interest += 0.3
        
        # Cambi bruschi di argomento (negativo)
        if len(message.split()) < 3 and '?' not in message:
            interest -= 0.2
        
        return max(0.0, min(1.0, interest))
    
    def _calculate_emotional_response(self, message: str) -> float:
        """
        Calcola l'intensità della risposta emotiva.
        """
        # Conteggio emoticon
        import re
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]')
        emojis = emoji_pattern.findall(message)
        
        emotional = len(emojis) * 0.2
        
        # Punteggiatura enfatica
        emotional += message.count('!') * 0.1
        emotional += message.count('...') * 0.05
        
        return min(1.0, emotional)
    
    def _calculate_topic_continuation(self, user_msg: str, bot_msg: str) -> float:
        """
        Calcola se l'utente continua sullo stesso topic.
        """
        # Estrai parole chiave (semplificato)
        user_words = set(user_msg.lower().split())
        bot_words = set(bot_msg.lower().split())
        
        if not bot_words:
            return 0.5
        
        # Parole in comune
        common = user_words.intersection(bot_words)
        overlap = len(common) / len(bot_words)
        
        return min(1.0, overlap * 2)  # Scala
    
    def get_user_trend(self, user_id: str, days: int = 7) -> Dict[str, float]:
        """
        Calcola il trend di feedback per un utente.
        """
        if user_id not in self.feedback_history:
            return {}
        
        recent = [
            f for f in self.feedback_history[user_id]
            if f['timestamp'] > datetime.now() - timedelta(days=days)
        ]
        
        if not recent:
            return {}
        
        # Media dei feedback
        avg_feedback = {}
        for key in recent[0]['feedback'].keys():
            values = [f['feedback'][key] for f in recent]
            avg_feedback[key] = sum(values) / len(values)
        
        return avg_feedback
    
    def get_learning_signal(self, user_id: str) -> Dict[str, float]:
        """
        Genera segnale di apprendimento per ottimizzare comportamento.
        """
        trend = self.get_user_trend(user_id)
        
        if not trend:
            return {}
        
        # Converti in segnali di apprendimento
        signals = {}
        
        if trend.get('engagement', 0.5) < 0.4:
            signals['increase_engagement'] = 1 - trend['engagement']
        
        if trend.get('satisfaction', 0.5) < 0.4:
            signals['improve_quality'] = 1 - trend['satisfaction']
        
        if trend.get('interest', 0.5) < 0.3:
            signals['add_variety'] = 1 - trend['interest']
        
        return signals
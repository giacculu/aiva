"""
Estrazione di informazioni implicite dal messaggio
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger

class ImplicitExtractor:
    """
    Estrae ciò che l'utente NON dice esplicitamente:
    - Stati d'animo impliciti
    - Bisogni nascosti
    - Relazioni tra concetti
    - Contraddizioni
    """
    
    def __init__(self):
        logger.debug("🔍 Implicit Extractor inizializzato")
    
    def extract(self, text: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Estrae informazioni implicite dal messaggio.
        
        Args:
            text: Testo del messaggio
            history: Cronologia recente (opzionale)
        
        Returns:
            Dict con informazioni implicite
        """
        text_lower = text.lower()
        
        result = {
            'mood': self._extract_mood(text_lower),
            'needs': self._extract_needs(text_lower),
            'topics': self._extract_topics(text_lower),
            'contradictions': [],
            'hidden_requests': self._extract_hidden_requests(text_lower),
            'timing': self._extract_timing(text_lower),
            'intensity': self._extract_intensity(text_lower)
        }
        
        # Se c'è storia, cerca contraddizioni
        if history:
            result['contradictions'] = self._find_contradictions(text, history)
        
        return result
    
    def _extract_mood(self, text: str) -> Dict[str, float]:
        """
        Estrae l'umore implicito dallo stile di scrittura.
        """
        mood = {}
        
        # Lunghezza frasi (frasi corte = agitazione, lunghe = calma)
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if avg_sentence_length < 3:
            mood['agitation'] = 0.7
        elif avg_sentence_length > 15:
            mood['calm'] = 0.6
        
        # Uso della punteggiatura
        if '!' in text:
            mood['excitement'] = min(1.0, mood.get('excitement', 0) + 0.4)
        if '?' in text:
            mood['curiosity'] = min(1.0, mood.get('curiosity', 0) + 0.3)
        if '...' in text:
            mood['hesitation'] = 0.5
            mood['thoughtful'] = 0.6
        
        # Uso delle maiuscole
        words = text.split()
        all_caps = sum(1 for w in words if w.isupper() and len(w) > 1)
        if all_caps > 1:
            mood['anger'] = min(1.0, mood.get('anger', 0) + 0.5)
        
        return mood
    
    def _extract_needs(self, text: str) -> List[str]:
        """
        Estrae bisogni impliciti.
        """
        needs = []
        
        # Bisogno di attenzione
        attention_phrases = ['mi ascolti', 'ci sei', 'rispondi', 'ci sei?']
        if any(p in text for p in attention_phrases):
            needs.append('attention')
        
        # Bisogno di conforto
        comfort_phrases = ['tutto male', 'che tristezza', 'mi sento giù', 'non ce la faccio']
        if any(p in text for p in comfort_phrases):
            needs.append('comfort')
        
        # Bisogno di validazione
        validation_phrases = ['hai ragione', 'dimmi che', 'conferma', 'vero?']
        if any(p in text for p in validation_phrases):
            needs.append('validation')
        
        # Bisogno di intimità
        intimacy_phrases = ['vicino', 'abbraccio', 'calore', 'dolcezza']
        if any(p in text for p in intimacy_phrases):
            needs.append('intimacy')
        
        return needs
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Estrae i topic principali (anche se non esplicitamente nominati).
        """
        topics = []
        
        # Topic work
        work_words = ['lavoro', 'ufficio', 'colleghi', 'capo', 'stipendio', 'carriera']
        if any(w in text for w in work_words):
            topics.append('lavoro')
        
        # Topic relazioni
        relationship_words = ['amico', 'fidanzato', 'ragazzo', 'moglie', 'marito', 'famiglia']
        if any(w in text for w in relationship_words):
            topics.append('relazioni')
        
        # Topic salute
        health_words = ['salute', 'dottore', 'medico', 'malattia', 'dolore', 'stanco']
        if any(w in text for w in health_words):
            topics.append('salute')
        
        # Topic tempo libero
        leisure_words = ['weekend', 'vacanza', 'viaggio', 'festa', 'divertimento']
        if any(w in text for w in leisure_words):
            topics.append('tempo_libero')
        
        return topics
    
    def _extract_hidden_requests(self, text: str) -> List[str]:
        """
        Estrae richieste implicite (cose che l'utente vuole ma non chiede direttamente).
        """
        hidden = []
        
        # Richiesta implicita di foto
        if 'come sei' in text or 'fammi vedere' in text:
            hidden.append('foto')
        
        # Richiesta implicita di attenzione
        if 'nessuno mi capisce' in text or 'solo tu' in text:
            hidden.append('attenzione_esclusiva')
        
        # Richiesta implicita di rassicurazione
        if 'non sono abbastanza' in text or 'non valgo' in text:
            hidden.append('rassicurazione')
        
        # Richiesta implicita di consiglio
        if 'cosa faresti' in text or 'come ti comporteresti' in text:
            hidden.append('consiglio')
        
        return hidden
    
    def _extract_timing(self, text: str) -> Dict[str, Any]:
        """
        Estrae riferimenti temporali impliciti.
        """
        timing = {
            'urgency': False,
            'reference_to_past': False,
            'reference_to_future': False,
            'time_phrases': []
        }
        
        # Urgenza
        if 'subito' in text or 'ora' in text or 'immediatamente' in text:
            timing['urgency'] = True
            timing['time_phrases'].append('urgente')
        
        # Passato
        past_phrases = ['ieri', 'scorso', 'fa', 'prima', 'già']
        if any(p in text for p in past_phrases):
            timing['reference_to_past'] = True
            timing['time_phrases'].append('passato')
        
        # Futuro
        future_phrases = ['domani', 'prossimo', 'dopo', 'più tardi', 'poi']
        if any(p in text for p in future_phrases):
            timing['reference_to_future'] = True
            timing['time_phrases'].append('futuro')
        
        return timing
    
    def _extract_intensity(self, text: str) -> float:
        """
        Estrae l'intensità emotiva implicita.
        """
        intensity = 0.0
        
        # Lunghezza (testi lunghi = più intensi)
        intensity += min(0.3, len(text) / 1000)
        
        # Punteggiatura enfatica
        intensity += text.count('!') * 0.1
        intensity += text.count('?') * 0.05
        intensity += text.count('...') * 0.1
        
        # Parole intense
        intense_words = ['mai', 'sempre', 'tutto', 'niente', 'assolutamente', 'davvero']
        intensity += sum(0.1 for w in intense_words if w in text)
        
        return min(1.0, intensity)
    
    def _find_contradictions(self, current_text: str, history: List[Dict]) -> List[Dict]:
        """
        Trova contraddizioni tra il messaggio attuale e la cronologia.
        """
        contradictions = []
        
        if len(history) < 4:  # Serve abbastanza contesto
            return contradictions
        
        # Prendi ultimi messaggi dell'utente
        user_messages = [h['content'] for h in history if h['role'] == 'user'][-3:]
        
        if not user_messages:
            return contradictions
        
        # Confronta con messaggio attuale
        current_lower = current_text.lower()
        
        # Cerca affermazioni opposte
        opposite_pairs = [
            ('mi piace', 'non mi piace'),
            ('ti amo', 'non ti amo'),
            ('ci sto', 'non ci sto'),
            ('vengo', 'non vengo'),
            ('sì', 'no'),
            ('vero', 'falso')
        ]
        
        for pos, neg in opposite_pairs:
            if pos in current_lower:
                # Controlla se in passato ha detto il contrario
                for old_msg in user_messages:
                    if neg in old_msg.lower():
                        contradictions.append({
                            'type': 'opinion_change',
                            'current': pos,
                            'previous': neg,
                            'previous_message': old_msg[:50]
                        })
                        break
        
        return contradictions
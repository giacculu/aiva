"""
Analisi del sentiment e del tono emotivo dei messaggi
"""
from typing import Dict, Tuple, Optional, List
import re
from loguru import logger

class SentimentAnalyzer:
    """
    Analizza il sentiment e il tono emotivo dei messaggi.
    Combina euristiche lessicali con analisi contestuale.
    """
    
    # Dizionari emotivi italiani (semplificati)
    POSITIVE_WORDS = {
        'amore', '❤️', '💕', 'grazie', 'carino', 'bello', 'fantastico', 'meraviglioso',
        'felice', 'contento', 'gioia', 'sorriso', 'abbraccio', 'ti voglio bene',
        'dolce', 'speciale', 'unico', 'grande', 'perfetto', 'stupendo', 'adoro'
    }
    
    NEGATIVE_WORDS = {
        'odio', '💔', 'triste', 'rabbia', 'arrabbiato', 'deluso', 'brutto', 'cattivo',
        'schifo', 'pessimo', 'terribile', 'orribile', 'noioso', 'stupido', 'idiota',
        'maledetto', 'pianto', 'lacrime', 'sofferenza', 'dolore'
    }
    
    INTENSIFIERS = {
        'molto', 'tanto', 'davvero', 'veramente', 'assolutamente', 'proprio',
        'estremamente', 'incredibilmente', 'super', 'ultra', 'mega'
    }
    
    NEGATIONS = {
        'non', 'mai', 'nemmeno', 'neppure', 'no', 'per niente'
    }
    
    def __init__(self):
        logger.debug("📊 Sentiment Analyzer inizializzato")
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analizza il sentiment di un testo.
        
        Returns:
            Dict con:
            - polarity: da -1 (negativo) a +1 (positivo)
            - intensity: da 0 (neutro) a 1 (molto intenso)
            - confidence: confidenza dell'analisi
        """
        if not text:
            return {'polarity': 0.0, 'intensity': 0.0, 'confidence': 0.0}
        
        text_lower = text.lower()
        
        # Conta parole positive e negative
        pos_count = 0
        neg_count = 0
        
        # Cerca parole positive
        for word in self.POSITIVE_WORDS:
            if word in text_lower:
                pos_count += text_lower.count(word)
        
        # Cerca parole negative
        for word in self.NEGATIVE_WORDS:
            if word in text_lower:
                neg_count += text_lower.count(word)
        
        # Rileva intensificatori
        intensifier_count = 0
        for word in self.INTENSIFIERS:
            if word in text_lower:
                intensifier_count += text_lower.count(word)
        
        # Rileva negazioni
        negation_count = 0
        for word in self.NEGATIONS:
            if word in text_lower:
                negation_count += text_lower.count(word)
        
        # Calcola polarità base
        total = pos_count + neg_count
        if total == 0:
            polarity = 0.0
        else:
            polarity = (pos_count - neg_count) / total
        
        # Applica effetto negazioni (inverte se ci sono negazioni vicine a parole emotive)
        if negation_count > 0 and abs(polarity) > 0:
            # Euristica: se ci sono negazioni, potrebbe invertire il sentiment
            # Per semplicità, riduciamo la polarità
            polarity *= (1 - min(0.5, negation_count * 0.1))
        
        # Calcola intensità
        intensity = min(1.0, (total / 10) + (intensifier_count * 0.1))
        
        # Confidenza
        confidence = min(1.0, total / 5)  # Più parole emotive = più confidenza
        
        # Arricchisci con analisi di frasi chiave
        self._analyze_key_phrases(text_lower, polarity, intensity)
        
        return {
            'polarity': round(polarity, 2),
            'intensity': round(intensity, 2),
            'confidence': round(confidence, 2)
        }
    
    def _analyze_key_phrases(self, text: str, polarity: float, intensity: float) -> None:
        """Analisi aggiuntiva di frasi chiave."""
        # Frasi d'amore
        love_phrases = ['ti amo', 'ti adoro', 'ti voglio bene', 'sei speciale']
        for phrase in love_phrases:
            if phrase in text:
                logger.debug(f"❤️ Rilevata frase d'amore: '{phrase}'")
        
        # Frasi di rabbia
        anger_phrases = ['ti odio', 'va via', 'lasciami', 'smettila']
        for phrase in anger_phrases:
            if phrase in text:
                logger.debug(f"😠 Rilevata frase di rabbia: '{phrase}'")
    
    def get_emotion_from_sentiment(self, sentiment: Dict[str, float]) -> str:
        """
        Converte il sentiment in un'emozione.
        """
        polarity = sentiment['polarity']
        intensity = sentiment['intensity']
        
        if polarity > 0.5:
            if intensity > 0.7:
                return 'entusiasta'
            else:
                return 'felice'
        elif polarity > 0.2:
            return 'contenta'
        elif polarity > -0.2:
            return 'neutra'
        elif polarity > -0.5:
            return 'triste'
        else:
            if intensity > 0.7:
                return 'arrabbiata'
            else:
                return 'molto triste'
    
    def get_sentiment_description(self, sentiment: Dict[str, float]) -> str:
        """
        Restituisce una descrizione testuale del sentiment.
        """
        polarity = sentiment['polarity']
        intensity = sentiment['intensity']
        
        if polarity > 0.5:
            if intensity > 0.7:
                return "molto positivo ed entusiasta"
            else:
                return "positivo"
        elif polarity > 0.2:
            return "leggermente positivo"
        elif polarity > -0.2:
            return "neutro"
        elif polarity > -0.5:
            return "leggermente negativo"
        else:
            if intensity > 0.7:
                return "molto negativo e intenso"
            else:
                return "negativo"
    
    def combine_sentiments(self, sentiments: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Combina più analisi di sentiment (es. su più frasi).
        """
        if not sentiments:
            return {'polarity': 0.0, 'intensity': 0.0, 'confidence': 0.0}
        
        # Media pesata per confidenza
        total_weight = sum(s.get('confidence', 1.0) for s in sentiments)
        
        polarity = sum(s['polarity'] * s.get('confidence', 1.0) for s in sentiments) / total_weight
        intensity = sum(s['intensity'] * s.get('confidence', 1.0) for s in sentiments) / total_weight
        confidence = sum(s['confidence'] for s in sentiments) / len(sentiments)
        
        return {
            'polarity': round(polarity, 2),
            'intensity': round(intensity, 2),
            'confidence': round(confidence, 2)
        }
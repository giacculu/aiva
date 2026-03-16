"""
Rilevazione dell'intento profondo dell'utente
"""
from typing import Dict, List, Optional, Any, Tuple
import re
from loguru import logger

class IntentAnalyzer:
    """
    Analizza l'intento dell'utente andando oltre le parole chiave.
    Comprende cosa vuole veramente, anche quando non lo dice esplicitamente.
    """
    
    # Intenti principali
    INTENTS = [
        'saluto',
        'domanda_personale',
        'richiesta_foto',
        'richiesta_video',
        'richiesta_intima',
        'supporto_economico',
        'confessione',
        'sfogo',
        'complimento',
        'critica',
        'scherzo',
        'rimprovero',
        'addio',
        'curiosita_generica',
        'richiesta_info',
        'proposta',
        'rifiuto',
        'accettazione',
        'dubbio',
        'confusione'
    ]
    
    # Pattern per intenti (euristici)
    PATTERNS = {
        'saluto': [
            r'ciao', r'salve', r'hey', r'buongiorno', r'buonasera', r'buonanotte',
            r'come va', r'come stai', r'tutto bene'
        ],
        'domanda_personale': [
            r'come stai', r'cosa fai', r'dove sei', r'che fai', r'come ti senti',
            r'pensi a me', r'mi hai pensato'
        ],
        'richiesta_foto': [
            r'foto', r'selfie', r'vederti', r'mostrami', r'fammi vedere',
            r'che faccia hai', r'come sei vestita', r'immagine'
        ],
        'richiesta_video': [
            r'video', r'filmato', r'ripresa', r'registrazione'
        ],
        'richiesta_intima': [
            r'intima', r'sexy', r'hot', r'nuda', r'provocante', r'senza veli',
            r'spogliati', r'mostrati', r'osé'
        ],
        'supporto_economico': [
            r'paypal', r'pagamento', r'donazione', r'sostenerti', r'contribuire',
            r'supporto', r'donare', r'soldi', r'euro', r'pagare', r'contributo'
        ],
        'confessione': [
            r'ti devo dire', r'confessare', r'segreto', r'non l\'ho mai detto',
            r'devo dirti', r'ammetto che'
        ],
        'sfogo': [
            r'non ne posso più', r'sono stanco', r'che giornata', r'che stress',
            r'è successo che', r'mi è successo'
        ],
        'complimento': [
            r'sei bella', r'sei carina', r'sei fantastica', r'sei speciale',
            r'mi piaci', r'ti adoro', r'❤️', r'💕', r'stupenda'
        ],
        'critica': [
            r'non mi piace', r'fai schifo', r'sei noiosa', r'che delusione',
            r'potevi fare meglio', r'sbagli'
        ],
        'addio': [
            r'addio', r'ciao ciao', r'arrivederci', r'devo andare', r'vado',
            r'ci sentiamo', r'a dopo', r'a presto'
        ]
    }
    
    def __init__(self):
        self.confidence_threshold = 0.3
        logger.debug("🎯 Intent Analyzer inizializzato")
    
    def analyze(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analizza l'intento del messaggio.
        
        Args:
            text: Testo del messaggio
            context: Contesto aggiuntivo (es. conversazione recente)
        
        Returns:
            Dict con:
            - primary_intent: intento principale
            - secondary_intents: intenti secondari
            - confidence: confidenza (0-1)
            - details: dettagli aggiuntivi
        """
        text_lower = text.lower()
        
        # Calcola punteggi per ogni intento
        scores = {}
        for intent, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1
            
            if score > 0:
                # Normalizza in base alla lunghezza del testo
                normalized = score / (len(text.split()) + 1)  # +1 per evitare divisione per zero
                scores[intent] = min(1.0, normalized)
        
        # Se nessun pattern match, assegna intento generico
        if not scores:
            scores['curiosita_generica'] = 0.3
        
        # Trova intento principale
        primary = max(scores.items(), key=lambda x: x[1])
        
        # Trova intenti secondari (sopra soglia)
        secondary = [
            {'intent': intent, 'confidence': conf}
            for intent, conf in scores.items()
            if intent != primary[0] and conf > self.confidence_threshold
        ]
        
        # Arricchisci con analisi contestuale
        details = self._analyze_context(text_lower, context)
        
        # Aggiungi profondità all'intento principale
        primary_intent = self._add_depth(primary[0], text_lower, details)
        
        result = {
            'primary_intent': primary_intent,
            'primary_confidence': round(primary[1], 2),
            'secondary_intents': secondary[:3],  # Limita a 3
            'confidence': round(primary[1], 2),
            'details': details
        }
        
        logger.debug(f"🎯 Intento rilevato: {result['primary_intent']} ({result['confidence']})")
        return result
    
    def _analyze_context(self, text: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Analisi contestuale aggiuntiva."""
        details = {
            'has_question': '?' in text,
            'has_exclamation': '!' in text,
            'word_count': len(text.split()),
            'char_count': len(text),
            'has_emoji': bool(re.search(r'[\U0001F600-\U0001F64F]', text)),
            'is_very_short': len(text.split()) < 3,
            'is_very_long': len(text.split()) > 50
        }
        
        # Rileva urgenza
        urgent_words = ['urgente', 'presto', 'veloce', 'subito', 'adesso', 'ora']
        details['urgency'] = sum(1 for w in urgent_words if w in text) > 0
        
        # Rileva importanza
        important_words = ['importante', 'serio', 'grave', 'fondamentale', 'cruciale']
        details['importance'] = sum(1 for w in important_words if w in text) > 0
        
        return details
    
    def _add_depth(self, intent: str, text: str, details: Dict) -> str:
        """
        Aggiunge profondità all'intento base.
        """
        # Arricchisci intento con sfumature
        if intent == 'richiesta_foto':
            if 'subito' in text or 'ora' in text:
                return 'richiesta_foto_urgente'
            elif 'dopo' in text or 'più tardi' in text:
                return 'richiesta_foto_dilazionata'
        
        elif intent == 'supporto_economico':
            if 'caffè' in text or 'caffe' in text:
                return 'supporto_caffe'
            elif 'cena' in text:
                return 'supporto_cena'
            elif 'regalo' in text:
                return 'supporto_regalo'
        
        elif intent == 'saluto':
            if details.get('has_question'):
                return 'saluto_con_domanda'
            elif 'ciao ciao' in text or 'addio' in text:
                return 'saluto_di_addio'
        
        return intent
    
    def needs_response(self, intent_analysis: Dict) -> bool:
        """
        Determina se l'intento richiede una risposta.
        """
        primary = intent_analysis['primary_intent']
        
        # Intenti che potrebbero non richiedere risposta
        no_response_intents = ['addio']
        
        if primary in no_response_intents:
            return False
        
        # Se c'è una domanda esplicita, sempre rispondi
        if intent_analysis.get('details', {}).get('has_question'):
            return True
        
        # Default
        return True
    
    def get_expected_response_type(self, intent_analysis: Dict) -> str:
        """
        Suggerisce il tipo di risposta attesa.
        """
        primary = intent_analysis['primary_intent']
        
        if primary.startswith('richiesta_foto'):
            return 'media'
        elif primary.startswith('richiesta_video'):
            return 'media'
        elif primary == 'supporto_economico':
            return 'paypal_link'
        elif primary == 'domanda_personale':
            return 'emotional_response'
        elif primary == 'confessione':
            return 'empathetic_response'
        elif primary == 'sfogo':
            return 'listening_response'
        elif primary == 'complimento':
            return 'grateful_response'
        elif primary == 'critica':
            return 'defensive_response'
        else:
            return 'normal_response'
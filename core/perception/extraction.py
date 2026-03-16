"""
AIVA 2.0 – ESTRAZIONE DELL'IMPLICITO
AIVA legge tra le righe:
- Cosa l'utente non dice ma intende
- Le emozioni nascoste
- Le mezze verità
- I silenzi che parlano
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import numpy as np

class ImplicitExtractor:
    """
    Estrae ciò che è implicito nel messaggio.
    Combina analisi del contesto, pattern e psicologia inversa.
    """
    
    # Pattern per cose non dette
    IMPLICIT_PATTERNS = {
        "dubbio": [
            r"non so se",
            r"forse",
            r"magari",
            r"chissà",
            r"dubito",
            r"incerto",
            r"non sono sicur[oa]"
        ],
        "desiderio_nascosto": [
            r"vorrei ma",
            r"mi piacerebbe però",
            r"se potessi",
            r"sarebbe bello se",
            r"magari un giorno"
        ],
        "paura": [
            r"ho paura che",
            r"temo che",
            r"non vorrei che",
            r"mi preoccupa",
            r"che ansia"
        ],
        "gelosia": [
            r"chi è",
            r"con chi",
            r"altri",
            r"anche con",
            r"solo per me"
        ],
        "insicurezza": [
            r"non sono abbastanza",
            r"non valgo",
            r"non merito",
            r"sono brutto",
            r"non piaccio"
        ],
        "bisogno_di_attenzione": [
            r"nessuno mi",
            r"tutti mi ignorano",
            r"non mi calcola",
            r"non rispondi mai"
        ],
        "sottinteso_sessuale": [
            r"da soli",
            r"senza niente",
            r"intimo",
            r"vicini",
            r"toccare"
        ],
        "rimpianto": [
            r"se solo",
            r"avrei dovuto",
            r"potevo",
            r"ormai è tardi",
            r"peccato che"
        ],
        "speranza": [
            r"spero che",
            r"magari",
            r"chissà che",
            r"forse un giorno",
            r"se tutto va bene"
        ]
    }
    
    # Segnali di incongruenza (tra ciò che dice e ciò che prova)
    INCONGRUENCE_SIGNALS = {
        "risata_finta": [
            "ahah", "lol", "haha",
            "che ridere", "molto divertente"
        ],
        "ottimismo_forzato": [
            "tutto bene", "tutto ok", "nessun problema",
            "va tutto bene", "non preoccuparti"
        ],
        "minimizzazione": [
            "non importa", "fa niente", "lascia stare",
            "non è niente", "roba da poco"
        ]
    }
    
    def __init__(self):
        self.implicit_patterns = self.IMPLICIT_PATTERNS
        self.incongruence_signals = self.INCONGRUENCE_SIGNALS
        
        # Compila regex
        self._compiled_patterns = {}
        for category, patterns in self.implicit_patterns.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        # Cache per analisi recenti
        self.recent_extractions = {}
        self.CACHE_SIZE = 100
        
        logger.info("🔍 Implicit Extractor inizializzato")
    
    async def extract(self, text: str, user_id: Optional[str] = None, 
                     context: Optional[Dict] = None) -> Dict:
        """
        Estrae ciò che è implicito nel messaggio.
        """
        if not text:
            return self._empty_result()
        
        text_lower = text.lower()
        
        # Rileva pattern impliciti
        detected_patterns = self._detect_implicit_patterns(text_lower)
        
        # Rileva incongruenze
        incongruences = self._detect_incongruences(text_lower)
        
        # Analizza i silenzi (se contesto disponibile)
        silences = self._analyze_silences(context) if context else {}
        
        # Cosa nasconde veramente
        hidden_mood = self._infer_hidden_mood(text_lower, detected_patterns)
        
        # Cosa desidera veramente
        hidden_desire = self._infer_hidden_desire(text_lower, detected_patterns)
        
        # Livello di sincerità
        sincerity = self._calculate_sincerity(text_lower, incongruences)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            
            # Categorie implicite rilevate
            "detected_patterns": detected_patterns,
            
            # Emozione nascosta
            "hidden_mood": hidden_mood,
            "hidden_desire": hidden_desire,
            
            # Incongruenze
            "incongruences": incongruences,
            "sincerity": sincerity,  # 0-1, quanto è sincero
            
            # Silenzi (se disponibili)
            "silence_analysis": silences,
            
            # Interpretazione
            "interpretation": self._generate_interpretation(
                detected_patterns, hidden_mood, hidden_desire, incongruences
            ),
            
            # Per il prompt
            "summary": self._generate_summary(
                detected_patterns, hidden_mood, hidden_desire
            )
        }
        
        return result
    
    def _detect_implicit_patterns(self, text: str) -> Dict[str, float]:
        """
        Rileva pattern di cose non dette.
        Restituisce categorie con punteggio di confidenza.
        """
        detected = {}
        
        for category, patterns in self._compiled_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if pattern.search(text):
                    matches += 1
                    confidence += 0.3  # base per match
            
            if matches > 0:
                # Normalizza
                confidence = min(1.0, confidence)
                detected[category] = confidence
        
        return detected
    
    def _detect_incongruences(self, text: str) -> Dict[str, float]:
        """
        Rileva segnali di incongruenza (dice una cosa ma ne pensa un'altra).
        """
        incongruences = {}
        
        for category, signals in self.incongruence_signals.items():
            for signal in signals:
                if signal in text:
                    incongruences[category] = 0.7
                    break
        
        return incongruences
    
    def _analyze_silences(self, context: Dict) -> Dict:
        """
        Analizza i silenzi tra i messaggi.
        """
        if not context:
            return {}
        
        now = datetime.now()
        last_message_time = context.get("last_message_time")
        
        if not last_message_time:
            return {}
        
        # Calcola tempo dall'ultimo messaggio
        if isinstance(last_message_time, str):
            last_message_time = datetime.fromisoformat(last_message_time)
        
        seconds_since = (now - last_message_time).total_seconds()
        minutes_since = seconds_since / 60
        
        result = {
            "seconds_since_last": seconds_since,
            "minutes_since_last": minutes_since,
            "interpretation": self._interpret_silence(minutes_since, context)
        }
        
        return result
    
    def _interpret_silence(self, minutes: float, context: Dict) -> str:
        """
        Interpreta cosa significa un silenzio.
        """
        if minutes < 1:
            return "risposta immediata"
        elif minutes < 5:
            return "pausa normale"
        elif minutes < 15:
            return "sta pensando"
        elif minutes < 60:
            return "distratto/a"
        elif minutes < 180:
            return "assente"
        else:
            return "probabilmente non vuole più parlare"
    
    def _infer_hidden_mood(self, text: str, detected: Dict) -> Dict:
        """
        Inferisce l'umore nascosto (quello che non dice).
        """
        # Mappa pattern a emozioni nascoste
        mood_map = {
            "dubbio": "insicurezza",
            "paura": "ansia",
            "gelosia": "possessività",
            "insicurezza": "bassa autostima",
            "bisogno_di_attenzione": "solitudine",
            "rimpianto": "tristezza",
            "speranza": "ottimismo",
            "desiderio_nascosto": "frustrazione"
        }
        
        hidden = {}
        for pattern, confidence in detected.items():
            if pattern in mood_map:
                hidden[mood_map[pattern]] = confidence
        
        if not hidden:
            return {"emotion": "neutro", "confidence": 0.5}
        
        # Trova l'emozione dominante
        dominant = max(hidden, key=hidden.get)
        return {
            "emotion": dominant,
            "confidence": hidden[dominant],
            "all": hidden
        }
    
    def _infer_hidden_desire(self, text: str, detected: Dict) -> Dict:
        """
        Inferisce il desiderio nascosto.
        """
        desire_map = {
            "desiderio_nascosto": "qualcosa che non osa chiedere",
            "sottinteso_sessuale": "intimità fisica",
            "bisogno_di_attenzione": "attenzione e affetto",
            "gelosia": "esclusività",
            "speranza": "cambiamento positivo"
        }
        
        desires = {}
        for pattern, confidence in detected.items():
            if pattern in desire_map:
                desires[desire_map[pattern]] = confidence
        
        if not desires:
            return {"desire": "non evidente", "confidence": 0.0}
        
        dominant = max(desires, key=desires.get)
        return {
            "desire": dominant,
            "confidence": desires[dominant],
            "all": desires
        }
    
    def _calculate_sincerity(self, text: str, incongruences: Dict) -> float:
        """
        Calcola quanto è sincero il messaggio (0-1).
        """
        # Base: assumptione di sincerità
        sincerity = 0.8
        
        # Penalità per incongruenze
        sincerity -= len(incongruences) * 0.2
        
        # Segnali linguistici di insincerità
        insincerity_signals = [
            "diciamo", "praticamente", "in pratica",
            "tipo che", "cioè", "nel senso"
        ]
        
        for signal in insincerity_signals:
            if signal in text:
                sincerity -= 0.1
        
        return max(0.0, min(1.0, sincerity))
    
    def _generate_interpretation(self, detected: Dict, hidden_mood: Dict, 
                                hidden_desire: Dict, incongruences: Dict) -> str:
        """
        Genera un'interpretazione in linguaggio naturale.
        """
        parts = []
        
        if detected:
            main_pattern = max(detected, key=detected.get)
            pattern_desc = self._get_pattern_description(main_pattern)
            parts.append(pattern_desc)
        
        if hidden_mood.get("emotion") and hidden_mood["emotion"] != "neutro":
            parts.append(f"sembra {hidden_mood['emotion']} anche se non lo dice")
        
        if hidden_desire.get("desire") and hidden_desire["desire"] != "non evidente":
            parts.append(f"forse desidera {hidden_desire['desire']}")
        
        if incongruences:
            parts.append("c'è qualcosa che non quadra")
        
        if not parts:
            return "sembra sincero, niente di particolarmente nascosto"
        
        return ". ".join(parts).capitalize() + "."
    
    def _generate_summary(self, detected: Dict, hidden_mood: Dict, 
                         hidden_desire: Dict) -> str:
        """
        Genera un riassunto breve per il prompt.
        """
        parts = []
        
        if hidden_mood.get("emotion") and hidden_mood["emotion"] != "neutro":
            parts.append(f"sembra {hidden_mood['emotion']}")
        
        if hidden_desire.get("desire") and hidden_desire["desire"] != "non evidente":
            parts.append(f"desidera {hidden_desire['desire']}")
        
        if not parts:
            return "nessun implicito rilevante"
        
        return ", ".join(parts)
    
    def _get_pattern_description(self, pattern: str) -> str:
        """Restituisce una descrizione per un pattern"""
        descriptions = {
            "dubbio": "è in dubbio",
            "desiderio_nascosto": "ha un desiderio inespresso",
            "paura": "ha paura",
            "gelosia": "è geloso",
            "insicurezza": "è insicuro",
            "bisogno_di_attenzione": "cerca attenzione",
            "sottinteso_sessuale": "sottintende qualcosa di intimo",
            "rimpianto": "ha rimpianti",
            "speranza": "spera in qualcosa"
        }
        return descriptions.get(pattern, pattern)
    
    def _empty_result(self) -> Dict:
        """Restituisce un risultato vuoto"""
        return {
            "detected_patterns": {},
            "hidden_mood": {"emotion": "neutro", "confidence": 0.0},
            "hidden_desire": {"desire": "non evidente", "confidence": 0.0},
            "incongruences": {},
            "sincerity": 1.0,
            "silence_analysis": {},
            "interpretation": "nessun implicito rilevato",
            "summary": "nessun implicito"
        }

# Istanza globale
implicit_extractor = ImplicitExtractor()
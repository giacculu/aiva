"""
AIVA 2.0 – ANALISI DEL SENTIMENT E DEL TONO
AIVA percepisce le emozioni dietro le parole dell'utente.
Non solo positivo/negativo, ma sfumature: ironia, rabbia, tristezza, eccitazione...
"""

import numpy as np
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from loguru import logger
import emoji
from collections import Counter

class SentimentAnalyzer:
    """
    Analizza il sentiment e il tono dei messaggi.
    Combina lessici, pattern e (opzionalmente) chiamate a modelli più avanzati.
    """
    
    # Lessico emotivo italiano (semplificato)
    EMOTION_LEXICON = {
        "positivo": [
            "amore", "felice", "bello", "bravo", "grazie", "❤️", "💕", "🥰",
            "fantastico", "meraviglioso", "stupendo", "adoro", "piacere",
            "contento", "felicità", "gioia", "sorriso", "ridere", "ahah",
            "complimenti", "wow", "ottimo", "perfetto", "grande"
        ],
        "negativo": [
            "odio", "triste", "brutto", "schifo", "male", "😠", "😡", "💔",
            "terribile", "orribile", "pessimo", "disastro", "noia", "annoio",
            "rabbia", "arrabbiato", "deluso", "delusione", "piangere", "😢",
            "lamento", "problema", "difficile", "duro", "fatica"
        ],
        "eccitazione": [
            "wow", "😱", "🔥", "incredibile", "pazzesco", "fantastico",
            "urca", "cavolo", "accidenti", "mannaggia", "finalmente", "sì",
            "evviva", "forza", "dai", "grande", "super", "straordinario"
        ],
        "tristezza": [
            "😢", "😭", "triste", "tristezza", "malinconia", "piangere",
            "lacrime", "sofferenza", "dolore", "mancanza", "rimpianto",
            "nostalgia", "vuoto", "solo", "solitario"
        ],
        "rabbia": [
            "😠", "😡", "rabbia", "arrabbiato", "incazzato", "furioso",
            "odio", "detesto", "insopportabile", "inaccettabile", "vergogna",
            "maledetto", "stupido", "idiota", "coglione", "cazzo"
        ],
        "sorpresa": [
            "😱", "😲", "wow", "oh", "ah", "eh", "cavolo", "accidenti",
            "davvero?", "ma dai", "non ci credo", "incredibile", "impossibile"
        ],
        "ironia": [
            "certo che", "proprio", "guarda un po'", "che bello",
            "come no", "ovvio", "chiaramente", "ma va", "ma dai"
        ],
        "affetto": [
            "❤️", "💕", "🥰", "😘", "ti voglio bene", "ti adoro",
            "ti amo", "cuore", "tesoro", "amore", "dolcezza", "carezza"
        ],
        "noia": [
            "noia", "annoio", "stanco", "stufo", "solito", "sempre uguale",
            "che palle", "rottura", "pesante", "lungo", "interminabile"
        ]
    }
    
    # Pattern per rilevare caratteristiche specifiche
    PATTERNS = {
        "domanda": r"\?$|^\s*[Cc]ome|[Pp]erché|[Dd]ove|[Qq]uando|[Cc]hi|[Cc]osa",
        "esclamazione": r"!+$",
        "maiuscolo": r"[A-Z]{4,}",  # parole TUTTE MAIUSCOLE
        "ripetizione": r"(.)\1{3,}",  # lettere ripetute (ciaoooo)
        "puntini": r"\.{3,}",  # sospensione...
        "numeri": r"\d+",
        "url": r"https?://\S+|www\.\S+",
        "mention": r"@\w+",
        "hashtag": r"#\w+"
    }
    
    def __init__(self):
        self.lexicon = self.EMOTION_LEXICON
        self.patterns = self.PATTERNS
        
        # Normalizza lessico (tutto lowercase)
        for emotion, words in self.lexicon.items():
            self.lexicon[emotion] = [w.lower() for w in words]
        
        # Cache per analisi recenti
        self.recent_analyses = {}
        self.CACHE_SIZE = 100
        
        logger.info("📊 Sentiment Analyzer inizializzato")
    
    async def analyze(self, text: str) -> Dict:
        """
        Analizza il sentiment di un testo.
        Restituisce un dizionario con varie dimensioni.
        """
        if not text:
            return self._neutral_result()
        
        # Controlla cache (se stesso testo analizzato di recente)
        cache_key = hash(text) % self.CACHE_SIZE
        if cache_key in self.recent_analyses:
            cached = self.recent_analyses[cache_key]
            if cached["text"] == text and (datetime.now() - cached["timestamp"]).seconds < 60:
                return cached["result"]
        
        # Analisi
        result = {
            "text": text[:100],  # preview
            "timestamp": datetime.now().isoformat(),
            
            # Dimensioni principali
            "positivity": self._calculate_positivity(text),
            "arousal": self._calculate_arousal(text),  # eccitazione/calma
            "dominance": self._calculate_dominance(text),  # sicurezza/insicurezza
            
            # Emozioni specifiche
            "emotions": self._detect_emotions(text),
            "primary_emotion": None,  # sarà riempito dopo
            
            # Caratteristiche stilistiche
            "style": self._analyze_style(text),
            
            # Metriche
            "word_count": len(text.split()),
            "char_count": len(text),
            "emoji_count": emoji.emoji_count(text),
            "question": bool(re.search(self.patterns["domanda"], text, re.IGNORECASE)),
            "exclamation": bool(re.search(self.patterns["esclamazione"], text)),
            "caps_ratio": self._caps_ratio(text),
            
            # Sfumature
            "irony_probability": self._detect_irony(text),
            "sarcasm_probability": self._detect_sarcasm(text),
            "formality": self._detect_formality(text),
            
            # Intensità
            "intensity": self._calculate_intensity(text)
        }
        
        # Determina emozione primaria
        if result["emotions"]:
            result["primary_emotion"] = max(result["emotions"], key=result["emotions"].get)
        
        # Normalizza dimensioni PAD (0-1)
        result["positivity"] = (result["positivity"] + 1) / 2  # da [-1,1] a [0,1]
        result["arousal"] = (result["arousal"] + 1) / 2
        result["dominance"] = (result["dominance"] + 1) / 2
        
        # Salva in cache
        self.recent_analyses[cache_key] = {
            "text": text,
            "result": result,
            "timestamp": datetime.now()
        }
        
        return result
    
    def _calculate_positivity(self, text: str) -> float:
        """
        Calcola la positività/negatività del testo.
        Restituisce un valore tra -1 e 1.
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        pos_count = sum(1 for w in words if w in self.lexicon["positivo"])
        neg_count = sum(1 for w in words if w in self.lexicon["negativo"])
        
        # Conta anche emoji
        for char in text:
            if emoji.is_emoji(char):
                if char in self.lexicon["positivo"]:
                    pos_count += 2  # emoji pesano di più
                elif char in self.lexicon["negativo"]:
                    neg_count += 2
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def _calculate_arousal(self, text: str) -> float:
        """
        Calcola l'eccitazione/calma del testo.
        Restituisce un valore tra -1 (calmo) e 1 (eccitato).
        """
        text_lower = text.lower()
        
        # Parole che indicano eccitazione
        excited_words = self.lexicon["eccitazione"] + self.lexicon["sorpresa"] + self.lexicon["rabbia"]
        calm_words = ["calma", "rilassato", "tranquillo", "pace", "sereno", "dolce"]
        
        excited_count = sum(1 for w in excited_words if w in text_lower)
        calm_count = sum(1 for w in calm_words if w in text_lower)
        
        # Fattori stilistici
        exclamations = text.count('!')
        questions = text.count('?')
        caps = self._caps_ratio(text) * 10
        
        excited_count += exclamations * 0.5 + questions * 0.3 + caps
        
        total = excited_count + calm_count
        if total == 0:
            return 0.0
        
        return (excited_count - calm_count) / total
    
    def _calculate_dominance(self, text: str) -> float:
        """
        Calcola la dominanza/sicurezza del testo.
        Restituisce un valore tra -1 (insicuro) e 1 (sicuro).
        """
        text_lower = text.lower()
        
        # Parole che indicano sicurezza
        dominant_words = ["devo", "voglio", "faccio", "posso", "sono", "so", "certezza"]
        submissive_words = ["forse", "potrei", "se posso", "se vuoi", "scusa", "dipende"]
        
        dominant_count = sum(1 for w in dominant_words if w in text_lower)
        submissive_count = sum(1 for w in submissive_words if w in text_lower)
        
        # Frasi imperative
        imperative = bool(re.search(r"^[A-Za-z]+!$", text))
        if imperative:
            dominant_count += 2
        
        total = dominant_count + submissive_count
        if total == 0:
            return 0.0
        
        return (dominant_count - submissive_count) / total
    
    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """
        Rileva la presenza di varie emozioni nel testo.
        Restituisce un dizionario emozione -> probabilità (0-1).
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        emotions = {}
        for emotion, lexicon in self.lexicon.items():
            if emotion in ["positivo", "negativo"]:
                continue  # già calcolate separatamente
            
            # Conta occorrenze
            count = sum(1 for w in words if w in lexicon)
            for char in text:
                if emoji.is_emoji(char) and char in lexicon:
                    count += 2
            
            # Normalizza
            max_count = len(words) / 2  # massimo teorico
            emotions[emotion] = min(1.0, count / max_count) if max_count > 0 else 0.0
        
        return emotions
    
    def _analyze_style(self, text: str) -> Dict:
        """
        Analizza lo stile di scrittura.
        """
        return {
            "has_emojis": emoji.emoji_count(text) > 0,
            "has_questions": '?' in text,
            "has_exclamations": '!' in text,
            "has_ellipsis": '...' in text,
            "has_caps": self._caps_ratio(text) > 0.3,
            "has_repetitions": bool(re.search(r'(.)\1{3,}', text)),
            "avg_word_length": sum(len(w) for w in text.split()) / max(1, len(text.split())),
            "punctuation_density": sum(1 for c in text if c in '.,!?;:') / max(1, len(text))
        }
    
    def _detect_irony(self, text: str) -> float:
        """
        Stima la probabilità che il testo sia ironico.
        """
        text_lower = text.lower()
        
        # Indicatori di ironia
        irony_indicators = [
            "che bello", "proprio", "guarda un po'", "come no", "ovvio",
            "chiaramente", "ma certo", "sicuramente", "😏", "🙄"
        ]
        
        indicator_count = sum(1 for ind in irony_indicators if ind in text_lower)
        
        # Contrasto tra parole positive e negative
        pos = self._calculate_positivity(text)
        if pos > 0.5:
            # Se dice cose positive ma con indicatori ironici
            return min(1.0, indicator_count * 0.3)
        elif pos < -0.5:
            # Se dice cose negative ma con indicatori ironici
            return min(1.0, indicator_count * 0.2)
        
        return 0.0
    
    def _detect_sarcasm(self, text: str) -> float:
        """
        Stima la probabilità di sarcasmo.
        """
        text_lower = text.lower()
        
        # Il sarcasmo spesso usa esagerazioni
        exaggeration = bool(re.search(r"assolutamente|totalmente|completamente|mai|sempre", text_lower))
        
        # O contrasti forti
        pos = self._calculate_positivity(text)
        has_negative = any(w in text_lower for w in self.lexicon["negativo"])
        
        if exaggeration and has_negative and pos > 0.3:
            return 0.7
        
        return 0.0
    
    def _detect_formality(self, text: str) -> float:
        """
        Stima il livello di formalità (0 informale, 1 formale).
        """
        text_lower = text.lower()
        
        # Indicatori di informalità
        informal_indicators = ["ciao", "hey", "😊", "ahah", "lol", "cmq", "xkè", "nn", "ke"]
        informal_count = sum(1 for ind in informal_indicators if ind in text_lower)
        
        # Indicatori di formalità
        formal_indicators = ["gentile", "distinti saluti", "cordiali", "egregio", "spettabile"]
        formal_count = sum(1 for ind in formal_indicators if ind in text_lower)
        
        total = informal_count + formal_count
        if total == 0:
            return 0.5  # neutro
        
        return formal_count / total
    
    def _calculate_intensity(self, text: str) -> float:
        """
        Calcola l'intensità emotiva del testo (0-1).
        """
        factors = [
            self._caps_ratio(text) * 2,
            text.count('!') / 10,
            text.count('?') / 10,
            sum(1 for c in text if emoji.is_emoji(c)) / 5,
            len([w for w in text.split() if w.isupper()]) / max(1, len(text.split()))
        ]
        
        return min(1.0, sum(factors))
    
    def _caps_ratio(self, text: str) -> float:
        """
        Percentuale di caratteri in maiuscolo.
        """
        if not text:
            return 0.0
        
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        
        caps = sum(1 for c in letters if c.isupper())
        return caps / len(letters)
    
    def _neutral_result(self) -> Dict:
        """Restituisce un risultato neutro"""
        return {
            "text": "",
            "positivity": 0.5,
            "arousal": 0.5,
            "dominance": 0.5,
            "emotions": {},
            "primary_emotion": "neutro",
            "style": {},
            "word_count": 0,
            "char_count": 0,
            "emoji_count": 0,
            "question": False,
            "exclamation": False,
            "caps_ratio": 0.0,
            "irony_probability": 0.0,
            "sarcasm_probability": 0.0,
            "formality": 0.5,
            "intensity": 0.0
        }
    
    def get_summary(self, analysis: Dict) -> str:
        """
        Genera una descrizione testuale dell'analisi.
        """
        parts = []
        
        # Tono principale
        pos = analysis["positivity"]
        if pos > 0.7:
            parts.append("molto positivo")
        elif pos > 0.6:
            parts.append("positivo")
        elif pos < 0.3:
            parts.append("molto negativo")
        elif pos < 0.4:
            parts.append("negativo")
        
        # Arousal
        aro = analysis["arousal"]
        if aro > 0.7:
            parts.append("molto eccitato")
        elif aro < 0.3:
            parts.append("molto calmo")
        
        # Emozione primaria
        if analysis["primary_emotion"] and analysis["primary_emotion"] != "neutro":
            parts.append(f"con {analysis['primary_emotion']}")
        
        if not parts:
            return "tono neutro"
        
        return " e ".join(parts)

# Istanza globale
sentiment = SentimentAnalyzer()
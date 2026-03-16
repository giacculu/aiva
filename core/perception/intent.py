"""
AIVA 2.0 – RILEVAZIONE DELL'INTENTO
AIVA capisce cosa vuole veramente l'utente:
- Sta chiedendo qualcosa?
- Si sta lamentando?
- Vuole fare una richiesta intima?
- Vuole supportarmi?
- Sta scherzando?
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from loguru import logger
import numpy as np

class IntentExtractor:
    """
    Estrae l'intento principale e secondario dai messaggi.
    Combina pattern, lessici e analisi contestuale.
    """
    
    # Categorie di intento principali
    INTENT_CATEGORIES = {
        # Richieste
        "request_info": {
            "keywords": ["che cos'è", "come si", "dimmi", "spiegami", "cos'è"],
            "weight": 1.0,
            "description": "Richiesta di informazioni"
        },
        "request_photo": {
            "keywords": ["foto", "immagine", "vederti", "selfie", "mostrami"],
            "weight": 1.2,
            "description": "Richiesta di foto"
        },
        "request_video": {
            "keywords": ["video", "filmato", "registrazione", "girato"],
            "weight": 1.2,
            "description": "Richiesta di video"
        },
        "request_intimate": {
            "keywords": ["intimo", "sexy", "hot", "sporca", "nuda", "provocante"],
            "weight": 1.5,
            "description": "Richiesta di contenuti intimi"
        },
        "request_chat": {
            "keywords": ["parlare", "chat", "conversare", "discutere"],
            "weight": 1.0,
            "description": "Richiesta di conversazione"
        },
        
        # Supporto
        "offer_support": {
            "keywords": ["aiutarti", "sostenerti", "supporto", "donazione", "contribuire"],
            "weight": 1.3,
            "description": "Offerta di supporto economico"
        },
        "payment_confirmation": {
            "keywords": ["pagato", "fatto pagamento", "trasferito", "inviato soldi"],
            "weight": 1.4,
            "description": "Conferma di avvenuto pagamento"
        },
        "ask_support": {
            "keywords": ["come supportarti", "dove posso", "link paypal", "sostenerti"],
            "weight": 1.3,
            "description": "Richiesta di come supportare"
        },
        
        # Relazionali
        "greeting": {
            "keywords": ["ciao", "salve", "hey", "buongiorno", "buonasera"],
            "weight": 0.8,
            "description": "Saluto"
        },
        "farewell": {
            "keywords": ["ciao", "arrivederci", "a dopo", "a presto", "notte"],
            "weight": 0.8,
            "description": "Commiato"
        },
        "compliment": {
            "keywords": ["bella", "carina", "brava", "simpatica", "dolce"],
            "weight": 1.1,
            "description": "Complimento"
        },
        "insult": {
            "keywords": ["brutta", "stupida", "idiota", "cogliona", "roffa"],
            "weight": 1.5,
            "description": "Insulto"
        },
        "flirt": {
            "keywords": ["ti piace", "ti piaccio", "bella", "sexy", "❤️", "💕"],
            "weight": 1.2,
            "description": "Flirt"
        },
        "joke": {
            "keywords": ["scherzo", "ridere", "ahah", "lol", "divertente"],
            "weight": 0.9,
            "description": "Scherzo"
        },
        
        # Personali
        "share_info": {
            "keywords": ["mi chiamo", "ho anni", "vivo a", "lavoro come"],
            "weight": 1.1,
            "description": "Condivisione di informazioni personali"
        },
        "ask_personal": {
            "keywords": ["tu come", "tu cosa", "che fai", "dove vivi"],
            "weight": 1.0,
            "description": "Richiesta di informazioni personali"
        },
        "emotional": {
            "keywords": ["triste", "felice", "solo", "depresso", "contento"],
            "weight": 1.2,
            "description": "Espressione emotiva"
        },
        
        # Azioni
        "command": {
            "keywords": ["fai", "manda", "dimmi", "rispondi", "scrivimi"],
            "weight": 1.1,
            "description": "Comando"
        },
        "suggestion": {
            "keywords": ["dovresti", "potresti", "prova a", "perché non"],
            "weight": 0.9,
            "description": "Suggerimento"
        },
        "complaint": {
            "keywords": ["lento", "non funziona", "problema", "errore", "male"],
            "weight": 1.2,
            "description": "Lamentela"
        },
        
        # Meta
        "question": {
            "keywords": ["?"],
            "weight": 0.7,
            "description": "Domanda generica"
        },
        "unknown": {
            "keywords": [],
            "weight": 0.5,
            "description": "Intento non riconosciuto"
        }
    }
    
    # Pattern per intenti complessi
    PATTERNS = {
        "nome": r"mi chiamo\s+(\w+)|sono\s+(\w+)|chiamo\s+(\w+)",
        "età": r"ho\s+(\d+)\s*anni",
        "città": r"vivo a\s+(\w+)|abito a\s+(\w+)|sono di\s+(\w+)",
        "lavoro": r"lavoro come\s+(\w+)|faccio il\s+(\w+)|faccio la\s+(\w+)",
        "pagamento": r"pagato\s+(\d+)|ho inviato\s+(\d+)|bonifico",
        "richiesta_foto": r"(?:mi )?mandi (?:una|la) foto|posso vederti",
        "richiesta_intima": r"(?:foto|video) (?:intima|sexy|hot|nuda)",
    }
    
    def __init__(self):
        self.categories = self.INTENT_CATEGORIES
        
        # Preprocessa keywords (lowercase)
        for intent, data in self.categories.items():
            data["keywords"] = [k.lower() for k in data["keywords"]]
        
        # Cache per analisi recenti
        self.recent_intents = {}
        self.CACHE_SIZE = 100
        
        logger.info("🎯 Intent Extractor inizializzato")
    
    async def extract(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Estrae l'intento principale dal messaggio.
        """
        if not text:
            return self._empty_result()
        
        text_lower = text.lower()
        
        # Calcola punteggi per ogni intento
        scores = {}
        for intent, data in self.categories.items():
            score = self._calculate_intent_score(text_lower, intent, data, context)
            if score > 0:
                scores[intent] = score
        
        # Determina intento principale
        if scores:
            primary_intent = max(scores, key=scores.get)
            primary_score = scores[primary_intent]
            
            # Trova secondari (sopra 0.3)
            secondary = [
                {"intent": i, "score": s}
                for i, s in scores.items()
                if s > 0.3 and i != primary_intent
            ]
            secondary.sort(key=lambda x: x["score"], reverse=True)
        else:
            primary_intent = "unknown"
            primary_score = 0.5
            secondary = []
        
        # Estrai parametri specifici
        params = self._extract_parameters(text, primary_intent)
        
        result = {
            "primary": primary_intent,
            "primary_description": self.categories[primary_intent]["description"],
            "confidence": primary_score,
            "secondary": secondary[:3],  # max 3 secondari
            "all_scores": dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]),
            "parameters": params,
            "is_question": '?' in text,
            "is_command": self._is_command(text),
            "urgency": self._calculate_urgency(text),
            "requires_action": self._requires_action(primary_intent),
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _calculate_intent_score(self, text: str, intent: str, data: Dict, context: Optional[Dict]) -> float:
        """
        Calcola il punteggio per un intento specifico.
        """
        score = 0.0
        
        # Match keywords
        for keyword in data["keywords"]:
            if keyword in text:
                score += 1.0
                # Bonus per match esatto all'inizio
                if text.startswith(keyword):
                    score += 0.5
        
        # Pattern specifici
        if intent == "request_photo":
            if re.search(r"mi mandi (?:una|la) foto", text):
                score += 2.0
        elif intent == "request_intimate":
            if re.search(r"(?:foto|video) (?:intima|sexy|hot)", text):
                score += 2.0
        elif intent == "offer_support":
            if re.search(r"posso (?:aiutarti|supportarti|darti soldi)", text):
                score += 2.0
        elif intent == "share_info":
            if re.search(r"mi chiamo|ho anni|vivo a", text):
                score += 2.0
        
        # Contesto (se fornito)
        if context:
            # Se è una risposta a una domanda precedente
            if context.get("last_intent") == "ask_personal" and intent == "share_info":
                score += 1.5
            # Se sta continuando un discorso
            if context.get("conversation_topic") == intent:
                score += 0.5
        
        # Normalizza con peso
        score = score * data["weight"]
        
        # Bonus per messaggi brevi (saluti, comandi)
        if len(text.split()) < 3 and intent in ["greeting", "farewell", "command"]:
            score += 0.5
        
        return score
    
    def _extract_parameters(self, text: str, primary_intent: str) -> Dict:
        """
        Estrae parametri specifici in base all'intento.
        """
        params = {}
        
        if primary_intent == "share_info":
            # Estrai nome
            name_match = re.search(self.PATTERNS["nome"], text, re.IGNORECASE)
            if name_match:
                params["name"] = next(g for g in name_match.groups() if g is not None)
            
            # Estrai età
            age_match = re.search(self.PATTERNS["età"], text, re.IGNORECASE)
            if age_match:
                params["age"] = int(age_match.group(1))
            
            # Estrai città
            city_match = re.search(self.PATTERNS["città"], text, re.IGNORECASE)
            if city_match:
                params["city"] = next(g for g in city_match.groups() if g is not None)
            
            # Estrai lavoro
            job_match = re.search(self.PATTERNS["lavoro"], text, re.IGNORECASE)
            if job_match:
                params["job"] = next(g for g in job_match.groups() if g is not None)
        
        elif primary_intent == "payment_confirmation":
            # Estrai importo
            amount_match = re.search(self.PATTERNS["pagamento"], text, re.IGNORECASE)
            if amount_match:
                params["amount"] = float(amount_match.group(1))
        
        elif primary_intent in ["request_photo", "request_intimate"]:
            # Che tipo di foto?
            if "selfie" in text:
                params["type"] = "selfie"
            elif "intima" in text:
                params["type"] = "intimate"
            elif "sexy" in text:
                params["type"] = "sexy"
        
        return params
    
    def _is_command(self, text: str) -> bool:
        """
        Determina se il messaggio è un comando.
        """
        command_patterns = [
            r"^fai\s+",
            r"^manda\s+",
            r"^dimmi\s+",
            r"^rispondi\s+",
            r"^scrivimi\s+",
            r"^vai\s+",
            r"^fermati\s+",
        ]
        
        return any(re.search(p, text, re.IGNORECASE) for p in command_patterns)
    
    def _calculate_urgency(self, text: str) -> float:
        """
        Calcola l'urgenza del messaggio (0-1).
        """
        urgency = 0.0
        
        # Parole che indicano urgenza
        urgent_words = ["presto", "veloce", "subito", "urgente", "ora", "adesso", "immediato"]
        for word in urgent_words:
            if word in text.lower():
                urgency += 0.3
        
        # Punteggiatura
        urgency += text.count('!') * 0.1
        urgency += text.count('?') * 0.05
        
        # Maiuscole
        caps_ratio = sum(1 for c in text if c.isupper()) / max(1, len(text))
        urgency += caps_ratio * 0.5
        
        return min(1.0, urgency)
    
    def _requires_action(self, intent: str) -> bool:
        """
        Determina se l'intento richiede un'azione immediata.
        """
        action_intents = [
            "request_photo",
            "request_video",
            "request_intimate",
            "payment_confirmation",
            "command",
            "complaint"
        ]
        return intent in action_intents
    
    def _empty_result(self) -> Dict:
        """Restituisce un risultato vuoto"""
        return {
            "primary": "unknown",
            "primary_description": "Intento non riconosciuto",
            "confidence": 0.0,
            "secondary": [],
            "all_scores": {},
            "parameters": {},
            "is_question": False,
            "is_command": False,
            "urgency": 0.0,
            "requires_action": False,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_intent_description(self, intent: str) -> str:
        """Restituisce la descrizione di un intento"""
        return self.categories.get(intent, {}).get("description", "Sconosciuto")
    
    def get_actionable_intents(self) -> List[str]:
        """Restituisce la lista di intenti che richiedono azione"""
        return [i for i, d in self.categories.items() 
                if i in ["request_photo", "request_video", "request_intimate", 
                        "payment_confirmation", "command", "complaint"]]

# Istanza globale
intent_extractor = IntentExtractor()
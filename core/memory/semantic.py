"""
Memoria semantica: fatti strutturati sull'utente
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
from database.sqlite.models import SQLiteDatabase

class SemanticMemory:
    """
    Gestisce la memoria fattuale (nomi, età, preferenze, etc.)
    Ogni fatto è associato a un utente e ha un livello di confidenza.
    """
    
    def __init__(self, db: SQLiteDatabase):
        self.db = db
        logger.debug("🧠 Memoria semantica inizializzata")
    
    # ========== FATTI BASE ==========
    
    def remember(self, user_id: str, key: str, value: str, 
                category: str = 'general', confidence: float = 1.0) -> None:
        """Salva un fatto."""
        self.db.remember_fact(user_id, key, value, category, confidence)
        logger.debug(f"📝 Fatto memorizzato: {user_id} | {key} = {value}")
    
    def recall(self, user_id: str, key: str) -> Optional[str]:
        """Recupera un fatto."""
        return self.db.recall_fact(user_id, key)
    
    def recall_all(self, user_id: str) -> Dict[str, str]:
        """Recupera tutti i fatti di un utente."""
        return self.db.recall_all_facts(user_id)
    
    def forget(self, user_id: str, key: str) -> None:
        """Dimentica un fatto."""
        self.db.forget_fact(user_id, key)
        logger.debug(f"🗑️ Fatto dimenticato: {user_id} | {key}")
    
    # ========== CATEGORIE SPECIALI ==========
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Restituisce un profilo completo dell'utente."""
        facts = self.recall_all(user_id)
        
        # Organizza per categorie
        profile = {
            'identity': {},
            'preferences': {},
            'history': {},
            'relationship': {},
            'other': {}
        }
        
        category_map = {
            'nome': 'identity',
            'età': 'identity',
            'città': 'identity',
            'lavoro': 'identity',
            'hobby': 'preferences',
            'musica': 'preferences',
            'film': 'preferences',
            'prima_volta': 'history',
            'ultima_interazione': 'history',
            'supporto': 'relationship',
            'livello': 'relationship'
        }
        
        for key, value in facts.items():
            cat = category_map.get(key, 'other')
            profile[cat][key] = value
        
        return profile
    
    # ========== RAGIONAMENTO SEMANTICO ==========
    
    def infer_gender(self, user_id: str) -> Optional[str]:
        """Tenta di inferire il genere dai fatti noti."""
        name = self.recall(user_id, 'nome')
        if not name:
            return None
        
        # Euristica semplice: nomi che finiscono in 'a' sono spesso femminili in italiano
        if name.lower().endswith('a'):
            return 'femminile'
        else:
            return 'maschile'
    
    def infer_age_group(self, user_id: str) -> Optional[str]:
        """Inferisce fascia d'età."""
        age_str = self.recall(user_id, 'età')
        if not age_str:
            return None
        
        try:
            age = int(age_str)
            if age < 18:
                return 'minorenne'
            elif age < 25:
                return 'giovane adulto'
            elif age < 40:
                return 'adulto'
            elif age < 60:
                return 'maturo'
            else:
                return 'senior'
        except ValueError:
            return None
    
    # ========== APPRENDIMENTO IMPLICITO ==========
    
    def learn_from_conversation(self, user_id: str, user_message: str, ai_response: str) -> None:
        """
        Estrae implicitamente informazioni dalla conversazione.
        Da chiamare dopo ogni interazione.
        """
        # Pattern per informazioni che l'utente potrebbe condividere spontaneamente
        import re
        
        patterns = {
            'nome': [
                r'mi chiamo\s+([A-Za-z]+)',
                r'sono\s+([A-Za-z]+)',
                r'(?:il|il mio) nome (?:è|e)\s+([A-Za-z]+)'
            ],
            'età': [
                r'ho\s+(\d+)\s*anni',
                r'(\d+)\s*anni'
            ],
            'città': [
                r'vivo a\s+([A-Za-z\s]+)',
                r'abito a\s+([A-Za-z\s]+)',
                r'sono di\s+([A-Za-z\s]+)'
            ],
            'lavoro': [
                r'lavoro come\s+([A-Za-z\s]+)',
                r'faccio (?:il|la)\s+([A-Za-z\s]+)'
            ],
            'hobby': [
                r'mi piace\s+([A-Za-z\s]+)',
                r'adoro\s+([A-Za-z\s]+)',
                r'passione\s+([A-Za-z\s]+)'
            ]
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Filtra parole comuni che non sono valori reali
                    if (len(value) > 2 and 
                        value.lower() not in ['qui', 'lì', 'la', 'il', 'un', 'una', 'uno']):
                        self.remember(user_id, key, value, confidence=0.8)
                        return  # Esce dopo il primo apprendimento
    
    # ========== STATISTICHE ==========
    
    def get_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Statistiche sulla memoria."""
        if user_id:
            facts = self.recall_all(user_id)
            return {
                'user_id': user_id,
                'fact_count': len(facts),
                'categories': self._count_categories(facts)
            }
        else:
            # Statistiche globali (da implementare con query al DB)
            return {
                'total_users': 0,  # TODO
                'total_facts': 0   # TODO
            }
    
    def _count_categories(self, facts: Dict[str, str]) -> Dict[str, int]:
        """Conta fatti per categoria."""
        categories = {}
        # Usa la stessa mappa di get_user_profile
        category_map = {
            'nome': 'identity', 'età': 'identity', 'città': 'identity', 'lavoro': 'identity',
            'hobby': 'preferences', 'musica': 'preferences', 'film': 'preferences',
            'prima_volta': 'history', 'ultima_interazione': 'history',
            'supporto': 'relationship', 'livello': 'relationship'
        }
        
        for key in facts:
            cat = category_map.get(key, 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        return categories
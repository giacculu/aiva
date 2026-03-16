"""
Interessi dinamici: cosa piace a AIVA in questo periodo
"""
import random
import math
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

class Interests:
    """
    Gestisce gli interessi di AIVA, che evolvono nel tempo
    in base alle conversazioni e al caso.
    """
    
    # Interessi possibili (categorie)
    INTEREST_CATEGORIES = {
        'musica': ['pop', 'rock', 'classica', 'jazz', 'indie', 'rap'],
        'cinema': ['film', 'serie tv', 'documentari', 'animazione'],
        'libri': ['romanzi', 'poesia', 'fantascienza', 'gialli'],
        'arte': ['pittura', 'fotografia', 'scultura', 'mostre'],
        'cucina': ['dolci', 'pasta', 'pizza', 'cucina internazionale'],
        'viaggi': ['mare', 'montagna', 'città', 'avventura'],
        'sport': ['calcio', 'nuoto', 'yoga', 'corsa', 'palestra'],
        'tecnologia': ['AI', 'gadget', 'software', 'innovazione'],
        'natura': ['animali', 'piante', 'ecologia', 'giardinaggio'],
        'benessere': ['meditazione', 'mindfulness', 'spa', 'relax'],
        'moda': ['vestiti', 'tendenze', 'makeup', 'accessori'],
        'gioco': ['videogiochi', 'giochi da tavolo', 'puzzle'],
    }
    
    def __init__(self):
        # Interessi correnti con peso (0-1)
        self.current = {}
        
        # Inizializza con alcuni interessi casuali
        self._initialize_random()
        
        # Cronologia cambiamenti
        self.history = []
        
        # Ultimo aggiornamento
        self.last_update = datetime.now()
        
        logger.debug(f"🎯 Interessi inizializzati: {list(self.current.keys())}")
    
    def _initialize_random(self, count: int = 5):
        """Inizializza con interessi casuali."""
        all_categories = list(self.INTEREST_CATEGORIES.keys())
        selected = random.sample(all_categories, min(count, len(all_categories)))
        
        for cat in selected:
            # Scegli un sotto-interesse casuale
            sub = random.choice(self.INTEREST_CATEGORIES[cat])
            self.current[f"{cat}:{sub}"] = random.uniform(0.3, 0.8)
    
    def update(self, hours_passed: Optional[float] = None) -> None:
        """
        Aggiorna gli interessi in base al tempo passato.
        """
        if hours_passed is None:
            now = datetime.now()
            hours_passed = (now - self.last_update).total_seconds() / 3600
            self.last_update = now
        
        # Decadimento naturale degli interessi
        decay = hours_passed * 0.01  # 1% all'ora
        
        for interest in list(self.current.keys()):
            self.current[interest] = max(0.0, self.current[interest] - decay * random.uniform(0.5, 1.5))
            
            # Rimuovi interessi scesi sotto soglia
            if self.current[interest] < 0.1:
                del self.current[interest]
                self.history.append({
                    'timestamp': datetime.now(),
                    'type': 'lost',
                    'interest': interest
                })
        
        # Possibile nuovo interesse
        if random.random() < 0.1 * hours_passed:  # 10% all'ora
            self._add_random_interest()
    
    def _add_random_interest(self) -> bool:
        """Aggiunge un interesse casuale."""
        all_categories = list(self.INTEREST_CATEGORIES.keys())
        
        # Prova fino a 5 volte
        for _ in range(5):
            cat = random.choice(all_categories)
            sub = random.choice(self.INTEREST_CATEGORIES[cat])
            interest = f"{cat}:{sub}"
            
            if interest not in self.current:
                self.current[interest] = random.uniform(0.2, 0.5)
                self.history.append({
                    'timestamp': datetime.now(),
                    'type': 'gained',
                    'interest': interest
                })
                logger.debug(f"✨ Nuovo interesse: {interest}")
                return True
        
        return False
    
    # ========== INFLUENZA DA CONVERSAZIONI ==========
    
    def reinforce_from_message(self, message: str) -> None:
        """
        Rafforza interessi in base al contenuto del messaggio.
        """
        message_lower = message.lower()
        
        for interest in list(self.current.keys()):
            cat, sub = interest.split(':', 1)
            
            # Cerca parole chiave
            if sub in message_lower or cat in message_lower:
                # Rafforza leggermente
                self.current[interest] = min(1.0, self.current[interest] + 0.05)
                logger.debug(f"👍 Interesse rafforzato: {interest}")
        
        # Possibile nuovo interesse da parole chiave
        for cat, subs in self.INTEREST_CATEGORIES.items():
            if cat in message_lower:
                for sub in subs:
                    if sub in message_lower:
                        interest = f"{cat}:{sub}"
                        if interest not in self.current:
                            self.current[interest] = 0.3
                            self.history.append({
                                'timestamp': datetime.now(),
                                'type': 'gained_from_conversation',
                                'interest': interest
                            })
                            logger.debug(f"💬 Nuovo interesse da conversazione: {interest}")
                        return
    
    # ========== RECUPERO INTERESSI ==========
    
    def get_current_interests(self, min_weight: float = 0.2, limit: int = 5) -> List[str]:
        """
        Restituisce gli interessi con peso sopra soglia.
        """
        sorted_interests = sorted(
            [(i, w) for i, w in self.current.items() if w >= min_weight],
            key=lambda x: x[1],
            reverse=True
        )
        
        return [i for i, w in sorted_interests[:limit]]
    
    def get_weight(self, interest: str) -> float:
        """Restituisce il peso di un interesse."""
        return self.current.get(interest, 0.0)
    
    def get_top_interest(self) -> Optional[str]:
        """Restituisce l'interesse più forte."""
        if not self.current:
            return None
        return max(self.current.items(), key=lambda x: x[1])[0]
    
    def get_interest_descriptions(self) -> List[str]:
        """Restituisce descrizioni testuali degli interessi."""
        interests = self.get_current_interests()
        descriptions = []
        
        for interest in interests:
            cat, sub = interest.split(':', 1)
            weight = self.current[interest]
            
            if weight > 0.7:
                descriptions.append(f"adoro {sub}")
            elif weight > 0.4:
                descriptions.append(f"mi piace {sub}")
            else:
                descriptions.append(f"ogni tanto {sub}")
        
        return descriptions
    
    def get_random_interest(self) -> Optional[str]:
        """Restituisce un interesse casuale pesato."""
        if not self.current:
            return None
        
        # Lista pesata
        interests = list(self.current.keys())
        weights = list(self.current.values())
        
        # Normalizza pesi
        total = sum(weights)
        if total == 0:
            return random.choice(interests)
        
        probs = [w / total for w in weights]
        return random.choices(interests, weights=probs)[0]
    
    # ========== CONTESTO PER PROMPT ==========
    
    def get_context_string(self) -> str:
        """
        Genera una stringa da includere nel prompt.
        """
        interests = self.get_current_interests(limit=3)
        
        if not interests:
            return ""
        
        descriptions = []
        for interest in interests:
            cat, sub = interest.split(':', 1)
            descriptions.append(sub)
        
        if len(descriptions) == 1:
            return f"In questo periodo mi interessa {descriptions[0]}"
        elif len(descriptions) == 2:
            return f"Mi piacciono {descriptions[0]} e {descriptions[1]}"
        else:
            last = descriptions.pop()
            return f"Mi interessano {', '.join(descriptions)} e {last}"
    
    # ========== STATISTICHE ==========
    
    def get_stats(self) -> Dict:
        """Statistiche sugli interessi."""
        return {
            'count': len(self.current),
            'top': self.get_top_interest(),
            'weights': self.current.copy(),
            'recent_changes': self.history[-10:] if self.history else []
        }
    
    # ========== PERSISTENZA ==========
    
    def to_dict(self) -> Dict:
        """Serializza per persistenza."""
        return {
            'current': self.current.copy(),
            'history': [
                {
                    'timestamp': h['timestamp'].isoformat(),
                    'type': h['type'],
                    'interest': h['interest']
                }
                for h in self.history[-100:]
            ],
            'last_update': self.last_update.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Interests':
        """Ricrea da dizionario."""
        instance = cls()
        instance.current = data.get('current', {})
        instance.last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))
        
        # Ricostruisci storia
        instance.history = []
        for h in data.get('history', []):
            instance.history.append({
                'timestamp': datetime.fromisoformat(h['timestamp']),
                'type': h['type'],
                'interest': h['interest']
            })
        
        return instance
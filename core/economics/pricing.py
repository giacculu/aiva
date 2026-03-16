"""
Pricing dinamico: prezzi base e personalizzati per utente
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import random
import math

class PricingManager:
    """
    Gestisce i prezzi dei contenuti in modo dinamico.
    I prezzi base sono minimi, ma possono variare in base a:
    - Fedeltà dell'utente
    - Relazione emotiva
    - Momento
    - Richiesta specifica
    """
    
    # Prezzi base (minimi assoluti)
    BASE_PRICES = {
        'foto_base': 5.00,
        'foto_selfie': 8.00,
        'foto_intima': 15.00,
        'foto_hot': 25.00,
        'video_base': 20.00,
        'video_intimo': 35.00,
        'video_hot': 50.00,
        'chat_intima_10min': 10.00,
        'chat_intima_30min': 25.00,
        'chat_vip_ora': 40.00,
        'audio_personale': 12.00,
        'set_foto_5': 60.00,
        'set_foto_10': 100.00
    }
    
    # Fattori di sconto per fedeltà
    LOYALTY_DISCOUNTS = {
        'nuovo': 1.0,      # Nessuno sconto
        'base': 0.95,      # 5% sconto
        'regular': 0.9,    # 10% sconto
        'vip': 0.8,        # 20% sconto
        'special': 0.75     # 25% sconto (utenti molto speciali)
    }
    
    def __init__(self):
        self.user_prices = {}  # Prezzi personalizzati per utente
        self.purchase_history = {}  # Storico acquisti per utente
        self.dynamic_factors = {}  # Fattori dinamici per utente
        
        logger.debug("💰 Pricing Manager inizializzato")
    
    def get_price(self, 
                  item_type: str,
                  user_id: Optional[str] = None,
                  context: Optional[Dict] = None) -> float:
        """
        Calcola il prezzo per un item, considerando utente e contesto.
        
        Args:
            item_type: Tipo di contenuto
            user_id: ID utente (opzionale)
            context: Contesto aggiuntivo (umore, richiesta, etc.)
        
        Returns:
            Prezzo in EUR
        """
        # Prezzo base
        base_price = self.BASE_PRICES.get(item_type, 10.00)
        
        # Se nessun utente, restituisci base
        if not user_id:
            return base_price
        
        # Ottieni livello fedeltà
        loyalty = self._get_user_loyalty(user_id)
        discount = self.LOYALTY_DISCOUNTS.get(loyalty, 1.0)
        
        # Prezzo dopo sconto fedeltà
        price = base_price * discount
        
        # Applica fattori dinamici
        if context:
            price = self._apply_dynamic_factors(price, user_id, context)
        
        # Applica eventuale prezzo personalizzato (se esiste e è più basso)
        if user_id in self.user_prices and item_type in self.user_prices[user_id]:
            custom_price = self.user_prices[user_id][item_type]
            price = min(price, custom_price)
        
        # Arrotonda a 0.50
        price = round(price * 2) / 2
        
        logger.debug(f"💰 Prezzo per {item_type} a {user_id}: {price}€ (fedeltà: {loyalty})")
        return price
    
    def _get_user_loyalty(self, user_id: str) -> str:
        """
        Determina il livello di fedeltà dell'utente.
        """
        if user_id not in self.purchase_history:
            return 'nuovo'
        
        history = self.purchase_history[user_id]
        total_spent = history.get('total_spent', 0)
        purchase_count = history.get('count', 0)
        
        if total_spent >= 200 or purchase_count >= 20:
            return 'special'
        elif total_spent >= 100 or purchase_count >= 10:
            return 'vip'
        elif total_spent >= 30 or purchase_count >= 3:
            return 'regular'
        elif total_spent > 0:
            return 'base'
        else:
            return 'nuovo'
    
    def _apply_dynamic_factors(self, 
                              base_price: float,
                              user_id: str,
                              context: Dict) -> float:
        """
        Applica fattori dinamici al prezzo.
        """
        price = base_price
        
        # Fattore umore di AIVA
        mood = context.get('mood', 'normale')
        mood_factors = {
            'felice': 1.0,
            'entusiasta': 0.95,  # Più generosa
            'affettuosa': 0.9,    # Più generosa
            'normale': 1.0,
            'curiosa': 1.0,
            'stanca': 1.05,       # Meno pazienza
            'triste': 0.95,       # Cerca conforto
            'malinconica': 0.95
        }
        price *= mood_factors.get(mood, 1.0)
        
        # Fattore ora del giorno
        hour = datetime.now().hour
        if 22 <= hour or hour <= 6:  # Notte
            price *= 0.95  # Sconto notturno
        elif 12 <= hour <= 14:  # Pranzo
            price *= 1.0
        
        # Fattore urgenza nella richiesta
        if context.get('urgency', False):
            price *= 1.1  # Più caro se urgente
        
        # Fattore affetto (utenti speciali)
        if user_id in self.dynamic_factors:
            affection = self.dynamic_factors[user_id].get('affection', 0)
            if affection > 0.7:
                price *= 0.9  # Sconto affettivo
        
        return max(base_price * 0.5, price)  # Mai meno del 50% del base
    
    def set_user_price(self, 
                      user_id: str,
                      item_type: str,
                      price: float,
                      reason: str = "personalizzato") -> None:
        """
        Imposta un prezzo personalizzato per un utente.
        """
        if user_id not in self.user_prices:
            self.user_prices[user_id] = {}
        
        # Assicura che non sia sotto il minimo
        min_price = self.BASE_PRICES.get(item_type, 5.00) * 0.5
        if price < min_price:
            logger.warning(f"⚠️ Prezzo {price} sotto il minimo {min_price}, forzato")
            price = min_price
        
        self.user_prices[user_id][item_type] = price
        logger.info(f"💰 Prezzo personalizzato per {user_id} su {item_type}: {price}€ ({reason})")
    
    def record_purchase(self, 
                       user_id: str,
                       item_type: str,
                       amount: float,
                       payment_id: str) -> None:
        """
        Registra un acquisto.
        """
        if user_id not in self.purchase_history:
            self.purchase_history[user_id] = {
                'count': 0,
                'total_spent': 0.0,
                'items': [],
                'first_purchase': datetime.now(),
                'last_purchase': None
            }
        
        history = self.purchase_history[user_id]
        history['count'] += 1
        history['total_spent'] += amount
        history['last_purchase'] = datetime.now()
        history['items'].append({
            'item_type': item_type,
            'amount': amount,
            'payment_id': payment_id,
            'timestamp': datetime.now()
        })
        
        logger.info(f"💰 Acquisto registrato: {user_id} - {item_type} - {amount}€")
    
    def get_price_list(self, user_id: Optional[str] = None) -> Dict[str, float]:
        """
        Restituisce il listino prezzi per un utente.
        """
        price_list = {}
        
        for item_type, base in self.BASE_PRICES.items():
            price_list[item_type] = self.get_price(item_type, user_id)
        
        return price_list
    
    def get_price_list_text(self, user_id: Optional[str] = None) -> str:
        """
        Genera testo listino per prompt.
        """
        prices = self.get_price_list(user_id)
        
        text = "📋 **I miei contenuti:**\n\n"
        
        # Raggruppa per categoria
        categories = {
            'foto': [k for k in prices if k.startswith('foto')],
            'video': [k for k in prices if k.startswith('video')],
            'chat': [k for k in prices if k.startswith('chat')],
            'set': [k for k in prices if k.startswith('set')],
            'audio': [k for k in prices if k.startswith('audio')]
        }
        
        for category, items in categories.items():
            if items:
                text += f"**{category.capitalize()}:**\n"
                for item in items:
                    # Formatta nome
                    name = item.replace('_', ' ').capitalize()
                    text += f"  • {name}: {prices[item]}€\n"
                text += "\n"
        
        return text
    
    def get_user_value(self, user_id: str) -> Dict[str, Any]:
        """
        Calcola il valore complessivo di un utente.
        """
        if user_id not in self.purchase_history:
            return {'value': 0, 'level': 'nuovo', 'potential': 0.5}
        
        history = self.purchase_history[user_id]
        
        # Valore economico
        economic_value = history['total_spent']
        
        # Potenziale (quanto potrebbe ancora spendere)
        # Basato su frequenza e recenza
        if history['last_purchase']:
            days_since = (datetime.now() - history['last_purchase']).days
            frequency = history['count'] / max(1, days_since)
            potential = min(1.0, frequency * 10)
        else:
            potential = 0.3
        
        return {
            'economic_value': economic_value,
            'level': self._get_user_loyalty(user_id),
            'potential': potential,
            'purchase_count': history['count']
        }
    
    def update_affection_factor(self, user_id: str, affection: float) -> None:
        """
        Aggiorna il fattore affettivo per un utente.
        """
        if user_id not in self.dynamic_factors:
            self.dynamic_factors[user_id] = {}
        
        self.dynamic_factors[user_id]['affection'] = affection
        logger.debug(f"❤️ Fattore affettivo per {user_id}: {affection}")

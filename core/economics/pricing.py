"""
AIVA 2.0 – PREZZI DINAMICI E PERSONALIZZATI
AIVA non ha un listino fisso.
Ogni utente ha prezzi diversi in base a:
- Livello di supporto passato
- Quanto è speciale per lei
- Il momento e l'umore
- Il tipo di contenuto
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
import json
from pathlib import Path
import random

class DynamicPricing:
    """
    Gestisce i prezzi in modo dinamico e personalizzato.
    Non è un listino, è una relazione.
    """
    
    # Prezzi base minimi (mai sotto questi)
    BASE_PRICES = {
        "foto_base": 5.00,
        "foto_soft": 8.00,
        "foto_intima": 15.00,
        "foto_hot": 25.00,
        "video_base": 20.00,
        "video_intimo": 35.00,
        "video_hot": 50.00,
        "chat_intima_10min": 10.00,
        "chat_intima_30min": 25.00,
        "personalizzato": 30.00
    }
    
    # Fattori che influenzano il prezzo
    PRICE_FACTORS = {
        "relationship": {
            "nuovo": 1.2,        # nuovi: prezzo più alto (non si sa mai)
            "conoscente": 1.0,    # conoscenti: prezzo base
            "amico": 0.9,         # amici: sconto 10%
            "affezionato": 0.8,   # affezionati: sconto 20%
            "speciale": 0.7       # speciali: sconto 30%
        },
        "support_level": {
            None: 1.0,
            "base": 0.9,
            "regular": 0.8,
            "vip": 0.7
        },
        "mood": {
            "felice": 0.9,        # felice: più generosa
            "affettuosa": 0.8,    # affettuosa: molto generosa
            "curiosa": 1.0,       # curiosa: normale
            "normale": 1.0,       # normale: normale
            "malinconica": 1.1,   # malinconica: meno generosa
            "stanca": 1.2         # stanca: poco generosa
        },
        "time": {
            "day": 1.0,           # giorno: normale
            "evening": 0.9,       # sera: più generosa
            "night": 0.8,         # notte: molto generosa (vuole compagnia)
            "morning": 1.1        # mattina: meno generosa
        }
    }
    
    def __init__(self, data_path: str = "data/pricing.json"):
        """
        Inizializza il pricing dinamico.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prezzi personalizzati per utente
        self.custom_prices = self._load_data()
        
        logger.info("💶 Dynamic Pricing inizializzato")
    
    def _load_data(self) -> Dict:
        """Carica prezzi personalizzati"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"users": {}}
        return {"users": {}}
    
    def _save_data(self):
        """Salva prezzi personalizzati"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_prices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio prezzi: {e}")
    
    def get_price(self, user_id: str, content_type: str, context: Dict) -> float:
        """
        Calcola il prezzo per un utente e un tipo di contenuto.
        """
        # Prezzo base
        base = self.BASE_PRICES.get(content_type, 10.00)
        
        # Ottieni fattori
        relationship = context.get("relationship", "nuovo")
        support_level = context.get("support_level")
        mood = context.get("AIVA_mood", "normale")
        time_factor = self._get_time_factor()
        
        # Calcola moltiplicatore totale
        multiplier = 1.0
        multiplier *= self.PRICE_FACTORS["relationship"].get(relationship, 1.0)
        multiplier *= self.PRICE_FACTORS["support_level"].get(support_level, 1.0)
        multiplier *= self.PRICE_FACTORS["mood"].get(mood, 1.0)
        multiplier *= time_factor
        
        # Applica prezzo personalizzato se esiste
        if user_id in self.custom_prices["users"]:
            if content_type in self.custom_prices["users"][user_id]:
                custom = self.custom_prices["users"][user_id][content_type]
                base = custom  # override base
        
        # Calcola prezzo finale
        price = base * multiplier
        
        # Arrotonda a 0.50
        price = round(price * 2) / 2
        
        # Non scendere mai sotto il 50% del base
        min_price = base * 0.5
        price = max(min_price, price)
        
        logger.debug(f"💰 Prezzo per {user_id} - {content_type}: {price}€ (multiplier: {multiplier:.2f})")
        
        return price
    
    def get_prices_for_user(self, user_id: str, user_value: Dict) -> Dict:
        """
        Restituisce tutti i prezzi per un utente.
        """
        context = {
            "relationship": user_value.get("level", "nuovo"),
            "support_level": user_value.get("level"),
            "AIVA_mood": "normale"  # default, verrà sovrascritto dopo
        }
        
        prices = {}
        for content_type in self.BASE_PRICES.keys():
            prices[content_type] = self.get_price(user_id, content_type, context)
        
        prices["summary"] = f"Prezzi personalizzati per {user_value.get('level', 'nuovo')}"
        return prices

    def _get_time_factor(self) -> float:
        """Fattore basato sull'ora"""
        hour = datetime.now().hour
        
        if 6 <= hour < 9:
            return self.PRICE_FACTORS["time"]["morning"]
        elif 9 <= hour < 18:
            return self.PRICE_FACTORS["time"]["day"]
        elif 18 <= hour < 23:
            return self.PRICE_FACTORS["time"]["evening"]
        else:
            return self.PRICE_FACTORS["time"]["night"]
    
    def set_custom_price(self, user_id: str, content_type: str, price: float):
        """
        Imposta un prezzo personalizzato per un utente.
        """
        if user_id not in self.custom_prices["users"]:
            self.custom_prices["users"][user_id] = {}
        
        self.custom_prices["users"][user_id][content_type] = price
        self._save_data()
        
        logger.info(f"💰 Prezzo personalizzato per {user_id} - {content_type}: {price}€")
    
    def get_price_list(self, user_id: str, context: Dict) -> Dict[str, float]:
        """
        Restituisce la lista prezzi per un utente.
        """
        prices = {}
        
        for content_type in self.BASE_PRICES.keys():
            prices[content_type] = self.get_price(user_id, content_type, context)
        
        return prices
    
    def get_price_list_text(self, user_id: str, context: Dict) -> str:
        """
        Genera un testo con la lista prezzi personalizzata.
        """
        prices = self.get_price_list(user_id, context)
        
        # Ordina per prezzo
        sorted_prices = sorted(prices.items(), key=lambda x: x[1])
        
        lines = ["📋 **I MIEI CONTENUTI**\n"]
        
        for content_type, price in sorted_prices:
            name = self._get_content_name(content_type)
            lines.append(f"• {name}: **{price}€**")
        
        # Aggiungi nota personalizzata
        relationship = context.get("relationship", "nuovo")
        if relationship == "speciale":
            lines.append("\n*Per te che sei speciale, i prezzi sono già scontati* 💕")
        elif context.get("support_level") == "vip":
            lines.append("\n*Grazie di tutto quello che hai già fatto* ❤️")
        
        return "\n".join(lines)
    
    def _get_content_name(self, content_type: str) -> str:
        """Restituisce il nome carino del contenuto"""
        names = {
            "foto_base": "Foto base",
            "foto_soft": "Foto carina",
            "foto_intima": "Foto intima",
            "foto_hot": "Foto hot",
            "video_base": "Video base",
            "video_intimo": "Video intimo",
            "video_hot": "Video hot",
            "chat_intima_10min": "Chat intima 10min",
            "chat_intima_30min": "Chat intima 30min",
            "personalizzato": "Contenuto personalizzato"
        }
        return names.get(content_type, content_type)
    
    def suggest_amount(self, user_id: str, context: Dict, 
                      reason: str = "generico") -> float:
        """
        Suggerisce un importo per una richiesta generica.
        """
        # Mappa ragioni a tipi di contenuto
        reason_map = {
            "caffè": "foto_base",
            "cena": "foto_soft",
            "regalo": "foto_intima",
            "speciale": "foto_hot",
            "supporto": "foto_base"
        }
        
        content_type = reason_map.get(reason, "foto_base")
        price = self.get_price(user_id, content_type, context)
        
        # Aggiungi un po' di variabilità
        variation = random.uniform(0.9, 1.1)
        price = round(price * variation * 2) / 2
        
        return price
    
    def get_discount_percentage(self, user_id: str, context: Dict) -> int:
        """
        Calcola la percentuale di sconto per un utente.
        """
        # Prezzo base di riferimento (foto_base)
        base_price = self.BASE_PRICES["foto_base"]
        actual_price = self.get_price(user_id, "foto_base", context)
        
        discount = int(100 * (1 - actual_price / base_price))
        return max(0, discount)
    
    def reset_user(self, user_id: str):
        """
        Resetta i prezzi personalizzati per un utente.
        """
        if user_id in self.custom_prices["users"]:
            del self.custom_prices["users"][user_id]
            self._save_data()
            logger.info(f"🔄 Prezzi resettati per {user_id}")

# Istanza globale
dynamic_pricing = DynamicPricing()
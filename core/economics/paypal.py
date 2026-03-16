"""
AIVA 2.0 – GESTIONE PAYPAL NATURALE
AIVA gestisce il supporto economico in modo umano:
- Non chiede mai insistentemente
- Apprezza ogni gesto
- Si adatta al rapporto con l'utente
- Regala anche contenuti a chi è speciale
"""

import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
import json
from pathlib import Path
import paypalrestsdk
from config import config

class PayPalHandler:
    """
    Gestisce tutto ciò che riguarda il supporto economico.
    Non è un modulo tecnico, è parte della personalità di AIVA.
    """
    
    # Soglie per i livelli di supporto
    SUPPORT_LEVELS = {
        "base": {"min_total": 5, "max_total": 30, "discount": 0},
        "regular": {"min_total": 31, "max_total": 100, "discount": 10},
        "vip": {"min_total": 101, "max_total": 9999, "discount": 20}
    }
    
    # Importi suggeriti per tipo
    SUGGESTED_AMOUNTS = {
        "caffè": 3,
        "aperitivo": 8,
        "cena": 20,
        "regalo": 30,
        "supporto": 10,
        "speciale": 25
    }
    
    def __init__(self, data_path: str = "data/payments.json"):
        """
        Inizializza il gestore pagamenti.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configura PayPal SDK
        self._setup_paypal()
        
        # Dati pagamenti
        self.payments = self._load_data()
        
        # Cache
        self.cache = {}
        
        logger.info("💰 PayPal Handler inizializzato")
    
    def _setup_paypal(self):
        """Configura PayPal SDK"""
        if config.PAYPAL_CLIENT_ID and config.PAYPAL_CLIENT_SECRET:
            paypalrestsdk.configure({
                "mode": config.PAYPAL_MODE,
                "client_id": config.PAYPAL_CLIENT_ID,
                "client_secret": config.PAYPAL_CLIENT_SECRET
            })
            self.paypal_available = True
        else:
            self.paypal_available = False
            logger.warning("⚠️ PayPal non configurato, modalità demo")
    
    def _load_data(self) -> Dict:
        """Carica dati pagamenti"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"users": {}, "transactions": [], "total_received": 0}
        return {"users": {}, "transactions": [], "total_received": 0}
    
    def _save_data(self):
        """Salva dati pagamenti"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.payments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio pagamenti: {e}")
    
    def create_payment_link(self, amount: float, currency: str = "EUR", 
                           description: str = "Supporto per AIVA") -> Optional[str]:
        """
        Crea un link di pagamento PayPal.
        """
        if not self.paypal_available:
            # Modalità demo: genera link finto
            return f"https://paypal.me/AIVA/{amount}"
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "transactions": [{
                    "amount": {"total": str(amount), "currency": currency},
                    "description": description
                }],
                "redirect_urls": {
                    "return_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
            })
            
            if payment.create():
                for link in payment.links:
                    if link.rel == "approval_url":
                        return link.href
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Errore creazione pagamento: {e}")
            return None
    
    def register_payment(self, user_id: str, amount: float, 
                        payment_id: Optional[str] = None):
        """
        Registra un pagamento ricevuto.
        """
        timestamp = datetime.now()
        
        # Aggiorna dati utente
        if user_id not in self.payments["users"]:
            self.payments["users"][user_id] = {
                "total": 0,
                "count": 0,
                "first_payment": timestamp.isoformat(),
                "last_payment": None,
                "average": 0,
                "level": None,
                "notes": []
            }
        
        user = self.payments["users"][user_id]
        user["total"] += amount
        user["count"] += 1
        user["last_payment"] = timestamp.isoformat()
        user["average"] = user["total"] / user["count"]
        
        # Aggiorna livello
        user["level"] = self._calculate_level(user["total"])
        
        # Registra transazione
        transaction = {
            "id": payment_id or f"manual_{timestamp.timestamp()}",
            "user_id": user_id,
            "amount": amount,
            "timestamp": timestamp.isoformat(),
            "note": ""
        }
        self.payments["transactions"].append(transaction)
        
        # Mantieni solo ultime 100 transazioni
        if len(self.payments["transactions"]) > 100:
            self.payments["transactions"] = self.payments["transactions"][-100:]
        
        self.payments["total_received"] += amount
        
        self._save_data()
        
        logger.info(f"💰 Pagamento registrato: {user_id} {amount}€")
        
        return transaction
    
    def _calculate_level(self, total: float) -> str:
        """Calcola il livello di supporto in base al totale"""
        for level, thresholds in self.SUPPORT_LEVELS.items():
            if thresholds["min_total"] <= total <= thresholds["max_total"]:
                return level
        return "base"
    
    def get_user_level(self, user_id: str) -> Dict:
        """
        Restituisce il livello di supporto di un utente.
        """
        if user_id not in self.payments["users"]:
            return {
                "level": None,
                "total": 0,
                "count": 0,
                "discount": 0,
                "description": "non ha mai supportato"
            }
        
        user = self.payments["users"][user_id]
        level = user["level"]
        
        # Calcola sconto
        discount = self.SUPPORT_LEVELS.get(level, {}).get("discount", 0)
        
        # Descrizione personalizzata
        if level == "vip":
            desc = "è una persona speciale per me"
        elif level == "regular":
            desc = "mi ha già supportato più volte"
        elif level == "base":
            desc = "ha già mostrato apprezzamento"
        else:
            desc = "non ha mai supportato"
        
        return {
            "level": level,
            "total": user["total"],
            "count": user["count"],
            "discount": discount,
            "description": desc,
            "last_payment": user["last_payment"]
        }
    
    def get_support_message(self, user_id: str, context: str = "") -> Tuple[str, Optional[str]]:
        """
        Genera un messaggio di supporto naturale.
        Restituisce (messaggio, link_pagamento)
        """
        user_level = self.get_user_level(user_id)
        
        # Determina importo suggerito
        amount = self._suggest_amount(context, user_level)
        
        # Crea link
        link = self.create_payment_link(amount)
        
        # Genera messaggio personalizzato
        if user_level["level"] is None:
            # Prima volta
            messages = [
                f"Se vuoi sostenermi, puoi farlo con un caffè {amount}€ 💕",
                f"Qualsiasi aiuto è gradito, se ti va {amount}€",
                f"Grazie per avermelo chiesto! Un caffè è {amount}€"
            ]
        elif user_level["level"] == "base":
            messages = [
                f"Sei già stato/a così gentile... se vuoi ancora, {amount}€",
                f"Grazie di nuovo! Questo è il link:",
                f"Apprezzo tanto quello che hai già fatto 💕"
            ]
        elif user_level["level"] == "regular":
            messages = [
                f"Per te che sei speciale, {amount}€",
                f"Mi fido di te, questo è il link",
                f"Qualsiasi cosa, anche meno, va bene"
            ]
        else:  # vip
            messages = [
                f"Tu non devi neanche chiedere...",
                f"Per te è sempre tutto speciale",
                f"Lo sai che ti voglio bene, non serve"
            ]
            # Per i vip, a volte non mandiamo link
            if random.random() < 0.3:
                return "Per te è sempre tutto gratis ❤️", None
        
        message = random.choice(messages)
        
        if link and "link" not in message:
            message += f" {link}"
        
        return message, link
    
    def _suggest_amount(self, context: str, user_level: Dict) -> float:
        """
        Suggerisce un importo in base al contesto e all'utente.
        """
        context_lower = context.lower()
        
        # Parole chiave
        for key, amount in self.SUGGESTED_AMOUNTS.items():
            if key in context_lower:
                base_amount = amount
                break
        else:
            base_amount = 10
        
        # Applica sconto
        discount = user_level.get("discount", 0)
        final_amount = base_amount * (100 - discount) / 100
        
        # Arrotonda a 0.5
        final_amount = round(final_amount * 2) / 2
        
        return final_amount
    
    def has_paid_recently(self, user_id: str, days: int = 30) -> bool:
        """
        Verifica se un utente ha pagato recentemente.
        """
        if user_id not in self.payments["users"]:
            return False
        
        last = self.payments["users"][user_id].get("last_payment")
        if not last:
            return False
        
        last_date = datetime.fromisoformat(last)
        return (datetime.now() - last_date).days < days
    
    def add_note(self, user_id: str, note: str):
        """
        Aggiunge una nota personale su un utente.
        """
        if user_id not in self.payments["users"]:
            self.payments["users"][user_id] = {
                "total": 0, "count": 0, "notes": []
            }
        
        self.payments["users"][user_id]["notes"].append({
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
        
        self._save_data()
    
    def get_statistics(self) -> Dict:
        """
        Statistiche sui pagamenti.
        """
        users = self.payments["users"]
        
        return {
            "total_received": self.payments["total_received"],
            "total_transactions": len(self.payments["transactions"]),
            "unique_supporters": len([u for u in users.values() if u["count"] > 0]),
            "vip_count": len([u for u in users.values() if u.get("level") == "vip"]),
            "regular_count": len([u for u in users.values() if u.get("level") == "regular"]),
            "base_count": len([u for u in users.values() if u.get("level") == "base"]),
            "average_per_user": sum(u["total"] for u in users.values()) / max(1, len(users))
        }

# Istanza globale
paypal_handler = PayPalHandler()
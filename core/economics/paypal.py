"""
Integrazione PayPal per pagamenti reali
"""
import os
import paypalrestsdk
import random
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from loguru import logger
from urllib.parse import urlparse

class PayPalClient:
    """
    Client per API PayPal.
    Gestisce creazione pagamenti, esecuzione e verifica.
    """
    
    def __init__(self, 
                 mode: str = "sandbox",
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 webhook_url: Optional[str] = None):
        
        self.mode = mode
        self.client_id = client_id
        self.client_secret = client_secret
        self.webhook_url = webhook_url
        
        # Inizializza SDK
        if client_id and client_secret:
            paypalrestsdk.configure({
                "mode": mode,
                "client_id": client_id,
                "client_secret": client_secret
            })
            logger.info(f"💰 PayPal client inizializzato (modalità: {mode})")
        else:
            logger.warning("⚠️ PayPal non configurato, modalità fake attivata")
        
        # Database pagamenti (in memoria, in produzione usare DB)
        self.payments = {}
        self.user_payments = {}
    
    def create_payment(self,
                      amount: float,
                      currency: str = "EUR",
                      description: str = "Supporto per AIVA",
                      user_id: Optional[str] = None,
                      return_url: Optional[str] = None,
                      cancel_url: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Crea un pagamento PayPal.
        
        Args:
            amount: Importo
            currency: Valuta
            description: Descrizione
            user_id: ID utente (per tracciamento)
            return_url: URL di ritorno dopo pagamento
            cancel_url: URL di cancellazione
        
        Returns:
            (approval_url, payment_id) oppure (None, None) se errore
        """
        
        # Modalità fake per test
        if not self.client_id or not self.client_secret:
            return self._create_fake_payment(amount, currency, description, user_id)
        
        # URL di default
        if not return_url:
            return_url = "https://example.com/success"
        if not cancel_url:
            cancel_url = "https://example.com/cancel"
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(round(amount, 2)),
                        "currency": currency
                    },
                    "description": description
                }],
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                }
            })
            
            if payment.create():
                # Trova URL di approvazione
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                # Salva pagamento
                payment_id = payment.id
                self.payments[payment_id] = {
                    'id': payment_id,
                    'amount': amount,
                    'currency': currency,
                    'description': description,
                    'user_id': user_id,
                    'status': 'created',
                    'created_at': datetime.now(),
                    'payment_obj': payment
                }
                
                if user_id:
                    if user_id not in self.user_payments:
                        self.user_payments[user_id] = []
                    self.user_payments[user_id].append(payment_id)
                
                logger.info(f"💰 Pagamento creato: {payment_id} - {amount}€")
                return approval_url, payment_id
            else:
                logger.error(f"❌ Errore creazione pagamento: {payment.error}")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ Errore PayPal: {e}")
            return None, None
    
    def _create_fake_payment(self,
                           amount: float,
                           currency: str,
                           description: str,
                           user_id: Optional[str]) -> Tuple[str, str]:
        """
        Crea un pagamento fittizio per test.
        """
        fake_id = f"FAKE_{datetime.now().timestamp()}"
        fake_url = f"https://paypal.me/AIVA/{amount}"
        
        self.payments[fake_id] = {
            'id': fake_id,
            'amount': amount,
            'currency': currency,
            'description': description,
            'user_id': user_id,
            'status': 'created',
            'created_at': datetime.now(),
            'fake': True
        }
        
        if user_id:
            if user_id not in self.user_payments:
                self.user_payments[user_id] = []
            self.user_payments[user_id].append(fake_id)
        
        logger.info(f"💰 [FAKE] Pagamento creato: {fake_id} - {amount}€")
        return fake_url, fake_id
    
    def execute_payment(self, 
                       payment_id: str, 
                       payer_id: str) -> bool:
        """
        Esegue un pagamento dopo approvazione.
        """
        if payment_id not in self.payments:
            logger.error(f"❌ Pagamento non trovato: {payment_id}")
            return False
        
        payment_info = self.payments[payment_id]
        
        # Pagamento fake
        if payment_info.get('fake'):
            payment_info['status'] = 'completed'
            payment_info['completed_at'] = datetime.now()
            logger.info(f"💰 [FAKE] Pagamento completato: {payment_id}")
            return True
        
        # Pagamento reale
        try:
            payment = payment_info['payment_obj']
            if payment.execute({"payer_id": payer_id}):
                payment_info['status'] = 'completed'
                payment_info['completed_at'] = datetime.now()
                logger.info(f"💰 Pagamento completato: {payment_id}")
                return True
            else:
                logger.error(f"❌ Errore esecuzione pagamento: {payment.error}")
                return False
        except Exception as e:
            logger.error(f"❌ Errore esecuzione pagamento: {e}")
            return False
    
    def get_payment_status(self, payment_id: str) -> str:
        """
        Ottiene lo stato di un pagamento.
        """
        if payment_id not in self.payments:
            return 'not_found'
        
        payment = self.payments[payment_id]
        
        # Aggiorna stato per pagamenti reali
        if not payment.get('fake') and 'payment_obj' in payment:
            try:
                payment['payment_obj'].refresh()
                payment['status'] = payment['payment_obj'].status
            except:
                pass
        
        return payment['status']
    
    def get_user_payments(self, user_id: str) -> Dict[str, Any]:
        """
        Ottiene tutti i pagamenti di un utente.
        """
        if user_id not in self.user_payments:
            return {'payments': [], 'total': 0, 'count': 0}
        
        payment_ids = self.user_payments[user_id]
        payments = [self.payments[pid] for pid in payment_ids if pid in self.payments]
        
        completed = [p for p in payments if p.get('status') == 'completed']
        total = sum(p.get('amount', 0) for p in completed)
        
        return {
            'payments': payments,
            'completed': completed,
            'total': total,
            'count': len(completed)
        }
    
    def get_user_level(self, user_id: str) -> str:
        """
        Determina il livello di supporto dell'utente.
        """
        info = self.get_user_payments(user_id)
        total = info['total']
        
        if total >= 200:
            return 'special'
        elif total >= 100:
            return 'vip'
        elif total >= 30:
            return 'regular'
        elif total > 0:
            return 'base'
        else:
            return 'nuovo'

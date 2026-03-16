"""
Webhook per notifiche PayPal
"""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
import json
import hmac
import hashlib

class PayPalWebhook:
    """
    Gestisce le notifiche webhook da PayPal.
    """
    
    def __init__(self, paypal_client, pricing_manager, consciousness):
        self.paypal = paypal_client
        self.pricing = pricing_manager
        self.consciousness = consciousness
        self.webhook_id = None  # Da configurare
        
        logger.debug("🔔 PayPal Webhook inizializzato")
    
    async def handle_webhook(self, headers: Dict, body: bytes) -> Dict:
        """
        Gestisce una notifica webhook.
        
        Args:
            headers: Headers HTTP della richiesta
            body: Corpo della richiesta
        
        Returns:
            Risposta da inviare
        """
        # Verifica firma (in produzione)
        # if not self._verify_signature(headers, body):
        #     return {'status': 'error', 'message': 'Invalid signature'}
        
        try:
            data = json.loads(body.decode('utf-8'))
            event_type = data.get('event_type')
            
            logger.info(f"🔔 Webhook PayPal: {event_type}")
            
            if event_type == 'PAYMENT.SALE.COMPLETED':
                await self._handle_payment_completed(data)
            elif event_type == 'PAYMENT.SALE.DENIED':
                await self._handle_payment_denied(data)
            elif event_type == 'PAYMENT.SALE.REFUNDED':
                await self._handle_payment_refunded(data)
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"❌ Errore webhook: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _handle_payment_completed(self, data: Dict) -> None:
        """
        Gestisce pagamento completato.
        """
        resource = data.get('resource', {})
        payment_id = resource.get('parent_payment')
        amount = float(resource.get('amount', {}).get('total', 0))
        
        # Trova utente associato
        user_id = self._find_user_by_payment(payment_id)
        
        if user_id:
            # Registra acquisto
            self.pricing.record_purchase(
                user_id=user_id,
                item_type='supporto',
                amount=amount,
                payment_id=payment_id
            )
            
            # Notifica coscienza (per reazione emotiva)
            if self.consciousness:
                await self.consciousness.receive_payment_notification(
                    user_id=user_id,
                    amount=amount
                )
            
            logger.info(f"💰 Pagamento {amount}€ completato per {user_id}")
    
    async def _handle_payment_denied(self, data: Dict) -> None:
        """
        Gestisce pagamento rifiutato.
        """
        resource = data.get('resource', {})
        payment_id = resource.get('parent_payment')
        
        logger.warning(f"⚠️ Pagamento rifiutato: {payment_id}")
    
    async def _handle_payment_refunded(self, data: Dict) -> None:
        """
        Gestisce pagamento rimborsato.
        """
        resource = data.get('resource', {})
        payment_id = resource.get('parent_payment')
        amount = float(resource.get('amount', {}).get('total', 0))
        
        logger.warning(f"⚠️ Rimborso di {amount}€ per {payment_id}")
    
    def _find_user_by_payment(self, payment_id: str) -> Optional[str]:
        """
        Trova l'utente associato a un pagamento.
        """
        if payment_id in self.paypal.payments:
            return self.paypal.payments[payment_id].get('user_id')
        return None
    
    def _verify_signature(self, headers: Dict, body: bytes) -> bool:
        """
        Verifica la firma del webhook (implementazione base).
        """
        # In produzione, usare la libreria ufficiale PayPal
        # https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature
        return True

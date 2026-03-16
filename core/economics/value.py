"""
Valore dell'utente: combinazione di supporto economico e affettivo
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

class UserValue:
    """
    Calcola il valore complessivo di un utente.
    Non solo economico, ma anche affettivo, di fedeltà, di potenziale.
    """
    
    def __init__(self, pricing_manager, paypal_client):
        self.pricing = pricing_manager
        self.paypal = paypal_client
        
        # Memoria affettiva
        self.affection_scores = {}  # user_id -> score
        self.interaction_quality = {}  # user_id -> media qualità
        
        logger.debug("📊 Value Manager inizializzato")
    
    def calculate_total_value(self, user_id: str) -> Dict[str, Any]:
        """
        Calcola il valore totale di un utente.
        """
        # Valore economico
        economic = self._calculate_economic_value(user_id)
        
        # Valore affettivo
        affective = self._calculate_affective_value(user_id)
        
        # Valore di fedeltà
        loyalty = self._calculate_loyalty_value(user_id)
        
        # Valore potenziale
        potential = self._calculate_potential_value(user_id)
        
        # Valore totale (combinazione)
        total = (
            economic['weighted'] * 0.4 +
            affective * 0.3 +
            loyalty * 0.2 +
            potential * 0.1
        )
        
        return {
            'total': round(total, 2),
            'economic': economic,
            'affective': affective,
            'loyalty': loyalty,
            'potential': potential,
            'level': self._get_level_from_value(total)
        }
    
    def _calculate_economic_value(self, user_id: str) -> Dict[str, float]:
        """
        Calcola il valore economico.
        """
        payments = self.paypal.get_user_payments(user_id)
        total = payments['total']
        
        # Valore assoluto (normalizzato)
        if total >= 200:
            absolute = 1.0
        elif total >= 100:
            absolute = 0.8
        elif total >= 50:
            absolute = 0.6
        elif total >= 20:
            absolute = 0.4
        elif total > 0:
            absolute = 0.2
        else:
            absolute = 0.0
        
        # Valore pesato (recency)
        weighted = absolute
        if payments['completed']:
            last = payments['completed'][-1]
            if 'completed_at' in last:
                days_since = (datetime.now() - last['completed_at']).days
                if days_since > 90:
                    weighted *= 0.5
                elif days_since > 30:
                    weighted *= 0.8
        
        return {
            'absolute': absolute,
            'weighted': weighted,
            'total': total
        }
    
    def _calculate_affective_value(self, user_id: str) -> float:
        """
        Calcola il valore affettivo.
        """
        base = self.affection_scores.get(user_id, 0.5)
        
        # Bonus per interazioni di qualità
        quality = self.interaction_quality.get(user_id, 0.5)
        
        return (base + quality) / 2
    
    def _calculate_loyalty_value(self, user_id: str) -> float:
        """
        Calcola il valore di fedeltà.
        """
        payments = self.paypal.get_user_payments(user_id)
        count = payments['count']
        
        if count >= 20:
            return 1.0
        elif count >= 10:
            return 0.8
        elif count >= 5:
            return 0.6
        elif count >= 2:
            return 0.4
        elif count >= 1:
            return 0.2
        else:
            return 0.0
    
    def _calculate_potential_value(self, user_id: str) -> float:
        """
        Calcola il valore potenziale futuro.
        """
        payments = self.paypal.get_user_payments(user_id)
        
        # Recency
        if payments['completed']:
            last = payments['completed'][-1]
            if 'completed_at' in last:
                days_since = (datetime.now() - last['completed_at']).days
                if days_since < 7:
                    recency = 1.0
                elif days_since < 30:
                    recency = 0.7
                elif days_since < 90:
                    recency = 0.4
                else:
                    recency = 0.2
            else:
                recency = 0.5
        else:
            recency = 0.3
        
        # Frequenza
        if payments['count'] > 5:
            frequency = 1.0
        elif payments['count'] > 2:
            frequency = 0.7
        elif payments['count'] > 0:
            frequency = 0.4
        else:
            frequency = 0.2
        
        # Trend (se sta aumentando)
        trend = 0.5  # Default
        
        return (recency + frequency + trend) / 3
    
    def _get_level_from_value(self, value: float) -> str:
        """
        Converte valore in livello.
        """
        if value >= 0.8:
            return 'special'
        elif value >= 0.6:
            return 'vip'
        elif value >= 0.4:
            return 'regular'
        elif value >= 0.2:
            return 'base'
        else:
            return 'nuovo'
    
    def update_affection(self, user_id: str, delta: float) -> None:
        """
        Aggiorna il punteggio affettivo.
        """
        current = self.affection_scores.get(user_id, 0.5)
        new = max(0.0, min(1.0, current + delta))
        self.affection_scores[user_id] = new
        
        logger.debug(f"❤️ Affection per {user_id}: {current:.2f} → {new:.2f}")
    
    def update_interaction_quality(self, 
                                  user_id: str, 
                                  sentiment: float,
                                  engagement: float) -> None:
        """
        Aggiorna la qualità delle interazioni.
        """
        current = self.interaction_quality.get(user_id, 0.5)
        
        # Media mobile
        new = current * 0.7 + ((sentiment + engagement) / 2) * 0.3
        self.interaction_quality[user_id] = new

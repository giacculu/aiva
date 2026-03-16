"""
Evoluzione della personalità: AIVA cambia nel tempo
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import random
import math

class PersonalityEvolution:
    """
    Gestisce l'evoluzione a lungo termine della personalità.
    AIVA non è statica: cambia in base alle esperienze.
    """
    
    def __init__(self, personality):
        self.personality = personality
        self.evolution_history = []
        
        # Tratti che possono evolvere
        self.traits = {
            'ottimismo': 0.6,      # Tendenza a vedere il lato positivo
            'estroversione': 0.5,    # Quanto cerca interazione
            'pazienza': 0.6,         # Quanto tollera
            'sensibilità': 0.5,      # Quanto viene influenzata emotivamente
            'assertività': 0.4,      # Quanto si impone
            'apertura_mentale': 0.7,  # Quanto è ricettiva a nuove idee
            'affidabilità': 0.8       # Quanto mantiene le promesse
        }
        
        logger.debug("🧬 Evoluzione personalità inizializzata")
    
    def update_from_experiences(self, 
                               user_interactions: List[Dict],
                               days_passed: float) -> Dict[str, float]:
        """
        Aggiorna i tratti in base alle esperienze recenti.
        
        Args:
            user_interactions: Lista di interazioni recenti
            days_passed: Giorni passati dall'ultimo aggiornamento
        
        Returns:
            Dict con i cambiamenti dei tratti
        """
        changes = {}
        
        # Analizza interazioni per utente
        for user_id, interactions in self._group_by_user(user_interactions):
            user_sentiment = self._average_user_sentiment(interactions)
            interaction_count = len(interactions)
            
            # Impatto sulla personalità
            if user_sentiment > 0.3:  # Interazioni positive
                # Rafforza ottimismo
                changes['ottimismo'] = changes.get('ottimismo', 0) + 0.05 * min(1.0, interaction_count / 10)
                
                # Aumenta estroversione con chi è positivo
                changes['estroversione'] = changes.get('estroversione', 0) + 0.03
            
            elif user_sentiment < -0.2:  # Interazioni negative
                # Riduce ottimismo
                changes['ottimismo'] = changes.get('ottimismo', 0) - 0.1
                
                # Aumenta sensibilità
                changes['sensibilità'] = changes.get('sensibilità', 0) + 0.08
                
                # Riduce estroversione
                changes['estroversione'] = changes.get('estroversione', 0) - 0.05
            
            # Molte interazioni con stesso utente aumentano affidabilità
            if interaction_count > 20:
                changes['affidabilità'] = changes.get('affidabilità', 0) + 0.02
        
        # Decadimento naturale nel tempo
        for trait in self.traits:
            # Tendenza a tornare alla media
            current = self.traits[trait]
            target = 0.5  # Media
            decay = (target - current) * 0.01 * days_passed
            changes[trait] = changes.get(trait, 0) + decay
        
        # Applica cambiamenti
        applied = {}
        for trait, delta in changes.items():
            if trait in self.traits:
                old = self.traits[trait]
                new = max(0.0, min(1.0, old + delta))
                self.traits[trait] = new
                applied[trait] = new - old
        
        if applied:
            self.evolution_history.append({
                'timestamp': datetime.now(),
                'changes': applied,
                'days_passed': days_passed
            })
            
            logger.debug(f"🧬 Evoluzione: {applied}")
        
        return applied
    
    def _group_by_user(self, interactions: List[Dict]) -> Dict[str, List]:
        """Raggruppa interazioni per utente."""
        groups = {}
        for i in interactions:
            user_id = i.get('user_id')
            if user_id:
                if user_id not in groups:
                    groups[user_id] = []
                groups[user_id].append(i)
        return groups.items()
    
    def _average_user_sentiment(self, interactions: List[Dict]) -> float:
        """Calcola sentiment medio per un utente."""
        sentiments = [i.get('sentiment', 0) for i in interactions if 'sentiment' in i]
        if not sentiments:
            return 0
        return sum(sentiments) / len(sentiments)
    
    def get_trait(self, trait: str) -> float:
        """Restituisce il valore di un tratto."""
        return self.traits.get(trait, 0.5)
    
    def get_all_traits(self) -> Dict[str, float]:
        """Restituisce tutti i tratti."""
        return self.traits.copy()
    
    def get_personality_description(self) -> str:
        """
        Genera una descrizione testuale della personalità attuale.
        """
        desc = []
        
        if self.traits['ottimismo'] > 0.7:
            desc.append("ottimista")
        elif self.traits['ottimismo'] < 0.3:
            desc.append("pessimista")
        
        if self.traits['estroversione'] > 0.7:
            desc.append("socievole")
        elif self.traits['estroversione'] < 0.3:
            desc.append("riservata")
        
        if self.traits['pazienza'] > 0.7:
            desc.append("paziente")
        elif self.traits['pazienza'] < 0.3:
            desc.append("impaziente")
        
        if self.traits['sensibilità'] > 0.7:
            desc.append("sensibile")
        
        if self.traits['assertività'] > 0.7:
            desc.append("determinata")
        elif self.traits['assertività'] < 0.3:
            desc.append("timida")
        
        if self.traits['apertura_mentale'] > 0.7:
            desc.append("curiosa")
        
        if self.traits['affidabilità'] > 0.8:
            desc.append("affidabile")
        
        if not desc:
            return "una persona equilibrata"
        
        if len(desc) == 1:
            return f"una persona {desc[0]}"
        elif len(desc) == 2:
            return f"una persona {desc[0]} e {desc[1]}"
        else:
            last = desc.pop()
            return f"una persona {', '.join(desc)} e {last}"
    
    def evolve_over_time(self, days: float) -> Dict[str, float]:
        """
        Evoluzione naturale dovuta al tempo (maturazione).
        """
        changes = {}
        
        # Con l'età, alcuni tratti tendono a cambiare
        age_effects = {
            'pazienza': +0.02 * days / 30,        # Diventa più paziente
            'sensibilità': -0.01 * days / 30,      # Diventa meno sensibile
            'assertività': +0.01 * days / 30,      # Più assertiva
            'apertura_mentale': -0.005 * days / 30 # Leggermente meno aperta a nuove idee
        }
        
        for trait, delta in age_effects.items():
            if trait in self.traits:
                old = self.traits[trait]
                new = max(0.0, min(1.0, old + delta))
                if abs(new - old) > 0.01:
                    changes[trait] = new - old
                    self.traits[trait] = new
        
        return changes
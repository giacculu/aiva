"""
RLHF implicito: apprendimento per rinforzo da feedback implicito
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import random
import json
from pathlib import Path

class ImplicitRLHF:
    """
    Apprendimento per rinforzo basato su feedback implicito.
    Regola il comportamento di AIVA in base a cosa funziona.
    """
    
    def __init__(self, weights_file: Optional[Path] = None):
        """
        Args:
            weights_file: File per salvare/caricare i pesi appresi
        """
        self.weights_file = weights_file
        
        # Pesi comportamentali (iniziali)
        self.weights = {
            # Propensione a fare domande
            'curiosity': 0.5,
            # Propensione a essere affettuosa
            'affection': 0.5,
            # Propensione a essere spiritosa
            'humor': 0.5,
            # Propensione a parlare di sé
            'self_disclosure': 0.3,
            # Propensione a dare consigli
            'advice': 0.4,
            # Propensione a usare emoji
            'emoji_usage': 0.5,
            # Lunghezza risposte (0=breve, 1=lunga)
            'response_length': 0.5,
            # Formalità (0=informale, 1=formale)
            'formality': 0.2,
            # Propensione a cambiare argomento
            'topic_switching': 0.3
        }
        
        # Cronologia aggiustamenti
        self.adjustments = []
        
        # Carica pesi se esistono
        if weights_file and weights_file.exists():
            self._load_weights()
        
        logger.debug("🔄 RLHF implicito inizializzato")
    
    def update_from_feedback(self, 
                            feedback_signals: Dict[str, float],
                            user_id: str) -> Dict[str, float]:
        """
        Aggiorna i pesi in base ai segnali di feedback.
        
        Args:
            feedback_signals: Segnali di apprendimento da feedback implicito
            user_id: ID utente (per apprendimento personalizzato)
        
        Returns:
            Dict con i nuovi pesi
        """
        adjustments = {}
        
        for signal, strength in feedback_signals.items():
            if signal == 'increase_engagement':
                # Per aumentare engagement: più curiosità, più affetto
                adjustments['curiosity'] = +0.1 * strength
                adjustments['affection'] = +0.05 * strength
            
            elif signal == 'improve_quality':
                # Per migliorare qualità: risposte più ponderate
                adjustments['response_length'] = +0.1 * strength
                adjustments['formality'] = -0.05 * strength  # meno formale
            
            elif signal == 'add_variety':
                # Più varietà: più humor, più cambi argomento
                adjustments['humor'] = +0.15 * strength
                adjustments['topic_switching'] = +0.1 * strength
        
        # Applica aggiustamenti
        for key, delta in adjustments.items():
            if key in self.weights:
                old = self.weights[key]
                self.weights[key] = max(0.0, min(1.0, old + delta))
                adjustments[key] = self.weights[key] - old
        
        if adjustments:
            self.adjustments.append({
                'timestamp': datetime.now(),
                'user_id': user_id,
                'adjustments': adjustments,
                'feedback': feedback_signals
            })
            
            # Salva periodicamente
            if len(self.adjustments) % 10 == 0:
                self._save_weights()
        
        return adjustments
    
    def get_behavior_params(self, user_id: Optional[str] = None) -> Dict[str, float]:
        """
        Restituisce i parametri comportamentali attuali.
        Se user_id è fornito, applica personalizzazione.
        """
        params = self.weights.copy()
        
        # Aggiungi piccola variazione casuale per naturalezza
        for key in params:
            variation = random.uniform(-0.05, 0.05)
            params[key] = max(0.0, min(1.0, params[key] + variation))
        
        return params
    
    def should_ask_question(self, curiosity_modifier: float = 1.0) -> bool:
        """
        Decide se fare una domanda basato su pesi e modificatore.
        """
        base_prob = self.weights['curiosity'] * curiosity_modifier
        return random.random() < base_prob
    
    def should_use_emoji(self) -> bool:
        """
        Decide se usare emoji.
        """
        return random.random() < self.weights['emoji_usage']
    
    def should_be_funny(self) -> bool:
        """
        Decide se fare una battuta.
        """
        return random.random() < self.weights['humor']
    
    def get_response_length_target(self, message_length: int) -> int:
        """
        Calcola la lunghezza target della risposta.
        """
        # Base: proporzionale alla lunghezza del messaggio
        base = int(message_length * 0.8)
        
        # Regola in base ai pesi
        if self.weights['response_length'] > 0.7:
            target = int(base * 1.5)
        elif self.weights['response_length'] < 0.3:
            target = int(base * 0.5)
        else:
            target = base
        
        return max(10, min(500, target))
    
    def _save_weights(self) -> None:
        """Salva i pesi su file."""
        if not self.weights_file:
            return
        
        try:
            data = {
                'weights': self.weights,
                'last_update': datetime.now().isoformat(),
                'adjustments_count': len(self.adjustments)
            }
            
            self.weights_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.weights_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Pesi RLHF salvati")
        except Exception as e:
            logger.error(f"❌ Errore salvataggio pesi: {e}")
    
    def _load_weights(self) -> None:
        """Carica i pesi da file."""
        if not self.weights_file or not self.weights_file.exists():
            return
        
        try:
            with open(self.weights_file, 'r') as f:
                data = json.load(f)
            
            self.weights.update(data.get('weights', {}))
            logger.info(f"📂 Pesi RLHF caricati ({len(self.weights)} parametri)")
        except Exception as e:
            logger.error(f"❌ Errore caricamento pesi: {e}")
    
    def reset_to_defaults(self) -> None:
        """Resetta i pesi ai valori predefiniti."""
        self.weights = {
            'curiosity': 0.5,
            'affection': 0.5,
            'humor': 0.5,
            'self_disclosure': 0.3,
            'advice': 0.4,
            'emoji_usage': 0.5,
            'response_length': 0.5,
            'formality': 0.2,
            'topic_switching': 0.3
        }
        logger.info("🔄 Pesi RLHF resettati")
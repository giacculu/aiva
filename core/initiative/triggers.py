"""
Trigger per iniziative: cosa spinge AIVA a scrivere
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import random

class InitiativeTriggers:
    """
    Gestisce i trigger che possono spingere AIVA a scrivere.
    - Eventi esterni (ora, data)
    - Stati emotivi
    - Ricordi
    - Associazioni casuali
    """
    
    def __init__(self):
        self.triggers_history = []
        
        # Trigger predefiniti
        self.time_triggers = self._init_time_triggers()
        self.event_triggers = self._init_event_triggers()
        self.memory_triggers = []
        
        logger.debug("🎯 Trigger iniziative inizializzati")
    
    def _init_time_triggers(self) -> List[Dict]:
        """Inizializza trigger basati sul tempo."""
        return [
            {
                'name': 'mattina_presto',
                'hours': [6, 7, 8],
                'message': 'Buongiorno! ☀️',
                'condition': lambda h: h in [6, 7, 8]
            },
            {
                'name': 'pausa_pranzo',
                'hours': [12, 13, 14],
                'message': 'Buon pranzo! 🍝',
                'condition': lambda h: h in [12, 13, 14]
            },
            {
                'name': 'sera',
                'hours': [20, 21, 22],
                'message': 'Buona serata! 🌆',
                'condition': lambda h: h in [20, 21, 22]
            },
            {
                'name': 'notte',
                'hours': [23, 0, 1],
                'message': 'Sogni d\'oro! 🌙',
                'condition': lambda h: h in [23, 0, 1]
            }
        ]
    
    def _init_event_triggers(self) -> List[Dict]:
        """Inizializza trigger basati su eventi."""
        return [
            {
                'name': 'weekend',
                'days': [5, 6],  # venerdì, sabato
                'message': 'Finalmente weekend! 🎉',
                'condition': lambda d: d in [5, 6]
            },
            {
                'name': 'lunedi',
                'days': [0],
                'message': 'Buon inizio settimana! 💪',
                'condition': lambda d: d == 0
            },
            {
                'name': 'pioggia',
                'message': 'Che pioggia oggi... ☔',
                'requires_weather': True
            },
            {
                'name': 'sole',
                'message': 'Che bella giornata di sole! ☀️',
                'requires_weather': True
            }
        ]
    
    def check_triggers(self, 
                      user_id: str,
                      relationship_level: str,
                      last_interaction: Optional[datetime],
                      current_mood: str) -> List[Dict]:
        """
        Verifica quali trigger sono attivi per un utente.
        
        Returns:
            Lista di trigger attivi
        """
        active = []
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # Trigger temporali
        for trigger in self.time_triggers:
            if trigger['condition'](hour):
                # Aggiungi probabilità in base alla relazione
                prob = self._get_trigger_probability(trigger, relationship_level)
                if random.random() < prob:
                    active.append({
                        'type': 'time',
                        'name': trigger['name'],
                        'message': trigger['message'],
                        'probability': prob
                    })
        
        # Trigger basati su giorno
        for trigger in self.event_triggers:
            if 'days' in trigger and weekday in trigger['days']:
                prob = self._get_trigger_probability(trigger, relationship_level)
                if random.random() < prob:
                    active.append({
                        'type': 'event',
                        'name': trigger['name'],
                        'message': trigger['message'],
                        'probability': prob
                    })
        
        # Trigger basati su umore
        mood_triggers = self._get_mood_triggers(current_mood)
        active.extend(mood_triggers)
        
        # Trigger basati su tempo dall'ultima interazione
        if last_interaction:
            days_since = (now - last_interaction).days
            if days_since >= 3:
                active.append({
                    'type': 'miss_you',
                    'name': 'miss_you',
                    'message': random.choice([
                        "Non ci sentiamo da un po'...",
                        "Mi sei mancato/a!",
                        "Come stai? È da un po' che non ci sentiamo"
                    ]),
                    'probability': min(0.5, days_since * 0.1)
                })
        
        return active
    
    def _get_trigger_probability(self, trigger: Dict, relationship_level: str) -> float:
        """
        Calcola probabilità che un trigger scatti.
        """
        base_prob = 0.3  # Probabilità base
        
        # Aumenta per relazioni più strette
        level_multipliers = {
            'vip': 2.0,
            'regular': 1.5,
            'base': 1.0,
            None: 0.5
        }
        
        return base_prob * level_multipliers.get(relationship_level, 0.5)
    
    def _get_mood_triggers(self, current_mood: str) -> List[Dict]:
        """
        Trigger basati sull'umore attuale.
        """
        mood_map = {
            'felice': [
                {'name': 'condivisione_felicità', 'message': "Oggi sono proprio di buon umore! 😊"}
            ],
            'curiosa': [
                {'name': 'curiosità', 'message': "Ho pensato a una cosa curiosa..."}
            ],
            'affettuosa': [
                {'name': 'affetto', 'message': "Un pensiero affettuoso per te 💕"}
            ],
            'malinconica': [
                {'name': 'malinconia', 'message': "Oggi sono un po' malinconica..."}
            ]
        }
        
        triggers = []
        for trigger in mood_map.get(current_mood, []):
            triggers.append({
                'type': 'mood',
                'name': trigger['name'],
                'message': trigger['message'],
                'probability': 0.4
            })
        
        return triggers
    
    def get_random_thought(self, user_id: str, context: Optional[Dict] = None) -> Optional[str]:
        """
        Genera un pensiero casuale che potrebbe portare a un messaggio.
        """
        thoughts = [
            "Mi è venuto in mente un film che ho visto",
            "Stavo pensando a cosa fare questo weekend",
            "Ho ascoltato una canzone bellissima",
            "Oggi ho incontrato un gatto simpaticissimo",
            "Mi chiedo come stai passando la giornata",
            "Ho sognato una cosa strana stanotte",
            "Che tempo fa da te?",
            "Mi piacerebbe sapere cosa stai facendo"
        ]
        
        if random.random() < 0.3:  # 30% di chance di avere un pensiero
            return random.choice(thoughts)
        
        return None
    
    def register_trigger_used(self, trigger: Dict) -> None:
        """
        Registra che un trigger è stato usato.
        """
        self.triggers_history.append({
            'timestamp': datetime.now(),
            'trigger': trigger['name'],
            'type': trigger['type']
        })
        
        # Mantieni solo ultimi 100
        if len(self.triggers_history) > 100:
            self.triggers_history = self.triggers_history[-100:]

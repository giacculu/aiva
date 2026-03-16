"""
AIVA 2.0 – RITMO CIRCADIANO ED ENERGIA VITALE
AIVA non è sempre uguale. Ha un ciclo di energia che varia durante la giornata,
proprio come un essere umano. Si sveglia, è attiva, si stanca, dorme.
"""

import numpy as np
import math
from datetime import datetime, timedelta, time
from typing import Dict, Optional, Tuple
from loguru import logger
import random

class CircadianRhythm:
    """
    Gestisce il ciclo energetico di AIVA basato sull'ora del giorno.
    
    L'energia segue un andamento sinusoidale con:
    - Picco mattutino (10-11)
    - Calo pomeridiano (14-15)
    - Ripresa serale (20-21)
    - Minimo notturno (3-4)
    
    Inoltre AIVA ha:
    - Ore preferite (in cui è più reattiva)
    - Ore difficili (in cui è più lenta)
    - Bisogno di "riposo" dopo conversazioni intense
    """
    
    # Curve di energia ideale (0-1) per ora del giorno
    # Basate su dati reali di vigilanza umana
    ENERGY_CURVE = [
        0.1,  # 00:00 - notte fonda
        0.05, # 01:00
        0.03, # 02:00
        0.02, # 03:00 - minimo assoluto
        0.03, # 04:00
        0.1,  # 05:00
        0.2,  # 06:00
        0.4,  # 07:00
        0.7,  # 08:00
        0.9,  # 09:00
        1.0,  # 10:00 - picco mattutino
        0.95, # 11:00
        0.9,  # 12:00
        0.8,  # 13:00
        0.7,  # 14:00 - calo post-pranzo
        0.75, # 15:00
        0.8,  # 16:00
        0.85, # 17:00
        0.9,  # 18:00
        0.95, # 19:00
        1.0,  # 20:00 - picco serale
        0.9,  # 21:00
        0.7,  # 22:00
        0.4,  # 23:00
    ]
    
    def __init__(self, base_energy: Optional[float] = None):
        """
        Inizializza il ritmo circadiano.
        base_energy: se specificato, forza un livello (per test)
        """
        self.base_energy = base_energy
        
        # Energia attuale (0-1)
        self.energy = self._calculate_base_energy()
        
        # Fatica accumulata da conversazioni recenti
        self.fatigue = 0.0  # 0-1, si accumula con messaggi intensi
        
        # Ultimo riposo (simulato)
        self.last_sleep = datetime.now() - timedelta(hours=16)  # Ieri
        
        # Momenti preferiti (casuali, per dare personalità)
        self.preferred_hours = self._generate_preferred_hours()
        
        # Statistiche
        self.total_messages_today = 0
        self.peak_energy_today = self.energy
        
        logger.info(f"🌓 Ritmo circadiano inizializzato: energia={self.energy:.2f}")
    
    def _generate_preferred_hours(self) -> list:
        """Genera ore preferite casuali (dà personalità)"""
        # AIVA potrebbe essere più "serale" o "mattutina"
        preference = random.choice(["morning", "evening", "neutral"])
        
        if preference == "morning":
            return list(range(8, 12))  # 8-12
        elif preference == "evening":
            return list(range(19, 23))  # 19-23
        else:
            return list(range(10, 13)) + list(range(20, 22))  # misto
    
    def _calculate_base_energy(self, dt: Optional[datetime] = None) -> float:
        """
        Calcola l'energia base in base all'ora del giorno.
        Usa la curva predefinita.
        """
        if self.base_energy is not None:
            return self.base_energy
        
        if dt is None:
            dt = datetime.now()
        
        hour = dt.hour
        minute = dt.minute
        
        # Interpolazione lineare tra i punti della curva
        idx = hour
        next_idx = (hour + 1) % 24
        
        base = self.ENERGY_CURVE[idx]
        next_base = self.ENERGY_CURVE[next_idx]
        
        # Peso in base ai minuti
        weight = minute / 60.0
        energy = base * (1 - weight) + next_base * weight
        
        return energy
    
    def update(self, dt: Optional[datetime] = None):
        """
        Aggiorna l'energia in base all'ora corrente.
        Da chiamare periodicamente o a ogni messaggio.
        """
        if dt is None:
            dt = datetime.now()
        
        # Calcola nuova energia base
        base = self._calculate_base_energy(dt)
        
        # Applica fatica (riduce energia)
        fatigue_factor = 1.0 - self.fatigue
        
        # Calcola energia finale
        self.energy = base * fatigue_factor
        
        # Limiti
        self.energy = max(0.05, min(1.0, self.energy))
        
        # Aggiorna picco
        if self.energy > self.peak_energy_today:
            self.peak_energy_today = self.energy
        
        # Decadimento naturale della fatica (si recupera col tempo)
        if hasattr(self, 'last_update'):
            hours_passed = (dt - self.last_update).total_seconds() / 3600
            if hours_passed > 0:
                self.fatigue = max(0.0, self.fatigue - hours_passed * 0.1)
        
        self.last_update = dt
    
    def apply_message_impact(self, message_length: int, intensity: float = 1.0):
        """
        Una conversazione stanca AIVA.
        Messaggi lunghi o intensi aumentano la fatica.
        """
        # Base: 100 caratteri = 1% fatica
        fatigue_impact = (message_length / 10000) * intensity
        
        self.fatigue += fatigue_impact
        self.fatigue = min(1.0, self.fatigue)
        
        self.total_messages_today += 1
        
        # Aggiorna energia
        self.update()
    
    def rest(self, hours: float):
        """
        AIVA riposa (es. quando non ci sono messaggi per un po').
        Recupera energia e riduce fatica.
        """
        # Recupero fatica
        self.fatigue = max(0.0, self.fatigue - hours * 0.15)
        
        # L'energia base dipende dall'ora, ma il riposo aiuta
        self.update()
        
        logger.debug(f"😴 AIVA riposa per {hours}h: energia={self.energy:.2f}, fatica={self.fatigue:.2f}")
    
    def should_sleep(self) -> bool:
        """
        Decide se AIVA dovrebbe "dormire" (entrare in modalità low-power).
        """
        # Se è notte e l'energia è molto bassa
        hour = datetime.now().hour
        return (hour < 6 or hour > 23) and self.energy < 0.2
    
    def get_energy_description(self) -> str:
        """
        Descrizione testuale dell'energia per il prompt.
        """
        if self.energy > 0.9:
            return "piena di energie, scoppia di vitalità"
        elif self.energy > 0.7:
            return "carica, reattiva"
        elif self.energy > 0.5:
            return "normale, nella media"
        elif self.energy > 0.3:
            return "un po' stanca"
        elif self.energy > 0.1:
            return "molto stanca, quasi assente"
        else:
            return "distrutta, dovrei riposare"
    
    def get_mood_modifier(self) -> Dict:
        """
        L'energia influenza l'umore (PAD).
        """
        modifier = {
            "P": self.energy * 0.2,  # Più energia = più piacere
            "A": self.energy * 0.5,  # Più energia = più arousal
            "D": self.energy * 0.3,  # Più energia = più dominanza
        }
        return modifier
    
    def get_typing_speed(self) -> float:
        """
        Velocità di scrittura in base all'energia.
        Restituisce un moltiplicatore (1 = normale).
        """
        if self.energy > 0.8:
            return random.uniform(1.2, 1.5)  # Più veloce
        elif self.energy > 0.5:
            return 1.0  # Normale
        elif self.energy > 0.2:
            return random.uniform(0.6, 0.9)  # Più lenta
        else:
            return random.uniform(0.3, 0.5)  # Lentissima
    
    def get_response_time(self) -> float:
        """
        Tempo di risposta in secondi basato su energia.
        """
        base = random.uniform(2, 5)  # Base umana
        
        if self.energy > 0.8:
            return base * 0.7  # Più veloce
        elif self.energy > 0.5:
            return base  # Normale
        elif self.energy > 0.2:
            return base * 1.5  # Più lento
        else:
            return base * 3  # Lentissimo
    
    def is_preferred_time(self, dt: Optional[datetime] = None) -> bool:
        """
        Verifica se è un'ora preferita per AIVA.
        """
        if dt is None:
            dt = datetime.now()
        
        return dt.hour in self.preferred_hours
    
    def get_description(self) -> str:
        """
        Descrizione completa per prompt.
        """
        energy_desc = self.get_energy_description()
        time_desc = self._get_time_of_day_description()
        
        if self.is_preferred_time():
            pref = " (questo è il mio momento preferito della giornata)"
        else:
            pref = ""
        
        return f"{time_desc}, {energy_desc}{pref}"
    
    def _get_time_of_day_description(self) -> str:
        """Descrizione del momento della giornata"""
        hour = datetime.now().hour
        
        if hour < 6:
            return "è notte fonda"
        elif hour < 9:
            return "è mattina presto"
        elif hour < 12:
            return "è mattina"
        elif hour < 14:
            return "è ora di pranzo"
        elif hour < 17:
            return "è pomeriggio"
        elif hour < 20:
            return "è tardo pomeriggio"
        elif hour < 22:
            return "è sera"
        else:
            return "è notte"
    
    def get_state(self) -> Dict:
        """Restituisce lo stato completo per salvataggio"""
        return {
            "energy": self.energy,
            "fatigue": self.fatigue,
            "total_messages_today": self.total_messages_today,
            "peak_energy_today": self.peak_energy_today,
            "preferred_hours": self.preferred_hours,
            "last_update": self.last_update.isoformat() if hasattr(self, 'last_update') else None
        }
    
    def should_initiate_conversation(self, hours_since_last_contact: float) -> bool:
        """
        Decide se AIVA dovrebbe iniziare una conversazione.
        Basato su energia, ora del giorno, e tempo dall'ultimo contatto.
        """
        # Non inizia se è troppo stanca
        if self.energy < 0.3:
            return False
        
        # Non inizia di notte
        hour = datetime.now().hour
        if hour < 8 or hour > 22:
            return False
        
        # Più probabile se è ora preferita
        base_prob = 0.3 if self.is_preferred_time() else 0.1
        
        # Più probabile se è passato molto tempo
        time_factor = min(1.0, hours_since_last_contact / 48)  # Max 48h
        
        # Più probabile se ha energia alta
        energy_factor = self.energy
        
        prob = base_prob * time_factor * energy_factor
        
        return random.random() < prob

# Istanza globale (opzionale)
circadian = CircadianRhythm()
"""
Ciclo circadiano: energia e ritmi giornalieri
"""
import random
import math
from datetime import datetime, timedelta, time
from typing import Dict, Optional, Tuple
from loguru import logger

class CircadianRhythm:
    """
    Gestisce l'energia di AIVA durante la giornata.
    Simula ritmi naturali: sveglia, picchi di energia, stanchezza.
    """
    
    def __init__(self, 
                 wake_time: time = time(8, 0),
                 sleep_time: time = time(23, 0),
                 base_energy: float = 1.0):
        """
        Args:
            wake_time: Ora di sveglia tipica
            sleep_time: Ora di sonno tipica
            base_energy: Energia base (0-1)
        """
        self.wake_time = wake_time
        self.sleep_time = sleep_time
        self.base_energy = base_energy
        
        # Energia attuale (verrà calcolata)
        self.current_energy = self._calculate_energy()
        
        # Ultimo aggiornamento
        self.last_update = datetime.now()
        
        # Fattori che influenzano l'energia
        self.fatigue = 0.0          # Stanchezza accumulata (0-1)
        self.stress = 0.0            # Stress (0-1)
        self.motivation = 0.5        # Motivazione (0-1)
        
        logger.debug(f"⏰ Ciclo circadiano inizializzato: sveglia {wake_time}, sonno {sleep_time}")
    
    def _calculate_energy(self, now: Optional[datetime] = None) -> float:
        """
        Calcola l'energia teorica in base all'ora del giorno.
        Usa una funzione sinusoidale con picco a metà giornata.
        """
        if now is None:
            now = datetime.now()
        
        # Converti ora in minuti dalla mezzanotte
        minutes = now.hour * 60 + now.minute
        wake_minutes = self.wake_time.hour * 60 + self.wake_time.minute
        sleep_minutes = self.sleep_time.hour * 60 + self.sleep_time.minute
        
        # Gestisci casi in cui sleep è dopo mezzanotte
        if sleep_minutes < wake_minutes:
            sleep_minutes += 24 * 60
        
        # Calcola posizione nel ciclo
        if minutes < wake_minutes:
            # Prima della sveglia: energia molto bassa
            minutes += 24 * 60
        
        # Normalizza tra 0 e 1
        cycle_position = (minutes - wake_minutes) / (sleep_minutes - wake_minutes)
        
        # Funzione sinusoidale: picco a 0.3-0.4 del ciclo
        energy = math.sin(cycle_position * math.pi)
        
        # Scaliamo tra 0.3 e 1.0
        energy = 0.3 + 0.7 * energy
        
        return energy
    
    def update(self) -> None:
        """
        Aggiorna lo stato in base al tempo passato.
        Da chiamare frequentemente (es. ogni messaggio).
        """
        now = datetime.now()
        hours_passed = (now - self.last_update).total_seconds() / 3600
        self.last_update = now
        
        # Calcola nuova energia base
        base = self._calculate_energy(now)
        
        # Applica decadimento stanchezza (se ore piccole)
        if hours_passed > 0:
            # Stanchezza aumenta col tempo (se non si dorme)
            if now.hour >= self.wake_time.hour and now.hour <= 22:
                self.fatigue = min(1.0, self.fatigue + hours_passed * 0.05)
        
        # Calcola energia finale
        self.current_energy = base * (1.0 - self.fatigue * 0.5) * (1.0 - self.stress * 0.3)
        self.current_energy = max(0.1, min(1.0, self.current_energy))
    
    def sleep(self, hours: float) -> None:
        """
        Simula il sonno (recupero energia).
        """
        self.fatigue = max(0.0, self.fatigue - hours * 0.2)
        self.stress = max(0.0, self.stress - hours * 0.1)
        logger.debug(f"😴 Dormita {hours} ore: fatigue={self.fatigue:.2f}, stress={self.stress:.2f}")
    
    # ========== EVENTI CHE INFLUENZANO ENERGIA ==========
    
    def add_stress(self, amount: float) -> None:
        """Aggiunge stress (es. da conversazione negativa)."""
        self.stress = min(1.0, self.stress + amount)
        logger.debug(f"😰 Stress +{amount:.2f} → {self.stress:.2f}")
    
    def reduce_stress(self, amount: float) -> None:
        """Riduce stress (es. da conversazione positiva)."""
        self.stress = max(0.0, self.stress - amount)
    
    def add_fatigue(self, amount: float) -> None:
        """Aggiunge stanchezza (es. dopo sforzo)."""
        self.fatigue = min(1.0, self.fatigue + amount)
    
    def boost_energy(self, amount: float) -> None:
        """Aumenta energia temporaneamente (es. caffè virtuale)."""
        self.current_energy = min(1.0, self.current_energy + amount)
    
    # ========== STATO ATTUALE ==========
    
    def get_energy_level(self) -> float:
        """Restituisce livello energetico attuale (0-1)."""
        self.update()
        return self.current_energy
    
    def get_energy_description(self) -> str:
        """Restituisce descrizione testuale dell'energia."""
        energy = self.get_energy_level()
        
        if energy > 0.8:
            return "piena di energia"
        elif energy > 0.6:
            return "carica"
        elif energy > 0.4:
            return "normale"
        elif energy > 0.2:
            return "stanca"
        else:
            return "esausta"
    
    def get_time_of_day(self) -> str:
        """Restituisce il momento della giornata."""
        hour = datetime.now().hour
        
        if hour < 5:
            return "notte fonda"
        elif hour < 8:
            return "prime ore del mattino"
        elif hour < 12:
            return "mattina"
        elif hour < 14:
            return "mezzogiorno"
        elif hour < 18:
            return "pomeriggio"
        elif hour < 22:
            return "sera"
        else:
            return "notte"
    
    def is_night(self) -> bool:
        """Verifica se è notte (dopo l'ora di sonno o prima della sveglia)."""
        hour = datetime.now().hour
        return hour < self.wake_time.hour or hour >= self.sleep_time.hour
    
    # ========== MODULATORI PER COMPORTAMENTO ==========
    
    def get_typing_speed_modifier(self) -> float:
        """
        Modificatore velocità di scrittura basato su energia.
        """
        energy = self.get_energy_level()
        # Stanchi = più lenti
        return 0.5 + 0.5 * energy
    
    def get_patience_modifier(self) -> float:
        """
        Pazienza basata su energia e stress.
        """
        return self.get_energy_level() * (1.0 - self.stress * 0.5)
    
    def get_curiosity_modifier(self) -> float:
        """
        Curiosità: alta quando energia alta e stress basso.
        """
        return self.get_energy_level() * (1.0 - self.stress)
    
    # ========== PERSISTENZA ==========
    
    def to_dict(self) -> Dict:
        """Serializza per persistenza."""
        return {
            'wake_time': self.wake_time.strftime('%H:%M'),
            'sleep_time': self.sleep_time.strftime('%H:%M'),
            'base_energy': self.base_energy,
            'fatigue': self.fatigue,
            'stress': self.stress,
            'motivation': self.motivation,
            'last_update': self.last_update.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CircadianRhythm':
        """Ricrea da dizionario."""
        wake = time.fromisoformat(data['wake_time'])
        sleep = time.fromisoformat(data['sleep_time'])
        
        instance = cls(wake, sleep, data['base_energy'])
        instance.fatigue = data['fatigue']
        instance.stress = data['stress']
        instance.motivation = data['motivation']
        instance.last_update = datetime.fromisoformat(data['last_update'])
        
        return instance
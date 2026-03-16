"""
Scheduler per iniziative spontanee: quando AIVA decide di scrivere
"""
import asyncio
import random
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from loguru import logger

class InitiativeScheduler:
    """
    Programma i momenti in cui AIVA prende iniziativa.
    Decide quando scrivere spontaneamente in base a:
    - Ora del giorno
    - Umore
    - Ultima interazione con l'utente
    - Livello di relazione
    """
    
    def __init__(self):
        self.tasks = []
        self.running = False
        self.callback = None
        
        # Configurazione
        self.min_hours_between_initiatives = 4  # Minimo tra un'iniziativa e l'altra
        self.max_initiatives_per_day = 3         # Massimo al giorno
        
        # Storico
        self.initiative_history = []  # (timestamp, user_id)
        
        logger.debug("⏰ Scheduler iniziative inizializzato")
    
    def start(self, callback: Callable) -> None:
        """
        Avvia lo scheduler.
        
        Args:
            callback: Funzione da chiamare quando AIVA vuole scrivere
                     Deve accettare (user_id, reason)
        """
        self.callback = callback
        self.running = True
        logger.info("⏰ Scheduler iniziative avviato")
    
    async def run(self):
        """Loop principale dello scheduler."""
        while self.running:
            try:
                # Controlla ogni ora
                await asyncio.sleep(3600)
                await self._check_initiative_opportunities()
            except Exception as e:
                logger.error(f"❌ Errore scheduler: {e}")
    
    async def _check_initiative_opportunities(self) -> None:
        """Controlla se ci sono opportunità per iniziative."""
        if not self.callback:
            return
        
        # Limite giornaliero
        today = datetime.now().date()
        today_initiatives = [
            h for h in self.initiative_history 
            if h[0].date() == today
        ]
        
        if len(today_initiatives) >= self.max_initiatives_per_day:
            return
        
        # Questo metodo verrà implementato con accesso al database
        # per trovare utenti con cui interagire
        logger.debug("⏰ Controllo opportunità iniziative")
    
    def should_take_initiative(self, 
                              user_id: str,
                              last_interaction: Optional[datetime],
                              relationship_level: str,
                              current_mood: str,
                              hour: int) -> float:
        """
        Calcola la probabilità che AIVA prenda iniziativa con un utente.
        
        Returns:
            Probabilità (0-1)
        """
        probability = 0.0
        
        # Se non c'è mai stata interazione, bassa probabilità
        if not last_interaction:
            return 0.05  # 5% di chance per nuovi utenti
        
        # Calcola ore dall'ultima interazione
        hours_since = (datetime.now() - last_interaction).total_seconds() / 3600
        
        # Più tempo è passato, più probabilità
        time_factor = min(0.5, hours_since / 48)  # Max 0.5 dopo 48 ore
        probability += time_factor
        
        # Livello di relazione
        level_factors = {
            'vip': 0.3,
            'regular': 0.2,
            'base': 0.1,
            None: 0.05
        }
        probability += level_factors.get(relationship_level, 0.05)
        
        # Umore di AIVA
        mood_factors = {
            'felice': 0.2,
            'entusiasta': 0.3,
            'affettuosa': 0.2,
            'curiosa': 0.2,
            'normale': 0.1,
            'stanca': 0.0,
            'triste': 0.05,
            'arrabbiata': 0.0
        }
        probability += mood_factors.get(current_mood, 0.1)
        
        # Ora del giorno (più probabile di giorno)
        if 9 <= hour <= 22:
            probability += 0.1
        else:
            probability -= 0.1
        
        return max(0.0, min(0.8, probability))
    
    def get_initiative_reason(self, 
                             user_id: str,
                             relationship_level: str,
                             current_mood: str) -> str:
        """
        Genera una ragione per l'iniziativa.
        """
        reasons = []
        
        # Ragioni basate sulla relazione
        if relationship_level == 'vip':
            reasons.extend([
                "pensavo a te",
                "mi sei mancato",
                "spero tu stia bene"
            ])
        elif relationship_level == 'regular':
            reasons.extend([
                "non ci sentiamo da un po'",
                "come stai?",
                "ti stavo pensando"
            ])
        else:
            reasons.extend([
                "ciao!",
                "come va?",
                "tutto bene?"
            ])
        
        # Ragioni basate sull'umore
        mood_reasons = {
            'felice': ["ho voglia di chiacchierare", "sono di buon umore"],
            'curiosa': ["ho una curiosità", "vorrei chiederti una cosa"],
            'affettuosa': ["un pensiero affettuoso", "ti volevo salutare"]
        }
        
        reasons.extend(mood_reasons.get(current_mood, []))
        
        return random.choice(reasons)
    
    def register_initiative(self, user_id: str) -> None:
        """
        Registra un'iniziativa presa.
        """
        self.initiative_history.append((datetime.now(), user_id))
        
        # Mantieni solo ultimi 100
        if len(self.initiative_history) > 100:
            self.initiative_history = self.initiative_history[-100:]
    
    def stop(self) -> None:
        """Ferma lo scheduler."""
        self.running = False
        logger.info("⏰ Scheduler iniziative fermato")
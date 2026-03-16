"""
Rate limiter per API Gemini
"""
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

class RateLimiter:
    """
    Limita le chiamate alle API per evitare di superare le quote.
    """
    
    def __init__(self, max_calls: int = 60, period: int = 60):
        """
        Args:
            max_calls: Numero massimo di chiamate nel periodo
            period: Periodo in secondi
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = asyncio.Lock()
        
        logger.debug(f"⏱️ Rate limiter inizializzato: {max_calls} chiamate/{period}s")
    
    async def acquire(self) -> bool:
        """
        Acquisisce un permesso per chiamare l'API.
        
        Returns:
            True se si può procedere, False se si deve attendere
        """
        async with self.lock:
            now = time.time()
            
            # Rimuovi chiamate vecchie
            self.calls = [t for t in self.calls if t > now - self.period]
            
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            # Calcola tempo di attesa
            oldest = min(self.calls)
            wait_time = oldest + self.period - now
            
            logger.warning(f"⏳ Rate limit raggiunto, attesa {wait_time:.1f}s")
            
            # Attendi
            await asyncio.sleep(wait_time)
            
            # Riprova
            return await self.acquire()
    
    async def __aenter__(self):
        """Context manager per uso with."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

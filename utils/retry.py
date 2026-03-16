"""
Retry decorator per operazioni che possono fallire
"""
import asyncio
import functools
from typing import Type, Union, Tuple, Optional, Callable
from loguru import logger

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    logger_msg: Optional[str] = None
):
    """
    Decorator per retry con backoff esponenziale.
    
    Args:
        max_attempts: Numero massimo di tentativi
        delay: Ritardo iniziale in secondi
        backoff: Fattore di backoff
        exceptions: Eccezioni da catturare
        logger_msg: Messaggio per log (opzionale)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        break
                    
                    msg = logger_msg or f"Tentativo {attempt}/{max_attempts} fallito"
                    logger.warning(f"⚠️ {msg}: {e}. Nuovo tentativo tra {current_delay:.1f}s")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # Ultimo errore
            logger.error(f"❌ Tutti i {max_attempts} tentativi falliti: {last_exception}")
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        break
                    
                    msg = logger_msg or f"Tentativo {attempt}/{max_attempts} fallito"
                    logger.warning(f"⚠️ {msg}: {e}. Nuovo tentativo tra {current_delay:.1f}s")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            logger.error(f"❌ Tutti i {max_attempts} tentativi falliti: {last_exception}")
            raise last_exception
        
        # Scegli wrapper appropriato in base al tipo di funzione
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

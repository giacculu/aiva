"""
Logger configurabile per AIVA AI
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

def setup_logger(
    log_file: Optional[Path] = None,
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "1 month",
    serialize: bool = False
) -> None:
    """
    Configura il logger secondo le specifiche.
    
    Args:
        log_file: Percorso del file di log (se None, solo console)
        level: Livello di logging (DEBUG, INFO, WARNING, ERROR)
        rotation: Quando ruotare il file (es. "10 MB", "1 day")
        retention: Quanto tenere i log vecchi
        serialize: Se True, produce log in formato JSON
    """
    # Rimuovi handlers predefiniti
    logger.remove()
    
    # Formato dettagliato per debug
    detailed_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Formato semplice per console (più leggibile)
    simple_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )
    
    # Aggiungi console handler
    logger.add(
        sys.stdout,
        format=simple_format,
        level=level,
        colorize=True
    )
    
    # Aggiungi file handler se specificato
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        if serialize:
            logger.add(
                log_file,
                format="{time} | {level} | {name} | {function} | {line} | {message}",
                level=level,
                rotation=rotation,
                retention=retention,
                serialize=True
            )
        else:
            logger.add(
                log_file,
                format=detailed_format,
                level=level,
                rotation=rotation,
                retention=retention,
                encoding="utf-8"
            )
    
    # Log iniziale
    logger.info("✅ Logger configurato (livello: {})", level)


# Istanza preconfigurata (da importare negli altri moduli)
# La configurazione effettiva verrà fatta in run.py
log = logger
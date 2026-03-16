"""
AIVA 2.0 – LOGGER AVANZATO
Configurazione logging con loguru.
Supporta:
- Colori nella console
- Rotazione file
- Livelli personalizzati
- Tracciamento performance
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Any, Optional

class AIVALogger:
    """
    Logger personalizzato per AIVA.
    """
    
    # Livelli personalizzati
    LEVELS = {
        "TRACE": 5,
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    def __init__(self, log_dir: str = "logs", 
                 log_file: str = "AIVA.log",
                 rotation: str = "10 MB",
                 retention: str = "30 days"):
        """
        Inizializza il logger.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / log_file
        self.rotation = rotation
        self.retention = retention
        
        self._configure()
        
        # Statistiche
        self.stats = {
            "start_time": datetime.now(),
            "message_count": 0,
            "error_count": 0,
            "warning_count": 0
        }
        
        logger.info("📋 Logger inizializzato")
    
    def _configure(self):
        """
        Configura loguru.
        """
        # Rimuovi default handler
        logger.remove()
        
        # Console handler (colorato)
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level:8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
        
        # File handler (tutto)
        logger.add(
            str(self.log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:8} | {name}:{function}:{line} - {message}",
            level="TRACE",
            rotation=self.rotation,
            retention=self.retention,
            compression="zip"
        )
        
        # File separato per errori
        logger.add(
            str(self.log_dir / "errors.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation=self.rotation,
            retention=self.retention
        )
        
        # File per performance
        logger.add(
            str(self.log_dir / "performance.log"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            filter=lambda record: record["extra"].get("type") == "performance",
            rotation=self.rotation
        )
    
    def log_performance(self, operation: str, duration: float, 
                       metadata: Optional[Dict] = None):
        """
        Logga metriche di performance.
        """
        data = {
            "operation": operation,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            data.update(metadata)
        
        logger.bind(type="performance").info(json.dumps(data))
    
    def log_interaction(self, user_id: str, message: str, 
                       response: str, duration: float):
        """
        Logga un'interazione utente.
        """
        self.stats["message_count"] += 1
        
        data = {
            "user_id": user_id,
            "message": message[:100],
            "response_length": len(response),
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.bind(type="interaction").info(json.dumps(data))
    
    def log_error(self, error: Exception, context: Dict = None):
        """
        Logga un errore con contesto.
        """
        self.stats["error_count"] += 1
        
        data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        logger.error(f"❌ {error}")
        logger.bind(type="error").error(json.dumps(data))
    
    def log_warning(self, message: str, context: Dict = None):
        """
        Logga un warning.
        """
        self.stats["warning_count"] += 1
        
        data = {
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        logger.warning(f"⚠️ {message}")
        logger.bind(type="warning").warning(json.dumps(data))
    
    def get_stats(self) -> Dict:
        """
        Restituisce statistiche del logger.
        """
        uptime = datetime.now() - self.stats["start_time"]
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime).split('.')[0],
            "message_count": self.stats["message_count"],
            "error_count": self.stats["error_count"],
            "warning_count": self.stats["warning_count"],
            "errors_per_hour": self.stats["error_count"] / (uptime.total_seconds() / 3600) if uptime.total_seconds() > 0 else 0
        }

# Istanza globale
AIVA_logger = AIVALogger()

# Esporta logger configurato
__all__ = ["logger", "AIVA_logger"]
"""
Health checks per monitorare lo stato di AIVA
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil
import platform
from loguru import logger

class HealthChecker:
    """
    Verifica la salute di tutti i componenti di AIVA.
    """
    
    def __init__(self, consciousness, paypal_client, media_manager, db_sqlite, chroma_client):
        self.consciousness = consciousness
        self.paypal = paypal_client
        self.media = media_manager
        self.db_sqlite = db_sqlite
        self.chroma = chroma_client
        
        self.start_time = datetime.now()
        self.last_check = None
        
        logger.debug("🏥 Health Checker inizializzato")
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Esegue tutti i health checks.
        
        Returns:
            Dict con stato di tutti i componenti
        """
        self.last_check = datetime.now()
        
        return {
            'timestamp': self.last_check.isoformat(),
            'uptime': self._get_uptime(),
            'system': self._check_system(),
            'database': await self._check_database(),
            'chroma': await self._check_chroma(),
            'paypal': self._check_paypal(),
            'media': self._check_media(),
            'consciousness': self._check_consciousness(),
            'overall_status': 'healthy'  # Verrà aggiornato
        }
    
    def _get_uptime(self) -> str:
        """Calcola uptime."""
        delta = datetime.now() - self.start_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        return f"{days}d {hours}h {minutes}m"
    
    def _check_system(self) -> Dict[str, Any]:
        """Verifica risorse di sistema."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy' if cpu_percent < 80 and memory.percent < 90 else 'warning',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'platform': platform.platform(),
                'python_version': platform.python_version()
            }
        except Exception as e:
            logger.error(f"❌ Errore system check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_database(self) -> Dict[str, Any]:
        """Verifica database SQLite."""
        try:
            # Test query
            start = datetime.now()
            result = self.db_sqlite.get_conversation_history('test', 1)
            query_time = (datetime.now() - start).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'query_time_ms': round(query_time, 2),
                'path': str(self.db_sqlite.db_path),
                'size': self._get_file_size(self.db_sqlite.db_path)
            }
        except Exception as e:
            logger.error(f"❌ Errore database check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_chroma(self) -> Dict[str, Any]:
        """Verifica ChromaDB."""
        try:
            # Test connessione
            count = self.chroma.count_memories()
            
            return {
                'status': 'healthy',
                'memories_count': count,
                'collection': self.chroma.collection_name
            }
        except Exception as e:
            logger.error(f"❌ Errore Chroma check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_paypal(self) -> Dict[str, Any]:
        """Verifica integrazione PayPal."""
        if not self.paypal:
            return {'status': 'not_configured'}
        
        try:
            # Verifica solo se configurato
            return {
                'status': 'healthy',
                'mode': self.paypal.mode,
                'has_client_id': bool(self.paypal.client_id)
            }
        except Exception as e:
            logger.error(f"❌ Errore PayPal check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_media(self) -> Dict[str, Any]:
        """Verifica media manager."""
        try:
            stats = self.media.get_stats()
            
            return {
                'status': 'healthy',
                'total_files': stats['total'],
                'by_level': stats['by_level'],
                'catalog_size': self._get_file_size(self.media.catalog_path)
            }
        except Exception as e:
            logger.error(f"❌ Errore media check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_consciousness(self) -> Dict[str, Any]:
        """Verifica stato coscienza."""
        try:
            return {
                'status': 'healthy',
                'interactions': len(self.consciousness.interaction_history),
                'users': len(self.consciousness.user_last_interaction),
                'last_thought': bool(self.consciousness.last_thought)
            }
        except Exception as e:
            logger.error(f"❌ Errore consciousness check: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_file_size(self, path) -> str:
        """Ottiene dimensione file in formato leggibile."""
        try:
            size = path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f}{unit}"
                size /= 1024
            return f"{size:.1f}TB"
        except:
            return "N/A"

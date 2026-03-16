"""
Metriche Prometheus per monitoring
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CollectorRegistry
from typing import Dict, Any
from datetime import datetime
import psutil

class MetricsCollector:
    """
    Colleziona metriche per Prometheus.
    """
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Metriche messaggi
        self.messages_received = Counter(
            'AIVA_messages_received_total',
            'Total messages received',
            ['platform'],
            registry=self.registry
        )
        
        self.messages_sent = Counter(
            'AIVA_messages_sent_total',
            'Total messages sent',
            ['platform'],
            registry=self.registry
        )
        
        self.media_sent = Counter(
            'AIVA_media_sent_total',
            'Total media sent',
            ['level'],
            registry=self.registry
        )
        
        # Metriche utenti
        self.active_users = Gauge(
            'AIVA_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.user_levels = Gauge(
            'AIVA_user_levels',
            'Users by level',
            ['level'],
            registry=self.registry
        )
        
        # Metriche economiche
        self.payments_total = Counter(
            'AIVA_payments_total',
            'Total payments amount',
            ['currency'],
            registry=self.registry
        )
        
        self.payments_count = Counter(
            'AIVA_payments_count',
            'Total number of payments',
            registry=self.registry
        )
        
        # Metriche performance
        self.response_time = Histogram(
            'AIVA_response_time_seconds',
            'Response time in seconds',
            buckets=[0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            registry=self.registry
        )
        
        self.processing_time = Histogram(
            'AIVA_processing_time_seconds',
            'Message processing time',
            buckets=[0.1, 0.5, 1, 2, 3, 4, 5],
            registry=self.registry
        )
        
        # Metriche di sistema
        self.cpu_usage = Gauge(
            'AIVA_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'AIVA_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'AIVA_disk_usage_bytes',
            'Disk usage in bytes',
            registry=self.registry
        )
        
        self.uptime = Gauge(
            'AIVA_uptime_seconds',
            'Uptime in seconds',
            registry=self.registry
        )
        
        self.start_time = datetime.now()
        
        logger.debug("📊 Metrics Collector inizializzato")
    
    def record_message_received(self, platform: str = 'telegram'):
        """Registra un messaggio ricevuto."""
        self.messages_received.labels(platform=platform).inc()
    
    def record_message_sent(self, platform: str = 'telegram'):
        """Registra un messaggio inviato."""
        self.messages_sent.labels(platform=platform).inc()
    
    def record_media_sent(self, level: str):
        """Registra un media inviato."""
        self.media_sent.labels(level=level).inc()
    
    def record_payment(self, amount: float, currency: str = 'EUR'):
        """Registra un pagamento."""
        self.payments_total.labels(currency=currency).inc(amount)
        self.payments_count.inc()
    
    def record_response_time(self, seconds: float):
        """Registra tempo di risposta."""
        self.response_time.observe(seconds)
    
    def record_processing_time(self, seconds: float):
        """Registra tempo di elaborazione."""
        self.processing_time.observe(seconds)
    
    def update_system_metrics(self):
        """Aggiorna metriche di sistema."""
        self.cpu_usage.set(psutil.cpu_percent())
        self.memory_usage.set(psutil.virtual_memory().used)
        self.disk_usage.set(psutil.disk_usage('/').used)
        
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        self.uptime.set(uptime_seconds)
    
    def update_user_metrics(self, active_count: int, levels: Dict[str, int]):
        """Aggiorna metriche utenti."""
        self.active_users.set(active_count)
        
        for level, count in levels.items():
            self.user_levels.labels(level=level).set(count)
    
    def get_metrics(self):
        """Restituisce metriche in formato Prometheus."""
        self.update_system_metrics()
        return generate_latest(self.registry)

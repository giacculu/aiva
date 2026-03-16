"""
AIVA 2.0 – GESTIONE LIBRERIA MEDIA
Gestisce tutte le foto e i video di AIVA.
Organizzazione per livelli di intimità:
- sfw: foto normali (sempre disponibili)
- soft: foto carine (dopo confidenza)
- intimate: foto intime (dopo supporto base)
- hot: foto esplicite (dopo supporto regular/vip)
"""

import os
import random
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
from PIL import Image
import hashlib

class MediaManager:
    """
    Gestisce la libreria media di AIVA.
    """
    
    # Livelli di intimità
    INTIMACY_LEVELS = {
        "sfw": 1,
        "soft": 2,
        "intimate": 3,
        "hot": 4
    }
    
    # Livelli minimi per utente
    MIN_LEVEL_FOR_USER = {
        None: "sfw",      # nuovo utente
        "base": "soft",    # ha supportato almeno una volta
        "regular": "intimate",  # supporto regolare
        "vip": "hot"       # supporto significativo
    }
    
    # Estensioni supportate
    SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm']
    
    def __init__(self, media_path: str = "media/library", 
                 catalog_path: str = "media/catalog.json"):
        """
        Inizializza il media manager.
        """
        self.media_path = Path(media_path)
        self.catalog_path = Path(catalog_path)
        
        # Crea cartelle se non esistono
        for level in self.INTIMACY_LEVELS:
            (self.media_path / level).mkdir(parents=True, exist_ok=True)
        
        # Carica catalogo
        self.catalog = self._load_catalog()
        
        # Statistiche invii per evitare ripetizioni
        self.sent_history = {}  # user_id -> lista ultimi invii
        self.last_sent_per_user = {}  # user_id -> ultimo media
        
        logger.info("📸 Media Manager inizializzato")
    
    def _load_catalog(self) -> Dict:
        """Carica o crea catalogo"""
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._create_catalog()
        return self._create_catalog()
    
    def _create_catalog(self) -> Dict:
        """Crea nuovo catalogo"""
        catalog = {}
        for level in self.INTIMACY_LEVELS:
            catalog[level] = []
        return catalog
    
    async def scan_library(self):
        """
        Scannerizza la libreria e aggiorna il catalogo.
        """
        logger.info("🔍 Scansione libreria media...")
        
        for level in self.INTIMACY_LEVELS:
            level_path = self.media_path / level
            if not level_path.exists():
                continue
            
            # Trova tutti i file supportati
            found_files = []
            for ext in self.SUPPORTED_EXTENSIONS:
                found_files.extend(level_path.glob(f'*{ext}'))
            
            new_items = 0
            for file_path in found_files:
                # Controlla se già in catalogo
                existing = [m for m in self.catalog[level] 
                           if m['path'] == str(file_path)]
                
                if not existing:
                    # Ottieni metadata
                    metadata = self._get_file_metadata(file_path)
                    
                    media_item = {
                        'id': self._generate_id(file_path),
                        'path': str(file_path),
                        'filename': file_path.name,
                        'level': level,
                        'intimacy': self.INTIMACY_LEVELS[level],
                        'size': file_path.stat().st_size,
                        'type': self._get_file_type(file_path),
                        'width': metadata.get('width'),
                        'height': metadata.get('height'),
                        'duration': metadata.get('duration'),
                        'times_sent': 0,
                        'last_sent': None,
                        'added': datetime.now().isoformat(),
                        'tags': self._generate_tags(file_path)
                    }
                    self.catalog[level].append(media_item)
                    new_items += 1
            
            logger.info(f"  {level}: {len(self.catalog[level])} file (nuovi: {new_items})")
        
        # Salva catalogo
        await self._save_catalog()
        
        total = sum(len(v) for v in self.catalog.values())
        logger.info(f"✅ Scansione completata: {total} media totali")
    
    def _get_file_metadata(self, file_path: Path) -> Dict:
        """Ottiene metadata del file"""
        metadata = {}
        
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            try:
                with Image.open(file_path) as img:
                    metadata['width'], metadata['height'] = img.size
            except:
                pass
        
        return metadata
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determina tipo di file"""
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'image'
        elif file_path.suffix.lower() in ['.mp4', '.webm']:
            return 'video'
        return 'unknown'
    
    def _generate_id(self, file_path: Path) -> str:
        """Genera ID univoco per media"""
        import hashlib
        import secrets
        
        random_part = secrets.token_hex(4)
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        return f"{file_hash}_{random_part}"
    
    def _generate_tags(self, file_path: Path) -> List[str]:
        """Genera tag dal nome file"""
        name = file_path.stem.lower()
        tags = []
        
        # Tag comuni
        if 'selfie' in name:
            tags.append('selfie')
        if 'natura' in name:
            tags.append('natura')
        if 'casa' in name:
            tags.append('casa')
        if 'outfit' in name:
            tags.append('outfit')
        
        return tags
    
    async def _save_catalog(self):
        """Salva catalogo su disco"""
        try:
            with open(self.catalog_path, 'w', encoding='utf-8') as f:
                json.dump(self.catalog, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio catalogo: {e}")
    
    async def select_media_for_user(self, user_id: str, user_level: Optional[str],
                                    context: str = "") -> Optional[Dict]:
        """
        Seleziona un media appropriato per l'utente.
        """
        # Determina livello massimo accessibile
        max_level_name = self.MIN_LEVEL_FOR_USER.get(user_level, "sfw")
        max_level = self.INTIMACY_LEVELS[max_level_name]
        
        # Filtra media accessibili
        available = []
        for level_name, level_value in self.INTIMACY_LEVELS.items():
            if level_value <= max_level:
                available.extend(self.catalog[level_name])
        
        if not available:
            return None
        
        # Escludi media inviati di recente a questo utente
        if user_id in self.sent_history:
            recent_paths = [s['path'] for s in self.sent_history[user_id][-5:]]
            available = [m for m in available if m['path'] not in recent_paths]
        
        if not available:
            # Se tutti sono stati inviati di recente, prendi comunque
            available = []
            for level_name, level_value in self.INTIMACY_LEVELS.items():
                if level_value <= max_level:
                    available.extend(self.catalog[level_name])
        
        # Scegli casualmente
        selected = random.choice(available)
        
        return selected
    
    def get_media_description(self, media: Dict) -> str:
        """
        Genera una descrizione naturale per il media.
        """
        level = media['level']
        media_type = media['type']
        
        descriptions = {
            'sfw': [
                "Ecco una foto 😊",
                "Una delle mie preferite",
                "Così, per farmi vedere",
                "Spero ti piaccia"
            ],
            'soft': [
                "Una foto un po' più carina 💕",
                "Mi piace questa",
                "Spero ti faccia piacere",
                "Per te"
            ],
            'intimate': [
                "Questa è più intima 🔥",
                "Solo per chi apprezzo",
                "Spero ti piaccia...",
                "Un po' più audace"
            ],
            'hot': [
                "🌶️",
                "Questa è bollente",
                "Spero di non esagerare",
                "Mi fido di te"
            ]
        }
        
        # Scegli descrizione in base al tipo
        if media_type == 'video':
            videos = [f"Ecco un video {level}", f"Video per te {level}"]
            return random.choice(videos)
        
        return random.choice(descriptions.get(level, ["Ecco"]))
    
    def mark_as_sent(self, media: Dict, user_id: str):
        """
        Registra che un media è stato inviato.
        """
        # Aggiorna contatori media
        level = media['level']
        for item in self.catalog[level]:
            if item['id'] == media['id']:
                item['times_sent'] += 1
                item['last_sent'] = datetime.now().isoformat()
                break
        
        # Registra per utente
        if user_id not in self.sent_history:
            self.sent_history[user_id] = []
        
        self.sent_history[user_id].append({
            'path': media['path'],
            'level': level,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mantieni solo ultimi 20
        if len(self.sent_history[user_id]) > 20:
            self.sent_history[user_id] = self.sent_history[user_id][-20:]
        
        self.last_sent_per_user[user_id] = media
        
        # Salva in background
        asyncio.create_task(self._save_catalog())
    
    def get_stats(self) -> Dict:
        """Statistiche libreria"""
        return {
            'total': sum(len(v) for v in self.catalog.values()),
            'by_level': {level: len(items) for level, items in self.catalog.items()},
            'by_type': self._count_by_type()
        }
    
    def _count_by_type(self) -> Dict:
        """Conta media per tipo"""
        counts = {'image': 0, 'video': 0}
        for items in self.catalog.values():
            for item in items:
                type = item.get('type', 'image')
                counts[type] = counts.get(type, 0) + 1
        return counts
    
    def get_available_levels(self, user_level: Optional[str]) -> List[str]:
        """Restituisce livelli disponibili per utente"""
        max_level_name = self.MIN_LEVEL_FOR_USER.get(user_level, "sfw")
        max_level = self.INTIMACY_LEVELS[max_level_name]
        
        return [level for level, value in self.INTIMACY_LEVELS.items() 
                if value <= max_level]

# Istanza globale
media_manager = MediaManager()
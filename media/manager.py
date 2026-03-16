"""
Media Manager: gestione intelligente di foto e video
"""
import os
import random
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

class MediaManager:
    """
    Gestisce la libreria di foto e video di AIVA.
    
    Livelli di intimità:
    - sfw: foto normali (sempre disponibili)
    - soft: foto carine (dopo confidenza base)
    - intimate: foto intime (dopo supporto base)
    - hot: foto esplicite (dopo supporto regular/vip)
    """
    
    # Livelli di intimità con descrizioni
    INTIMACY_LEVELS = {
        'sfw': {
            'level': 1,
            'description': 'foto normali',
            'min_user_level': 'nuovo'
        },
        'soft': {
            'level': 2,
            'description': 'foto carine',
            'min_user_level': 'base'
        },
        'intimate': {
            'level': 3,
            'description': 'foto intime',
            'min_user_level': 'regular'
        },
        'hot': {
            'level': 4,
            'description': 'foto esplicite',
            'min_user_level': 'vip'
        }
    }
    
    # Estensioni supportate
    SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.mov']
    
    def __init__(self, media_dir: Path, catalog_path: Path):
        """
        Args:
            media_dir: Directory principale dei media
            catalog_path: Percorso file catalogo JSON
        """
        self.media_dir = media_dir
        self.catalog_path = catalog_path
        
        # Catalogo media
        self.catalog = self._init_catalog()
        
        # Statistiche invii per utente
        self.user_sent = {}  # user_id -> lista media inviati
        
        # Cache ultimi invii per evitare ripetizioni
        self.recent_sent = {}  # user_id -> ultimo media per livello
        
        logger.info("📸 Media Manager inizializzato")
    
    def _init_catalog(self) -> Dict[str, List]:
        """
        Inizializza catalogo con struttura per livelli.
        """
        catalog = {level: [] for level in self.INTIMACY_LEVELS}
        
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Verifica struttura
                    for level in self.INTIMACY_LEVELS:
                        if level in loaded:
                            catalog[level] = loaded[level]
                logger.info(f"📚 Catalogo caricato: {self.catalog_path}")
            except Exception as e:
                logger.error(f"❌ Errore caricamento catalogo: {e}")
        
        return catalog
    
    async def scan_library(self) -> None:
        """
        Scannerizza la libreria e aggiorna il catalogo.
        """
        logger.info("🔍 Scansione libreria media in corso...")
        
        # Crea cartelle se non esistono
        for level in self.INTIMACY_LEVELS:
            level_dir = self.media_dir / level
            level_dir.mkdir(parents=True, exist_ok=True)
        
        # Scannerizza ogni cartella
        total_new = 0
        for level in self.INTIMACY_LEVELS:
            level_dir = self.media_dir / level
            new_files = await self._scan_level(level, level_dir)
            total_new += new_files
        
        # Salva catalogo
        await self._save_catalog()
        
        logger.info(f"✅ Scansione completata: {self.get_stats()['total']} media totali ({total_new} nuovi)")
    
    async def _scan_level(self, level: str, directory: Path) -> int:
        """
        Scannerizza un livello specifico.
        
        Returns:
            Numero di nuovi file trovati
        """
        new_count = 0
        
        for ext in self.SUPPORTED_EXTENSIONS:
            for file_path in directory.glob(f'*{ext}'):
                # Verifica se già presente
                existing = any(
                    m['path'] == str(file_path) 
                    for m in self.catalog[level]
                )
                
                if not existing:
                    media_item = self._create_media_item(file_path, level)
                    self.catalog[level].append(media_item)
                    new_count += 1
                    logger.debug(f"📸 Nuovo media: {file_path.name} ({level})")
        
        return new_count
    
    def _create_media_item(self, file_path: Path, level: str) -> Dict:
        """
        Crea un item media con metadati.
        """
        stat = file_path.stat()
        
        return {
            'path': str(file_path),
            'filename': file_path.name,
            'level': level,
            'intimacy': self.INTIMACY_LEVELS[level]['level'],
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'added': datetime.now().isoformat(),
            'times_sent': 0,
            'last_sent': None,
            'tags': self._extract_tags(file_path.stem)
        }
    
    def _extract_tags(self, filename: str) -> List[str]:
        """
        Estrae tag dal nome del file.
        """
        tags = []
        name_lower = filename.lower()
        
        # Tag comuni
        tag_keywords = {
            'selfie': 'selfie',
            'spiaggia': 'mare',
            'casa': 'indoor',
            'esterno': 'outdoor',
            'naturale': 'naturale',
            'makeup': 'makeup',
            'sorriso': 'sorriso',
            'posa': 'posa'
        }
        
        for keyword, tag in tag_keywords.items():
            if keyword in name_lower:
                tags.append(tag)
        
        return tags
    
    async def _save_catalog(self) -> None:
        """Salva catalogo su disco."""
        try:
            self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.catalog_path, 'w', encoding='utf-8') as f:
                json.dump(self.catalog, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio catalogo: {e}")
    
    def can_access_level(self, level: str, user_level: str) -> bool:
        """
        Verifica se un utente può accedere a un livello.
        """
        if level not in self.INTIMACY_LEVELS:
            return False
        
        required = self.INTIMACY_LEVELS[level]['min_user_level']
        
        # Mappa livelli
        level_order = ['nuovo', 'base', 'regular', 'vip', 'special']
        
        try:
            user_idx = level_order.index(user_level)
            required_idx = level_order.index(required)
            return user_idx >= required_idx
        except ValueError:
            return False
    
    def get_available_levels(self, user_level: str) -> List[str]:
        """
        Restituisce livelli disponibili per un utente.
        """
        return [
            level for level in self.INTIMACY_LEVELS
            if self.can_access_level(level, user_level)
        ]
    
    def select_media(self, 
                    level: str,
                    user_id: str,
                    avoid_recent: bool = True) -> Optional[Dict]:
        """
        Seleziona un media dal livello specificato.
        
        Args:
            level: Livello richiesto
            user_id: ID utente
            avoid_recent: Evita media inviati recentemente
        
        Returns:
            Media selezionato o None
        """
        if level not in self.catalog or not self.catalog[level]:
            return None
        
        available = self.catalog[level].copy()
        
        if avoid_recent and user_id in self.recent_sent:
            last = self.recent_sent[user_id].get(level)
            if last:
                # Filtra l'ultimo inviato
                available = [m for m in available if m['path'] != last['path']]
        
        if not available:
            # Se non ci sono alternative, usa tutti
            available = self.catalog[level]
        
        selected = random.choice(available)
        
        return selected
    
    def select_media_for_context(self,
                                context: str,
                                user_id: str,
                                user_level: str) -> Optional[Dict]:
        """
        Seleziona media in base al contesto della conversazione.
        """
        context_lower = context.lower()
        
        # Determina livello appropriato dal contesto
        requested_level = None
        
        if any(word in context_lower for word in ['foto', 'vederti', 'selfie', 'immagine']):
            requested_level = 'sfw'
        elif any(word in context_lower for word in ['carina', 'dolce', 'simpatica']):
            requested_level = 'soft'
        elif any(word in context_lower for word in ['intima', 'sexy', 'provocante']):
            requested_level = 'intimate'
        elif any(word in context_lower for word in ['hot', 'bollente', 'sporca']):
            requested_level = 'hot'
        
        if not requested_level:
            return None
        
        # Verifica permessi
        if not self.can_access_level(requested_level, user_level):
            # Fallback a livello inferiore
            for level in ['sfw', 'soft', 'intimate', 'hot']:
                if self.can_access_level(level, user_level) and self.catalog[level]:
                    requested_level = level
                    break
            else:
                return None
        
        # Seleziona media
        selected = self.select_media(requested_level, user_id)
        
        if selected:
            logger.info(f"📸 Selezionato {requested_level}: {selected['filename']}")
        
        return selected
    
    def mark_as_sent(self, media: Dict, user_id: str) -> None:
        """
        Registra che un media è stato inviato.
        """
        level = media['level']
        path = media['path']
        
        # Aggiorna catalogo
        for item in self.catalog[level]:
            if item['path'] == path:
                item['times_sent'] += 1
                item['last_sent'] = datetime.now().isoformat()
                break
        
        # Aggiorna recent sent
        if user_id not in self.recent_sent:
            self.recent_sent[user_id] = {}
        self.recent_sent[user_id][level] = {
            'path': path,
            'time': datetime.now()
        }
        
        # Aggiorna storico utente
        if user_id not in self.user_sent:
            self.user_sent[user_id] = []
        self.user_sent[user_id].append({
            'path': path,
            'level': level,
            'time': datetime.now().isoformat()
        })
        
        # Salva in background
        asyncio.create_task(self._save_catalog())
    
    def get_media_description(self, media: Dict) -> str:
        """
        Genera una descrizione naturale per il media.
        """
        level = media['level']
        tags = media.get('tags', [])
        
        descriptions = {
            'sfw': [
                "Ecco una foto 😊",
                "Una delle mie preferite",
                "Così, per vedermi",
                "Spero ti piaccia"
            ],
            'soft': [
                "Una foto un po' più carina 💕",
                "Mi piace questa",
                "Spero ti faccia piacere",
                "Te la dedico"
            ],
            'intimate': [
                "Una foto più intima 🔥",
                "Questa è per te",
                "Solo per chi apprezzo",
                "Spero ti piaccia"
            ],
            'hot': [
                "🌶️",
                "Bollente...",
                "Spero di non esagerare",
                "Questa è speciale"
            ]
        }
        
        base = random.choice(descriptions.get(level, ["Ecco"]))
        
        # Aggiungi tag se presenti
        if tags and random.random() < 0.3:
            tag = random.choice(tags)
            base += f" (#{tag})"
        
        return base
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche della libreria.
        """
        total = sum(len(items) for items in self.catalog.values())
        by_level = {level: len(items) for level, items in self.catalog.items()}
        
        return {
            'total': total,
            'by_level': by_level,
            'catalog_path': str(self.catalog_path)
        }
    
    def get_level_description(self, level: str) -> str:
        """
        Restituisce descrizione di un livello.
        """
        return self.INTIMACY_LEVELS.get(level, {}).get('description', level)

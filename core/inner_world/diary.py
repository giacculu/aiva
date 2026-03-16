"""
Diario segreto di AIVA: pensieri intimi mai condivisi
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from loguru import logger
from utils.crypto import CryptoManager

class SecretDiary:
    """
    Il diario segreto di AIVA.
    Qui scrive i suoi veri pensieri, che non condividerà mai con gli utenti.
    Serve per autoriflessione e per costruire una personalità coerente.
    """
    
    def __init__(self, diary_path: Path, crypto: CryptoManager):
        """
        Args:
            diary_path: Percorso del file diario (cifrato)
            crypto: Gestore crittografia
        """
        self.path = diary_path
        self.crypto = crypto
        self.entries = []
        self._load()
        logger.info(f"📔 Diario segreto caricato ({len(self.entries)} voci)")
    
    def _load(self) -> None:
        """Carica il diario dal file cifrato."""
        if not self.path.exists():
            self.entries = []
            return
        
        try:
            with open(self.path, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.crypto.decrypt(encrypted)
            data = json.loads(decrypted.decode('utf-8'))
            self.entries = data.get('entries', [])
        except Exception as e:
            logger.error(f"❌ Errore caricamento diario: {e}")
            self.entries = []
    
    def _save(self) -> None:
        """Salva il diario (cifrato)."""
        try:
            data = {
                'entries': self.entries,
                'last_updated': datetime.now().isoformat()
            }
            
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            encrypted = self.crypto.encrypt(json_str)
            
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'wb') as f:
                f.write(encrypted)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio diario: {e}")
    
    # ========== SCRITTURA ==========
    
    def write(self, content: str, mood: Optional[str] = None, 
              user_id: Optional[str] = None, importance: float = 0.5) -> Dict:
        """
        Scrive una nuova voce nel diario.
        
        Args:
            content: Contenuto del pensiero
            mood: Umore al momento della scrittura
            user_id: Utente correlato (se presente)
            importance: Importanza (0-1)
        
        Returns:
            La voce creata
        """
        entry = {
            'id': len(self.entries) + 1,
            'timestamp': datetime.now().isoformat(),
            'content': content,
            'mood': mood,
            'user_id': user_id,
            'importance': importance,
            'tags': self._extract_tags(content)
        }
        
        self.entries.append(entry)
        self._save()
        
        logger.debug(f"📝 Nuova voce diario: {content[:50]}...")
        return entry
    
    def write_about_user(self, user_id: str, thought: str, 
                        sentiment: float = 0.0) -> Dict:
        """
        Scrive un pensiero su un utente specifico.
        """
        return self.write(
            content=f"Su {user_id}: {thought}",
            user_id=user_id,
            importance=0.3 + abs(sentiment) * 0.5
        )
    
    def write_reflection(self, topic: str, reflection: str) -> Dict:
        """
        Scrive una riflessione generale (non su un utente).
        """
        return self.write(
            content=f"Riflessione su {topic}: {reflection}",
            importance=0.6
        )
    
    # ========== LETTURA ==========
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Recupera le voci più recenti."""
        sorted_entries = sorted(
            self.entries,
            key=lambda e: e['timestamp'],
            reverse=True
        )
        return sorted_entries[:limit]
    
    def get_about_user(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Recupera voci su un utente specifico."""
        user_entries = [
            e for e in self.entries 
            if e.get('user_id') == user_id
        ]
        sorted_entries = sorted(
            user_entries,
            key=lambda e: e['timestamp'],
            reverse=True
        )
        return sorted_entries[:limit]
    
    def get_important(self, min_importance: float = 0.7, limit: int = 10) -> List[Dict]:
        """Recupera le voci più importanti."""
        important = [
            e for e in self.entries 
            if e.get('importance', 0) >= min_importance
        ]
        sorted_entries = sorted(
            important,
            key=lambda e: e['importance'],
            reverse=True
        )
        return sorted_entries[:limit]
    
    def search(self, keyword: str, case_sensitive: bool = False) -> List[Dict]:
        """Cerca voci per parola chiave."""
        results = []
        for e in self.entries:
            content = e['content']
            if not case_sensitive:
                content = content.lower()
                keyword = keyword.lower()
            
            if keyword in content:
                results.append(e)
        
        return results
    
    # ========== ANALISI ==========
    
    def _extract_tags(self, content: str) -> List[str]:
        """Estrae hashtag dal contenuto."""
        words = content.split()
        tags = [w[1:] for w in words if w.startswith('#')]
        return tags
    
    def get_common_tags(self, limit: int = 10) -> List[tuple]:
        """Restituisce i tag più frequenti."""
        tag_count = {}
        for e in self.entries:
            for tag in e.get('tags', []):
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        sorted_tags = sorted(
            tag_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_tags[:limit]
    
    def get_mood_distribution(self) -> Dict[str, int]:
        """Distribuzione degli umori nel diario."""
        mood_count = {}
        for e in self.entries:
            mood = e.get('mood')
            if mood:
                mood_count[mood] = mood_count.get(mood, 0) + 1
        return mood_count
    
    def get_user_mentions(self) -> Dict[str, int]:
        """Conteggio menzioni per utente."""
        mentions = {}
        for e in self.entries:
            user = e.get('user_id')
            if user:
                mentions[user] = mentions.get(user, 0) + 1
        return mentions
    
    # ========== MANUTENZIONE ==========
    
    def archive_old_entries(self, days: int = 90) -> int:
        """
        Archivia voci vecchie (rimuove dal diario principale).
        Restituisce il numero di voci archiviate.
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        to_archive = []
        remaining = []
        
        for e in self.entries:
            if e['timestamp'] < cutoff_str and e.get('importance', 0) < 0.3:
                to_archive.append(e)
            else:
                remaining.append(e)
        
        self.entries = remaining
        self._save()
        
        # Qui si potrebbe salvare le voci archiviate in un file separato
        if to_archive:
            logger.info(f"📦 Archiviate {len(to_archive)} voci vecchie")
        
        return len(to_archive)
    
    # ========== CONTESTO PER RIFLESSIONE ==========
    
    def get_reflection_prompt(self) -> str:
        """
        Genera un prompt per l'autoriflessione basato sul diario.
        """
        recent = self.get_recent(5)
        important = self.get_important(0.8, 3)
        
        prompt = "📔 **Estratti dal mio diario segreto:**\n\n"
        
        if recent:
            prompt += "**Pensieri recenti:**\n"
            for e in recent:
                date = datetime.fromisoformat(e['timestamp']).strftime("%d/%m")
                prompt += f"- [{date}] {e['content'][:100]}...\n"
            prompt += "\n"
        
        if important:
            prompt += "**Cose importanti per me:**\n"
            for e in important:
                prompt += f"- {e['content'][:100]}...\n"
        
        return prompt
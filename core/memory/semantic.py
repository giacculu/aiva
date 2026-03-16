"""
AIVA 2.0 – MEMORIA SEMANTICA (fatti strutturati)
Qui AIVA conserva tutto ciò che sa sugli utenti:
nome, età, città, lavoro, hobby, preferenze, etc.
Usa SQLite per accesso rapido e strutturato.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from loguru import logger
import threading
from contextlib import contextmanager

class SemanticMemory:
    """
    Memoria semantica di AIVA.
    Ogni fatto è una tripla: (user_id, chiave, valore, categoria, confidenza, timestamp)
    """
    
    # Schema del database
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        confidence REAL DEFAULT 1.0,
        source TEXT,  -- come è stato appreso
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        times_mentioned INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT 1,
        metadata TEXT,  -- JSON aggiuntivo
        UNIQUE(user_id, key)
    );
    
    CREATE INDEX IF NOT EXISTS idx_facts_user ON facts(user_id);
    CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
    CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key);
    CREATE INDEX IF NOT EXISTS idx_facts_active ON facts(is_active);
    
    CREATE TABLE IF NOT EXISTS fact_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact_id INTEGER,
        old_value TEXT,
        new_value TEXT,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reason TEXT,
        FOREIGN KEY(fact_id) REFERENCES facts(id)
    );
    
    CREATE TABLE IF NOT EXISTS user_metadata (
        user_id TEXT PRIMARY KEY,
        first_interaction TIMESTAMP,
        last_interaction TIMESTAMP,
        total_messages INTEGER DEFAULT 0,
        avg_response_time REAL,
        preferred_language TEXT,
        timezone TEXT,
        notes TEXT,  -- appunti personali di AIVA
        trust_level INTEGER DEFAULT 0,  -- 0-10
        intimacy_level INTEGER DEFAULT 0,  -- 0-10
        metadata TEXT
    );
    
    CREATE TABLE IF NOT EXISTS fact_categories (
        category TEXT PRIMARY KEY,
        description TEXT,
        priority INTEGER DEFAULT 0,  -- più alto = più importante
        retention_days INTEGER DEFAULT 365,  -- quanto conservare
        requires_confirmation BOOLEAN DEFAULT 0
    );
    
    PRAGMA foreign_keys = ON;
    """
    
    # Categorie predefinite
    DEFAULT_CATEGORIES = {
        "identita": {"priority": 100, "retention_days": 9999, "desc": "Nome, età, genere"},
        "contatti": {"priority": 80, "retention_days": 9999, "desc": "Città, telefono, email"},
        "lavoro": {"priority": 60, "retention_days": 730, "desc": "Professione, studi"},
        "hobby": {"priority": 40, "retention_days": 365, "desc": "Interessi, passioni"},
        "gusti": {"priority": 30, "retention_days": 180, "desc": "Cibi, musica, film"},
        "relazione": {"priority": 90, "retention_days": 9999, "desc": "Come ci conosciamo"},
        "supporto": {"priority": 95, "retention_days": 9999, "desc": "Storico pagamenti"},
        "preferenze": {"priority": 50, "retention_days": 365, "desc": "Come preferisce interagire"},
        "note": {"priority": 20, "retention_days": 90, "desc": "Appunti vari"},
        "private": {"priority": 200, "retention_days": 9999, "desc": "Note personali di AIVA"}
    }
    
    def __init__(self, db_path: str = "data/semantic.db"):
        """
        Inizializza il database SQLite.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-local storage per connessioni
        self.local = threading.local()
        
        # Inizializza database
        self._init_db()
        
        # Cache in memoria per accesso rapido
        self.cache = {}
        self.cache_timestamps = {}
        self.CACHE_TTL = 300  # 5 minuti
        
        logger.info(f"📚 Memoria semantica inizializzata in {db_path}")
    
    def _init_db(self):
        """Crea le tabelle se non esistono"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Esegui schema
            for statement in self.SCHEMA.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            
            # Inserisci categorie predefinite
            for cat, data in self.DEFAULT_CATEGORIES.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO fact_categories (category, description, priority, retention_days)
                    VALUES (?, ?, ?, ?)
                """, (cat, data["desc"], data["priority"], data["retention_days"]))
            
            conn.commit()
    
    @contextmanager
    def _get_conn(self):
        """Fornisce una connessione thread-safe"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES,
                check_same_thread=False
            )
            self.local.conn.row_factory = sqlite3.Row
        yield self.local.conn
    
    def _cache_key(self, user_id: str, key: str = None) -> str:
        """Genera chiave cache"""
        if key:
            return f"{user_id}:{key}"
        return user_id
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se cache è ancora valida"""
        if cache_key not in self.cache_timestamps:
            return False
        age = (datetime.now() - self.cache_timestamps[cache_key]).total_seconds()
        return age < self.CACHE_TTL
    
    def remember(self, user_id: str, key: str, value: Any, 
                category: str = "general", confidence: float = 1.0,
                source: str = "conversation", metadata: Optional[Dict] = None):
        """
        Ricorda un fatto su un utente.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                # Controlla se esiste già
                cursor.execute("""
                    SELECT id, value FROM facts 
                    WHERE user_id = ? AND key = ? AND is_active = 1
                """, (user_id, key))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Aggiorna esistente
                    old_value = existing["value"]
                    fact_id = existing["id"]
                    
                    # Solo se il valore è cambiato
                    if str(old_value) != str(value):
                        cursor.execute("""
                            UPDATE facts 
                            SET value = ?, confidence = ?, last_updated = CURRENT_TIMESTAMP,
                                times_mentioned = times_mentioned + 1, metadata = ?
                            WHERE id = ?
                        """, (str(value), confidence, json.dumps(metadata) if metadata else None, fact_id))
                        
                        # Registra nella history
                        cursor.execute("""
                            INSERT INTO fact_history (fact_id, old_value, new_value, reason)
                            VALUES (?, ?, ?, ?)
                        """, (fact_id, old_value, str(value), source))
                        
                        logger.debug(f"📝 Fatto aggiornato: {user_id} [{key}] = {value}")
                else:
                    # Nuovo fatto
                    cursor.execute("""
                        INSERT INTO facts (user_id, key, value, category, confidence, source, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, key, str(value), category, confidence, source, 
                          json.dumps(metadata) if metadata else None))
                    
                    logger.debug(f"📝 Nuovo fatto: {user_id} [{key}] = {value}")
                
                # Aggiorna ultima interazione
                cursor.execute("""
                    INSERT INTO user_metadata (user_id, last_interaction, total_messages)
                    VALUES (?, CURRENT_TIMESTAMP, 1)
                    ON CONFLICT(user_id) DO UPDATE SET
                        last_interaction = CURRENT_TIMESTAMP,
                        total_messages = total_messages + 1
                """, (user_id,))
                
                conn.commit()
                
                # Invalida cache
                cache_key = self._cache_key(user_id)
                self.cache.pop(cache_key, None)
                self.cache_timestamps.pop(cache_key, None)
                
        except Exception as e:
            logger.error(f"❌ Errore nel ricordare: {e}")
    
    def recall(self, user_id: str, key: str = None, category: str = None) -> Any:
        """
        Ricorda uno o più fatti su un utente.
        """
        cache_key = self._cache_key(user_id, key)
        
        # Controlla cache
        if self._is_cache_valid(cache_key) and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                if key:
                    # Fatto specifico
                    cursor.execute("""
                        SELECT value FROM facts 
                        WHERE user_id = ? AND key = ? AND is_active = 1
                    """, (user_id, key))
                    
                    row = cursor.fetchone()
                    result = row[0] if row else None
                    
                elif category:
                    # Tutti i fatti di una categoria
                    cursor.execute("""
                        SELECT key, value, confidence, last_updated 
                        FROM facts 
                        WHERE user_id = ? AND category = ? AND is_active = 1
                        ORDER BY priority DESC, last_updated DESC
                    """, (user_id, category))
                    
                    result = {row["key"]: row["value"] for row in cursor.fetchall()}
                    
                else:
                    # Tutti i fatti
                    cursor.execute("""
                        SELECT key, value, category, confidence, last_updated 
                        FROM facts 
                        WHERE user_id = ? AND is_active = 1
                        ORDER BY category, priority DESC, last_updated DESC
                    """, (user_id,))
                    
                    result = {}
                    for row in cursor.fetchall():
                        if row["category"] not in result:
                            result[row["category"]] = {}
                        result[row["category"]][row["key"]] = row["value"]
                
                # Salva in cache
                self.cache[cache_key] = result
                self.cache_timestamps[cache_key] = datetime.now()
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Errore nel ricordare: {e}")
            return None
    
    def recall_all(self, user_id: str) -> Dict:
        """Ricorda tutto ciò che sa su un utente"""
        return self.recall(user_id)
    
    def forget(self, user_id: str, key: str = None, reason: str = "user_request"):
        """
        Dimentica un fatto o tutto su un utente.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                if key:
                    # Dimentica un fatto specifico
                    cursor.execute("""
                        UPDATE facts SET is_active = 0 
                        WHERE user_id = ? AND key = ?
                    """, (user_id, key))
                    
                    logger.info(f"🗑️ Dimenticato {key} per {user_id}")
                    
                else:
                    # Dimentica tutto sull'utente
                    cursor.execute("""
                        UPDATE facts SET is_active = 0 
                        WHERE user_id = ?
                    """, (user_id,))
                    
                    logger.info(f"🗑️ Dimenticato tutto su {user_id}")
                
                conn.commit()
                
                # Invalida cache
                cache_key = self._cache_key(user_id)
                self.cache.pop(cache_key, None)
                self.cache_timestamps.pop(cache_key, None)
                
        except Exception as e:
            logger.error(f"❌ Errore nel dimenticare: {e}")
    
    def get_user_profile(self, user_id: str) -> Dict:
        """
        Restituisce un profilo completo dell'utente.
        """
        facts = self.recall_all(user_id)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Metadati utente
            cursor.execute("""
                SELECT * FROM user_metadata WHERE user_id = ?
            """, (user_id,))
            
            metadata_row = cursor.fetchone()
            metadata = dict(metadata_row) if metadata_row else {}
        
        return {
            "facts": facts,
            "metadata": metadata,
            "summary": self._generate_summary(user_id, facts, metadata)
        }
    
    def _generate_summary(self, user_id: str, facts: Dict, metadata: Dict) -> str:
        """
        Genera un riassunto in linguaggio naturale di ciò che sa sull'utente.
        """
        parts = []
        
        # Estrai informazioni chiave
        identita = facts.get("identita", {})
        if nome := identita.get("nome"):
            parts.append(f"Si chiama {nome}")
        if eta := identita.get("età"):
            parts.append(f"ha {eta} anni")
        
        contatti = facts.get("contatti", {})
        if citta := contatti.get("città"):
            parts.append(f"vive a {citta}")
        
        lavoro = facts.get("lavoro", {})
        if professione := lavoro.get("lavoro"):
            parts.append(f"fa {professione}")
        
        relazione = facts.get("relazione", {})
        if come := relazione.get("come_conosciuto"):
            parts.append(f"ci conosciamo da {come}")
        
        if not parts:
            return "Non so ancora molto di questa persona."
        
        # Costruisci frase
        intro = "Di questa persona so che"
        if len(parts) == 1:
            return f"{intro} {parts[0]}."
        elif len(parts) == 2:
            return f"{intro} {parts[0]} e {parts[1]}."
        else:
            last = parts.pop()
            return f"{intro} {', '.join(parts)} e {last}."
    
    def update_trust(self, user_id: str, delta: int):
        """
        Aggiorna il livello di fiducia per un utente.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_metadata (user_id, trust_level)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    trust_level = trust_level + ?
            """, (user_id, max(0, delta), delta))
            conn.commit()
    
    def update_intimacy(self, user_id: str, delta: int):
        """
        Aggiorna il livello di intimità per un utente.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_metadata (user_id, intimacy_level)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    intimacy_level = intimacy_level + ?
            """, (user_id, max(0, delta), delta))
            conn.commit()
    
    def add_note(self, user_id: str, note: str):
        """
        Aggiunge una nota personale su un utente (visibile solo a AIVA).
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_metadata (user_id, notes)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    notes = notes || '\n' || ?
            """, (user_id, note, note))
            
            conn.commit()
    
    def get_fact_history(self, user_id: str, key: str) -> List[Dict]:
        """
        Recupera la storia delle modifiche di un fatto.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT f.id FROM facts f
                WHERE f.user_id = ? AND f.key = ?
            """, (user_id, key))
            
            fact_row = cursor.fetchone()
            if not fact_row:
                return []
            
            fact_id = fact_row["id"]
            
            cursor.execute("""
                SELECT * FROM fact_history 
                WHERE fact_id = ?
                ORDER BY changed_at DESC
            """, (fact_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """
        Statistiche sulla memoria semantica.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Totale fatti
            cursor.execute("SELECT COUNT(*) FROM facts WHERE is_active = 1")
            total_facts = cursor.fetchone()[0]
            
            # Utenti unici
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM facts")
            unique_users = cursor.fetchone()[0]
            
            # Fatti per categoria
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM facts 
                WHERE is_active = 1 
                GROUP BY category
            """)
            per_category = {row["category"]: row["count"] for row in cursor.fetchall()}
            
            # Fatti recenti (ultima settimana)
            cursor.execute("""
                SELECT COUNT(*) FROM facts 
                WHERE last_updated > datetime('now', '-7 days')
            """)
            recent = cursor.fetchone()[0]
            
            return {
                "total_facts": total_facts,
                "unique_users": unique_users,
                "per_category": per_category,
                "recent_facts": recent,
                "avg_facts_per_user": total_facts / unique_users if unique_users else 0
            }
    
    def cleanup_old_facts(self, days: int = 365):
        """
        Disattiva fatti più vecchi di un certo numero di giorni.
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE facts 
                SET is_active = 0 
                WHERE last_updated < datetime('now', ? || ' days')
                AND key NOT IN ('nome', 'user_id', 'prima_interazione')
            """, (f"-{days}",))
            
            affected = cursor.rowcount
            conn.commit()
            
            if affected:
                logger.info(f"🧹 Disattivati {affected} fatti vecchi")

# Istanza globale
semantic_memory = SemanticMemory()
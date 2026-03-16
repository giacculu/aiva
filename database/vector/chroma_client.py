"""
Client ChromaDB per memoria episodica vettoriale
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from loguru import logger
import json
import os

class ChromaMemoryClient:
    """
    Gestisce la memoria episodica usando ChromaDB.
    Ogni ricordo è vettorizzato e può essere recuperato per similarità.
    """
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 8000,
                 collection_name: str = "AIVA_memories",
                 persist_directory: Optional[str] = None):
        """
        Inizializza client ChromaDB.
        
        Args:
            host: Host di ChromaDB
            port: Porta di ChromaDB
            collection_name: Nome della collezione
            persist_directory: Directory per persistenza (se None, usa in-memory)
        """
        self.collection_name = collection_name
        
        # Configurazione client
        if persist_directory:
            # Modalità persistente (locale)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"📦 ChromaDB persistente: {persist_directory}")
        else:
            # Modalità client-server
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"📦 ChromaDB connesso a {host}:{port}")
        
        # Funzione di embedding (usa sentence-transformers)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Crea o recupera collezione
        self._init_collection()
    
    def _init_collection(self):
        """Inizializza la collezione."""
        try:
            # Prova a ottenere collezione esistente
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            count = self.collection.count()
            logger.info(f"📚 Collezione '{self.collection_name}' caricata ({count} ricordi)")
        except ValueError:
            # Crea nuova collezione
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"✨ Nuova collezione '{self.collection_name}' creata")
    
    def add_memory(self, 
                  text: str,
                  user_id: str,
                  memory_type: str = "conversation",
                  emotional_valence: Optional[float] = None,
                  importance: float = 0.5,
                  timestamp: Optional[datetime] = None,
                  metadata: Optional[Dict] = None) -> str:
        """
        Aggiunge un ricordo alla memoria vettoriale.
        
        Args:
            text: Testo del ricordo
            user_id: ID utente associato
            memory_type: Tipo di memoria (conversation, fact, emotion, etc.)
            emotional_valence: Valenza emotiva (-1 a +1)
            importance: Importanza (0 a 1)
            timestamp: Timestamp dell'evento
            metadata: Metadati aggiuntivi
        
        Returns:
            ID del ricordo creato
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Prepara metadati
        meta = {
            "user_id": user_id,
            "memory_type": memory_type,
            "emotional_valence": emotional_valence,
            "importance": importance,
            "timestamp": timestamp.isoformat(),
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M:%S")
        }
        if metadata:
            meta.update(metadata)
        
        # Genera ID univoco
        memory_id = f"{user_id}_{timestamp.timestamp()}_{memory_type}"
        
        # Aggiungi alla collezione
        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[memory_id]
        )
        
        logger.debug(f"💾 Ricordo aggiunto: {memory_id}")
        return memory_id
    
    def search_memories(self, 
                       query: str,
                       user_id: Optional[str] = None,
                       memory_type: Optional[str] = None,
                       n_results: int = 5,
                       min_importance: float = 0.0) -> List[Dict]:
        """
        Cerca ricordi per similarità semantica.
        
        Args:
            query: Testo di ricerca
            user_id: Filtra per utente
            memory_type: Filtra per tipo
            n_results: Numero massimo di risultati
            min_importance: Importanza minima
        
        Returns:
            Lista di ricordi con punteggi di similarità
        """
        # Costruisci filtro metadati
        where = {}
        if user_id:
            where["user_id"] = user_id
        if memory_type:
            where["memory_type"] = memory_type
        if min_importance > 0:
            where["importance"] = {"$gte": min_importance}
        
        # Esegui ricerca
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where if where else None
        )
        
        # Formatta risultati
        memories = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                memories.append({
                    'id': doc_id,
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                    'similarity': 1 - results['distances'][0][i] if 'distances' in results else None
                })
        
        return memories
    
    def get_memories_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Recupera tutti i ricordi di un utente (ordinati per data)."""
        results = self.collection.get(
            where={"user_id": user_id},
            limit=limit
        )
        
        memories = []
        if results['ids']:
            for i, doc_id in enumerate(results['ids']):
                memories.append({
                    'id': doc_id,
                    'text': results['documents'][i] if results['documents'] else None,
                    'metadata': results['metadatas'][i] if results['metadatas'] else None
                })
        
        # Ordina per data (decrescente)
        memories.sort(
            key=lambda x: x['metadata'].get('timestamp', ''),
            reverse=True
        )
        
        return memories
    
    def get_recent_memories(self, user_id: str, hours: int = 24) -> List[Dict]:
        """Recupera ricordi delle ultime N ore."""
        from datetime import datetime, timedelta
        
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        results = self.collection.get(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"timestamp": {"$gte": cutoff}}
                ]
            }
        )
        
        memories = []
        if results['ids']:
            for i, doc_id in enumerate(results['ids']):
                memories.append({
                    'id': doc_id,
                    'text': results['documents'][i] if results['documents'] else None,
                    'metadata': results['metadatas'][i] if results['metadatas'] else None
                })
        
        return memories
    
    def delete_memory(self, memory_id: str) -> None:
        """Elimina un ricordo specifico."""
        self.collection.delete(ids=[memory_id])
        logger.debug(f"🗑️ Ricordo eliminato: {memory_id}")
    
    def update_memory_importance(self, memory_id: str, importance: float) -> None:
        """Aggiorna l'importanza di un ricordo."""
        self.collection.update(
            ids=[memory_id],
            metadatas=[{"importance": importance}]
        )
    
    def count_memories(self, user_id: Optional[str] = None) -> int:
        """Conta i ricordi (opzionalmente per utente)."""
        if user_id:
            return self.collection.count(where={"user_id": user_id})
        return self.collection.count()
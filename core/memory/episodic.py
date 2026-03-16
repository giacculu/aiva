"""
AIVA 2.0 – MEMORIA EPISODICA (basata su ChromaDB)
AIVA ricorda eventi specifici come esperienze complete:
- Cosa è successo
- Quando
- Con chi
- Come l'ha fatta sentire
- Quanto è importante
"""

import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from loguru import logger
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import hashlib

class EpisodicMemory:
    """
    Memoria episodica di AIVA.
    Ogni episodio è un vettore + metadati.
    Usa ChromaDB per similarità semantica e filtro temporale.
    """
    
    # Peso per il decadimento temporale
    TIME_DECAY_FACTOR = 0.1  # per giorno
    
    # Soglie di importanza
    IMPORTANCE_THRESHOLDS = {
        "bassa": 0.3,
        "media": 0.6,
        "alta": 0.8,
        "fondamentale": 0.95
    }
    
    def __init__(self, persist_directory: str = "data/chromadb"):
        """
        Inizializza ChromaDB e il modello di embedding.
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Inizializza ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Crea o recupera collezione
        self.collection = self.client.get_or_create_collection(
            name="AIVA_episodic_memory",
            metadata={"hnsw:space": "cosine"}  # Similarità coseno
        )
        
        # Modello per embedding
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Cache in memoria per accesso rapido
        self.recent_episodes = []
        self.important_episodes = []
        
        logger.info(f"🧠 Memoria episodica inizializzata con {self.collection.count()} ricordi")
    
    async def add_episode(self,
                          user_id: str,
                          description: str,
                          emotion: Dict,
                          importance: float = 0.5,
                          message: Optional[str] = None,
                          response: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          metadata: Optional[Dict] = None):
        """
        Aggiunge un episodio alla memoria.
        
        Args:
            user_id: chi era coinvolto
            description: descrizione testuale dell'evento
            emotion: stato emotivo associato (P,A,D)
            importance: quanto è importante (0-1)
            message: messaggio ricevuto (opzionale)
            response: risposta data (opzionale)
            tags: tag per categorizzazione
            metadata: altri metadati
        """
        timestamp = datetime.now()
        
        # Genera embedding
        text_to_embed = f"{description} {message or ''} {response or ''}"
        embedding = self.encoder.encode(text_to_embed).tolist()
        
        # Prepara metadati
        metadata = metadata or {}
        metadata.update({
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "description": description[:200],  # Limite per Chroma
            "importance": importance,
            "pleasure": emotion.get("P", 0),
            "arousal": emotion.get("A", 0),
            "dominance": emotion.get("D", 0),
            "message_preview": (message or "")[:100],
            "response_preview": (response or "")[:100],
            "tags": ",".join(tags or []),
            "year": timestamp.year,
            "month": timestamp.month,
            "day": timestamp.day,
            "hour": timestamp.hour
        })
        
        # Genera ID univoco
        episode_id = self._generate_id(user_id, timestamp)
        
        # Aggiungi a ChromaDB
        self.collection.add(
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[episode_id]
        )
        
        # Aggiorna cache
        episode = {
            "id": episode_id,
            "user_id": user_id,
            "description": description,
            "timestamp": timestamp,
            "emotion": emotion,
            "importance": importance,
            "message": message,
            "response": response,
            "tags": tags or []
        }
        
        self.recent_episodes.append(episode)
        if len(self.recent_episodes) > 100:
            self.recent_episodes.pop(0)
        
        if importance > self.IMPORTANCE_THRESHOLDS["alta"]:
            self.important_episodes.append(episode)
            if len(self.important_episodes) > 50:
                self.important_episodes.pop(0)
        
        logger.debug(f"📝 Episodio aggiunto: {description[:50]}... (importanza: {importance:.2f})")
        
        return episode_id
    
    async def search(self,
                    query: str,
                    user_id: Optional[str] = None,
                    limit: int = 10,
                    min_importance: float = 0.0,
                    days_ago: Optional[int] = None,
                    emotion_similarity: Optional[Dict] = None,
                    weight_strategy: Optional[callable] = None) -> List[Dict]:
        """
        Cerca episodi simili a una query.
        
        Args:
            query: testo di ricerca
            user_id: filtra per utente
            limit: numero massimo risultati
            min_importance: importanza minima
            days_ago: solo ultimi N giorni
            emotion_similarity: cerca episodi con emozioni simili
            weight_strategy: funzione per pesare i risultati
        """
        # Genera embedding della query
        query_embedding = self.encoder.encode(query).tolist()
        
        # Costruisci filtri
        where = {}
        if user_id:
            where["user_id"] = user_id
        if days_ago:
            cutoff = datetime.now() - timedelta(days=days_ago)
            where["timestamp"] = {"$gte": cutoff.isoformat()}
        if min_importance > 0:
            where["importance"] = {"$gte": min_importance}
        
        # Cerca
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit * 2,  # Prendi di più per filtrare dopo
            where=where if where else None
        )
        
        # Ricostruisci episodi
        episodes = []
        for i in range(len(results['ids'][0])):
            episode_id = results['ids'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            
            # Calcola similarità (1 - distance)
            similarity = 1 - distance
            
            # Applica weight strategy se fornita
            weight = 1.0
            if weight_strategy:
                weight = weight_strategy(metadata)
            
            # Calcola score finale
            score = similarity * weight
            
            episodes.append({
                "id": episode_id,
                "user_id": metadata.get("user_id"),
                "description": metadata.get("description"),
                "timestamp": datetime.fromisoformat(metadata.get("timestamp")),
                "emotion": {
                    "P": metadata.get("pleasure"),
                    "A": metadata.get("arousal"),
                    "D": metadata.get("dominance")
                },
                "importance": metadata.get("importance"),
                "similarity": similarity,
                "weight": weight,
                "score": score,
                "metadata": metadata
            })
        
        # Ordina per score e limita
        episodes.sort(key=lambda x: x["score"], reverse=True)
        return episodes[:limit]
    
    async def get_episodes_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Recupera tutti gli episodi di un utente.
        """
        results = self.collection.get(
            where={"user_id": user_id},
            limit=limit
        )
        
        episodes = []
        for i in range(len(results['ids'])):
            episodes.append(self._metadata_to_episode(
                results['ids'][i],
                results['metadatas'][i]
            ))
        
        return episodes
    
    async def get_important_episodes(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Recupera gli episodi più importanti.
        """
        where = {"importance": {"$gte": self.IMPORTANCE_THRESHOLDS["alta"]}}
        if user_id:
            where["user_id"] = user_id
        
        results = self.collection.get(
            where=where,
            limit=limit
        )
        
        episodes = []
        for i in range(len(results['ids'])):
            episodes.append(self._metadata_to_episode(
                results['ids'][i],
                results['metadatas'][i]
            ))
        
        return episodes
    
    async def get_emotional_memories(self, emotion_vector: np.ndarray, limit: int = 10) -> List[Dict]:
        """
        Cerca episodi con emozioni simili a un vettore PAD.
        """
        # Questa è una ricerca per similarità di emozione, non semantica
        # Dovremo recuperare molti episodi e filtrare
        all_episodes = self.collection.get(limit=1000)
        
        episodes = []
        for i in range(len(all_episodes['ids'])):
            meta = all_episodes['metadatas'][i]
            episode_emotion = np.array([
                meta.get("pleasure", 0),
                meta.get("arousal", 0),
                meta.get("dominance", 0)
            ])
            
            # Similarità coseno
            similarity = np.dot(emotion_vector, episode_emotion) / (
                np.linalg.norm(emotion_vector) * np.linalg.norm(episode_emotion)
            )
            
            episodes.append({
                "episode": self._metadata_to_episode(all_episodes['ids'][i], meta),
                "similarity": similarity
            })
        
        episodes.sort(key=lambda x: x["similarity"], reverse=True)
        return [e["episode"] for e in episodes[:limit]]
    
    async def get_timeline(self, user_id: Optional[str] = None, days: int = 30) -> List[Dict]:
        """
        Restituisce una timeline di episodi.
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        where = {"timestamp": {"$gte": cutoff.isoformat()}}
        if user_id:
            where["user_id"] = user_id
        
        results = self.collection.get(
            where=where,
            limit=500
        )
        
        episodes = []
        for i in range(len(results['ids'])):
            episodes.append(self._metadata_to_episode(
                results['ids'][i],
                results['metadatas'][i]
            ))
        
        # Ordina per timestamp
        episodes.sort(key=lambda x: x["timestamp"])
        return episodes
    
    def _metadata_to_episode(self, episode_id: str, metadata: Dict) -> Dict:
        """Converte metadati Chroma in episodio"""
        return {
            "id": episode_id,
            "user_id": metadata.get("user_id"),
            "description": metadata.get("description"),
            "timestamp": datetime.fromisoformat(metadata.get("timestamp")),
            "emotion": {
                "P": metadata.get("pleasure"),
                "A": metadata.get("arousal"),
                "D": metadata.get("dominance")
            },
            "importance": metadata.get("importance"),
            "message": metadata.get("message_preview"),
            "response": metadata.get("response_preview"),
            "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else []
        }
    
    def _generate_id(self, user_id: str, timestamp: datetime) -> str:
        """Genera ID univoco per episodio"""
        import hashlib
        import secrets
        
        random_part = secrets.token_hex(4)
        time_part = timestamp.strftime("%Y%m%d%H%M%S")
        user_part = hashlib.md5(user_id.encode()).hexdigest()[:8]
        
        return f"{time_part}_{user_part}_{random_part}"
    
    def get_weight_strategy(self, strategy: str = "recency"):
        """
        Restituisce una funzione di peso per i risultati.
        """
        if strategy == "recency":
            def recency_weight(metadata):
                timestamp = datetime.fromisoformat(metadata.get("timestamp"))
                days_ago = (datetime.now() - timestamp).days
                return np.exp(-self.TIME_DECAY_FACTOR * days_ago)
            return recency_weight
        
        elif strategy == "importance":
            def importance_weight(metadata):
                return metadata.get("importance", 0.5)
            return importance_weight
        
        elif strategy == "balanced":
            def balanced_weight(metadata):
                timestamp = datetime.fromisoformat(metadata.get("timestamp"))
                days_ago = (datetime.now() - timestamp).days
                recency = np.exp(-self.TIME_DECAY_FACTOR * days_ago)
                importance = metadata.get("importance", 0.5)
                return (recency + importance) / 2
            return balanced_weight
        
        else:
            return lambda x: 1.0
    
    def delete_old_memories(self, days: int = 365):
        """
        Elimina memorie più vecchie di un certo numero di giorni.
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # ChromaDB non supporta delete con filtro temporale diretto
        # Dovremo recuperare e cancellare uno per uno
        results = self.collection.get()
        
        to_delete = []
        for i in range(len(results['ids'])):
            meta = results['metadatas'][i]
            timestamp = datetime.fromisoformat(meta.get("timestamp"))
            if timestamp < cutoff:
                to_delete.append(results['ids'][i])
        
        if to_delete:
            self.collection.delete(ids=to_delete)
            logger.info(f"🧹 Eliminate {len(to_delete)} memorie vecchie")
    
    def get_stats(self) -> Dict:
        """Statistiche della memoria"""
        count = self.collection.count()
        
        # Analisi per importanza
        results = self.collection.get(limit=1000)
        
        importance_levels = {level: 0 for level in self.IMPORTANCE_THRESHOLDS}
        for meta in results['metadatas']:
            imp = meta.get("importance", 0)
            for level, threshold in self.IMPORTANCE_THRESHOLDS.items():
                if imp >= threshold:
                    importance_levels[level] += 1
                    break
        
        return {
            "total_episodes": count,
            "importance_distribution": importance_levels,
            "unique_users": len(set(m.get("user_id") for m in results['metadatas']))
        }

# Istanza globale
episodic_memory = EpisodicMemory()
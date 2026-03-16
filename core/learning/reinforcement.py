"""
AIVA 2.0 – APPRENDIMENTO RINFORZATO IMPLICITO
AIVA ottimizza le sue risposte nel tempo:
- Impara quali strategie funzionano meglio
- Bilancia esplorazione (provare cose nuove) e sfruttamento (usare ciò che funziona)
- Si adatta a ogni utente individualmente
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path
import random

class ImplicitRL:
    """
    Apprendimento per rinforzo implicito.
    Ogni "azione" di AIVA (tono, lunghezza, argomento) ha un valore che viene
    aggiornato in base al feedback ricevuto.
    """
    
    # Parametri di apprendimento
    LEARNING_RATE = 0.1  # quanto velocemente impara
    DISCOUNT_FACTOR = 0.9  # importanza del futuro
    EXPLORATION_RATE = 0.2  # quanto spesso prova cose nuove
    EXPLORATION_DECAY = 0.995  # esplora meno col tempo
    
    # Spazio delle azioni
    ACTION_SPACE = {
        "tone": ["dolce", "scherzoso", "serio", "affettuoso", "malinconico", "energico"],
        "length": ["breve", "medio", "lungo"],
        # "topic": ["generale", "personale", "intimo", "supporto"],
        "emoji_usage": ["pochi", "normali", "molti"],
        "formality": ["informale", "medio", "formale"]
    }
    
    def __init__(self, data_path: str = "data/rl_data.json"):
        """
        Inizializza il reinforcement learner.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Q-values per ogni utente
        self.q_values = self._load_data()
        
        # Contatori per esplorazione
        self.exploration_counts = defaultdict(int)
        self.exploitation_counts = defaultdict(int)
        
        # Cache
        self.cache = {}
        
        logger.info("🤖 Implicit RL inizializzato")
    
    def _load_data(self) -> Dict:
        """Carica i Q-values esistenti"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_data(self):
        """Salva i Q-values"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.q_values, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio RL: {e}")
    
    def _get_user_q(self, user_id: str) -> Dict:
        """Ottiene o inizializza i Q-values per un utente"""
        if user_id not in self.q_values:
            self.q_values[user_id] = {
                "tone": {t: 0.5 for t in self.ACTION_SPACE["tone"]},
                "length": {l: 0.5 for l in self.ACTION_SPACE["length"]},
                "emoji_usage": {e: 0.5 for e in self.ACTION_SPACE["emoji_usage"]},
                "formality": {f: 0.5 for f in self.ACTION_SPACE["formality"]},
                "metadata": {
                    "total_updates": 0,
                    "last_update": None,
                    "exploration_rate": self.EXPLORATION_RATE
                }
            }
        return self.q_values[user_id]
    
    def select_action(self, user_id: str, context: Dict) -> Dict:
        """
        Seleziona le azioni (tono, lunghezza, etc.) per la risposta.
        Bilancia esplorazione e sfruttamento.
        """
        user_q = self._get_user_q(user_id)
        
        # Decay exploration rate
        meta = user_q["metadata"]
        current_epsilon = meta.get("exploration_rate", self.EXPLORATION_RATE)
        
        actions = {}
        
        for dim, values in self.ACTION_SPACE.items():
            if dim == "topic":
                continue  # gestito separatamente
            
            # ε-greedy: esplora con probabilità ε
            if random.random() < current_epsilon:
                # Esplora: scegli casualmente
                actions[dim] = random.choice(values)
                self.exploration_counts[user_id] += 1
                logger.debug(f"🔍 Esplorazione {dim}: {actions[dim]}")
            else:
                # Sfrutta: scegli il migliore
                best_action = max(user_q[dim], key=user_q[dim].get)
                actions[dim] = best_action
                self.exploitation_counts[user_id] += 1
                logger.debug(f"🎯 Sfruttamento {dim}: {best_action}")
        
        # Decay exploration rate
        meta["exploration_rate"] = current_epsilon * self.EXPLORATION_DECAY
        
        return actions
    
    def update_q_values(self, user_id: str, actions: Dict, reward: float, 
                       next_context: Optional[Dict] = None):
        """
        Aggiorna i Q-values in base al reward ricevuto.
        """
        user_q = self._get_user_q(user_id)
        
        # Calcola max future reward (se c'è contesto futuro)
        future_max = 0.0
        if next_context and next_context.get("next_reward"):
            future_max = max([
                max(user_q[dim].values()) 
                for dim in self.ACTION_SPACE.keys() 
                if dim in user_q
            ])
        
        # Aggiorna ogni dimensione
        for dim, action in actions.items():
            if dim not in user_q:
                continue
            
            current_q = user_q[dim].get(action, 0.5)
            
            # Q-learning update: Q(s,a) = Q(s,a) + α * [r + γ * max Q(s',a') - Q(s,a)]
            new_q = current_q + self.LEARNING_RATE * (
                reward + self.DISCOUNT_FACTOR * future_max - current_q
            )
            
            # Mantieni nel range [0,1]
            user_q[dim][action] = max(0.0, min(1.0, new_q))
            
            logger.debug(f"📈 Q[{dim}][{action}] aggiornato: {current_q:.2f} → {new_q:.2f} (reward: {reward:.2f})")
        
        # Aggiorna metadata
        user_q["metadata"]["total_updates"] += 1
        user_q["metadata"]["last_update"] = datetime.now().isoformat()
        
        # Salva periodicamente
        if user_q["metadata"]["total_updates"] % 10 == 0:
            self._save_data()
    
    def compute_reward(self, feedback_score: float, user_response: Optional[str],
                      context: Dict) -> float:
        """
        Calcola il reward in base al feedback e al contesto.
        """
        reward = feedback_score  # base da feedback
        
        # Bonus/Malus aggiuntivi
        if user_response:
            # Ha risposto = positivo
            reward += 0.2
        
        if context.get("continued_conversation"):
            # Ha continuato a parlare = molto positivo
            reward += 0.5
        
        if context.get("left_conversation"):
            # Ha smesso di parlare = molto negativo
            reward -= 0.5
        
        if context.get("asked_question_back"):
            # Ha fatto una domanda = interesse
            reward += 0.3
        
        if context.get("called_name"):
            # Ha chiamato per nome = confidenza
            reward += 0.2
        
        # Normalizza nel range [-1, 1]
        return max(-1.0, min(1.0, reward))
    
    def get_best_action(self, user_id: str, dimension: str) -> Optional[str]:
        """
        Restituisce la migliore azione per una dimensione.
        """
        user_q = self._get_user_q(user_id)
        if dimension not in user_q:
            return None
        
        return max(user_q[dimension], key=user_q[dimension].get)
    
    def get_action_values(self, user_id: str) -> Dict:
        """
        Restituisce tutti i Q-values per un utente.
        """
        user_q = self._get_user_q(user_id)
        return {
            dim: dict(sorted(values.items(), key=lambda x: x[1], reverse=True))
            for dim, values in user_q.items()
            if dim != "metadata"
        }
    
    def get_statistics(self, user_id: str) -> Dict:
        """
        Statistiche di apprendimento per un utente.
        """
        user_q = self._get_user_q(user_id)
        
        # Calcola convergenza (varianza dei Q-values)
        convergence = {}
        for dim, values in user_q.items():
            if dim == "metadata":
                continue
            q_list = list(values.values())
            convergence[dim] = np.var(q_list)
        
        return {
            "total_updates": user_q["metadata"]["total_updates"],
            "exploration_rate": user_q["metadata"]["exploration_rate"],
            "exploration_count": self.exploration_counts.get(user_id, 0),
            "exploitation_count": self.exploitation_counts.get(user_id, 0),
            "exploration_ratio": self.exploration_counts.get(user_id, 0) / 
                                max(1, self.exploration_counts.get(user_id, 0) + 
                                    self.exploitation_counts.get(user_id, 0)),
            "convergence": convergence,
            "best_actions": {
                dim: max(values, key=values.get)
                for dim, values in user_q.items() if dim != "metadata"
            }
        }
    
    def get_global_insights(self) -> Dict:
        """
        Insight globali su tutti gli utenti.
        """
        insights = {
            "total_users": len(self.q_values),
            "total_updates": sum(
                u["metadata"]["total_updates"] 
                for u in self.q_values.values() 
                if isinstance(u, dict) and "metadata" in u
            ),
            "avg_exploration_rate": np.mean([
                u["metadata"]["exploration_rate"] 
                for u in self.q_values.values() 
                if isinstance(u, dict) and "metadata" in u
            ]),
            "global_preferences": defaultdict(lambda: defaultdict(float))
        }
        
        # Preferenze globali
        for user_id, user_q in self.q_values.items():
            if not isinstance(user_q, dict):
                continue
            for dim, values in user_q.items():
                if dim == "metadata":
                    continue
                best = max(values, key=values.get)
                insights["global_preferences"][dim][best] += 1
        
        return insights
    
    def reset_user(self, user_id: str):
        """
        Resetta l'apprendimento per un utente (utile se cambia comportamento).
        """
        if user_id in self.q_values:
            del self.q_values[user_id]
            self.exploration_counts[user_id] = 0
            self.exploitation_counts[user_id] = 0
            logger.info(f"🔄 Reset apprendimento per {user_id}")

# Istanza globale
implicit_rl = ImplicitRL()
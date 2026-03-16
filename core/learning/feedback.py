"""
AIVA 2.0 – APPRENDIMENTO DAL FEEDBACK
AIVA impara dalle reazioni dell'utente:
- Cosa funziona (risposte lunghe, brevi, tono)
- Cosa non funziona (viene ignorato, risposte secche)
- Si adatta a ogni utente individualmente
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path

class FeedbackLearner:
    """
    Impara dalle interazioni passate per migliorare le risposte future.
    Tiene traccia di cosa funziona per ogni utente.
    """
    
    # Metriche di feedback implicito
    FEEDBACK_SIGNALS = {
        "positive": {
            "response_length_ratio": 0.8,  # risponde con messaggi lunghi
            "response_time": 0.5,  # risponde velocemente
            "continues_conversation": 0.9,  # continua a parlare
            "asks_questions": 0.7,  # fa domande
            "uses_emojis": 0.3,  # usa emoji positive
            "calls_name": 0.8,  # chiama AIVA per nome
            "compliments": 1.0  # fa complimenti
        },
        "negative": {
            "ignores": 0.9,  # ignora la domanda
            "short_responses": 0.7,  # risponde con "ok", "sì", "no"
            "leaves_conversation": 1.0,  # smette di rispondere
            "angry_emojis": 0.8,  # emoji arrabbiate
            "criticism": 1.0,  # critiche
            "repeats_question": 0.6  # ripete la stessa domanda
        }
    }
    
    def __init__(self, data_path: str = "data/feedback.json"):
        """
        Inizializza il learner con persistenza.
        """
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dati di apprendimento per utente
        self.user_data = self._load_data()
        
        # Cache per performance
        self.cache = {}
        
        logger.info("📚 Feedback Learner inizializzato")
    
    def _load_data(self) -> Dict:
        """Carica i dati esistenti"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_data(self):
        """Salva i dati"""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio feedback: {e}")
    
    def record_interaction(self, user_id: str, 
                          AIVA_message: str,
                          user_response: Optional[str],
                          context: Dict):
        """
        Registra un'interazione e il feedback implicito.
        """
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "interactions": [],
                "preferences": self._default_preferences(),
                "stats": {
                    "total_interactions": 0,
                    "positive_feedback": 0,
                    "negative_feedback": 0,
                    "avg_response_time": 0,
                    "preferred_topics": defaultdict(int)
                }
            }
        
        # Calcola feedback per questa interazione
        feedback = self._calculate_feedback(user_response, context)
        
        # Registra interazione
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "AIVA_message": AIVA_message[:100],  # preview
            "user_response": user_response[:100] if user_response else None,
            "user_responded": user_response is not None,
            "feedback_score": feedback["score"],
            "feedback_signals": feedback["signals"],
            "context": {
                "topic": context.get("topic", "unknown"),
                "AIVA_mood": context.get("AIVA_mood"),
                "user_intent": context.get("user_intent")
            }
        }
        
        self.user_data[user_id]["interactions"].append(interaction)
        
        # Aggiorna statistiche
        stats = self.user_data[user_id]["stats"]
        stats["total_interactions"] += 1
        if feedback["score"] > 0.5:
            stats["positive_feedback"] += 1
        elif feedback["score"] < -0.3:
            stats["negative_feedback"] += 1
        
        if user_response and context.get("response_time"):
            # Aggiorna tempo medio
            old_avg = stats["avg_response_time"]
            n = stats["total_interactions"]
            stats["avg_response_time"] = (old_avg * (n-1) + context["response_time"]) / n
        
        # Aggiorna preferenze
        self._update_preferences(user_id, feedback, context)
        
        # Mantieni solo ultime 100 interazioni
        if len(self.user_data[user_id]["interactions"]) > 100:
            self.user_data[user_id]["interactions"] = \
                self.user_data[user_id]["interactions"][-100:]
        
        # Salva periodicamente
        if stats["total_interactions"] % 10 == 0:
            self._save_data()
        
        return feedback
    
    def _calculate_feedback(self, user_response: Optional[str], 
                           context: Dict) -> Dict:
        """
        Calcola il feedback implicito dalla risposta dell'utente.
        """
        signals = {}
        score = 0.0
        weight_sum = 0.0
        
        if not user_response:
            # Non ha risposto = feedback negativo
            signals["no_response"] = 1.0
            score = -0.5
            weight_sum = 1.0
        else:
            # Analizza la risposta
            response_lower = user_response.lower()
            
            # Segnali positivi
            if len(user_response.split()) > 10:  # risposta lunga
                signals["long_response"] = 0.8
                score += 0.8 * self.FEEDBACK_SIGNALS["positive"]["response_length_ratio"]
                weight_sum += self.FEEDBACK_SIGNALS["positive"]["response_length_ratio"]
            
            if any(q in response_lower for q in ["?", "come", "perché", "cosa"]):
                signals["asks_questions"] = 0.7
                score += 0.7 * self.FEEDBACK_SIGNALS["positive"]["asks_questions"]
                weight_sum += self.FEEDBACK_SIGNALS["positive"]["asks_questions"]
            
            if "AIVA" in response_lower or "erika" in response_lower:
                signals["calls_name"] = 0.8
                score += 0.8 * self.FEEDBACK_SIGNALS["positive"]["calls_name"]
                weight_sum += self.FEEDBACK_SIGNALS["positive"]["calls_name"]
            
            if any(comp in response_lower for comp in ["brava", "bella", "carina", "dolce"]):
                signals["compliment"] = 1.0
                score += 1.0 * self.FEEDBACK_SIGNALS["positive"]["compliments"]
                weight_sum += self.FEEDBACK_SIGNALS["positive"]["compliments"]
            
            # Segnali negativi
            if len(user_response.split()) < 3:  # risposta molto breve
                signals["short_response"] = 0.7
                score -= 0.7 * self.FEEDBACK_SIGNALS["negative"]["short_responses"]
                weight_sum += self.FEEDBACK_SIGNALS["negative"]["short_responses"]
            
            if any(angry in response_lower for angry in ["😠", "😡", "rabbia", "cattivo"]):
                signals["angry"] = 0.8
                score -= 0.8 * self.FEEDBACK_SIGNALS["negative"]["angry_emojis"]
                weight_sum += self.FEEDBACK_SIGNALS["negative"]["angry_emojis"]
            
            if any(crit in response_lower for crit in ["brutta", "stupida", "noiosa"]):
                signals["criticism"] = 1.0
                score -= 1.0 * self.FEEDBACK_SIGNALS["negative"]["criticism"]
                weight_sum += self.FEEDBACK_SIGNALS["negative"]["criticism"]
        
        # Normalizza score
        if weight_sum > 0:
            score = score / weight_sum
        else:
            score = 0.0
        
        return {
            "score": score,
            "signals": signals,
            "interpretation": self._interpret_score(score)
        }
    
    def _interpret_score(self, score: float) -> str:
        """Interpreta il punteggio di feedback"""
        if score > 0.7:
            return "molto positivo"
        elif score > 0.3:
            return "positivo"
        elif score > -0.3:
            return "neutro"
        elif score > -0.7:
            return "negativo"
        else:
            return "molto negativo"
    
    def _update_preferences(self, user_id: str, feedback: Dict, context: Dict):
        """
        Aggiorna le preferenze dell'utente in base al feedback.
        """
        prefs = self.user_data[user_id]["preferences"]
        
        # Pesi per diverse caratteristiche
        learning_rate = 0.1
        
        # Aggiorna in base al feedback
        if feedback["score"] > 0.3:
            # Feedback positivo: rafforza ciò che abbiamo fatto
            if context.get("AIVA_mood"):
                current = prefs["preferred_moods"].get(context["AIVA_mood"], 0.5)
                prefs["preferred_moods"][context["AIVA_mood"]] = current + learning_rate
            
            if context.get("response_length"):
                prefs["preferred_length"] = (
                    prefs["preferred_length"] * (1 - learning_rate) + 
                    context["response_length"] * learning_rate
                )
            
            if context.get("topic"):
                prefs["preferred_topics"][context["topic"]] = (
                    prefs["preferred_topics"].get(context["topic"], 0) + 1
                )
        
        elif feedback["score"] < -0.3:
            # Feedback negativo: indebolisci ciò che abbiamo fatto
            if context.get("AIVA_mood"):
                current = prefs["preferred_moods"].get(context["AIVA_mood"], 0.5)
                prefs["preferred_moods"][context["AIVA_mood"]] = current - learning_rate
            
            if context.get("topic"):
                # Evita questo topic in futuro
                prefs["topics_to_avoid"].append(context["topic"])
                prefs["topics_to_avoid"] = list(set(prefs["topics_to_avoid"][-20:]))
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """
        Restituisce le preferenze apprese per un utente.
        """
        if user_id not in self.user_data:
            return self._default_preferences()
        
        prefs = self.user_data[user_id]["preferences"]
        
        # Normalizza
        total = sum(prefs["preferred_moods"].values())
        if total > 0:
            prefs["preferred_moods"] = {
                k: v/total for k, v in prefs["preferred_moods"].items()
            }
        
        return prefs
    
    def get_best_mood(self, user_id: str) -> Optional[str]:
        """
        Restituisce il mood che funziona meglio per questo utente.
        """
        prefs = self.get_user_preferences(user_id)
        moods = prefs.get("preferred_moods", {})
        
        if not moods:
            return None
        
        return max(moods, key=moods.get)
    
    def get_best_length(self, user_id: str) -> float:
        """
        Restituisce la lunghezza di risposta preferita (in parole).
        """
        prefs = self.get_user_preferences(user_id)
        return prefs.get("preferred_length", 50)
    
    def get_topics_to_avoid(self, user_id: str) -> List[str]:
        """
        Restituisce i topic che hanno causato feedback negativi.
        """
        prefs = self.get_user_preferences(user_id)
        return prefs.get("topics_to_avoid", [])
    
    def _default_preferences(self) -> Dict:
        """Preferenze di default"""
        return {
            "preferred_moods": {
                "felice": 0.5,
                "normale": 0.5,
                "affettuosa": 0.5
            },
            "preferred_length": 50,
            "preferred_topics": {},
            "topics_to_avoid": [],
            "use_emojis": 0.5,
            "formality": 0.5
        }
    
    def get_statistics(self, user_id: str) -> Dict:
        """
        Statistiche di apprendimento per un utente.
        """
        if user_id not in self.user_data:
            return {}
        
        data = self.user_data[user_id]
        stats = data["stats"]
        
        return {
            "total_interactions": stats["total_interactions"],
            "positive_rate": stats["positive_feedback"] / max(1, stats["total_interactions"]),
            "negative_rate": stats["negative_feedback"] / max(1, stats["total_interactions"]),
            "avg_response_time": stats["avg_response_time"],
            "preferred_mood": self.get_best_mood(user_id),
            "preferred_length": self.get_best_length(user_id),
            "topics_to_avoid": self.get_topics_to_avoid(user_id)
        }
    
    def get_global_insights(self) -> Dict:
        """
        Insight globali su tutti gli utenti.
        """
        insights = {
            "total_users": len(self.user_data),
            "total_interactions": sum(
                u["stats"]["total_interactions"] for u in self.user_data.values()
            ),
            "avg_positive_rate": np.mean([
                u["stats"]["positive_feedback"] / max(1, u["stats"]["total_interactions"])
                for u in self.user_data.values()
            ]),
            "best_moods": defaultdict(float)
        }
        
        # Mood più apprezzati globalmente
        for u_data in self.user_data.values():
            prefs = u_data["preferences"]
            for mood, score in prefs["preferred_moods"].items():
                insights["best_moods"][mood] += score
        
        # Normalizza
        total = sum(insights["best_moods"].values())
        if total > 0:
            insights["best_moods"] = {
                k: v/total for k, v in insights["best_moods"].items()
            }
        
        return insights

# Istanza globale
feedback_learner = FeedbackLearner()
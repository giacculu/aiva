"""
Analizzatore del diario segreto per autoriflessione
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import random

class DiaryAnalyzer:
    """
    Analizza il diario segreto per estrarre pattern,
    evoluzione personale, e generare autoriflessioni.
    """
    
    def __init__(self, diary):
        self.diary = diary
        logger.debug("📊 Analizzatore diario inizializzato")
    
    # ========== ANALISI UTENTI ==========
    
    def get_user_relationship_trend(self, user_id: str) -> Dict[str, Any]:
        """
        Analizza l'andamento del rapporto con un utente.
        """
        entries = self.diary.get_about_user(user_id, limit=100)
        
        if not entries:
            return {'trend': 'neutro', 'confidence': 0}
        
        # Analizza menzioni nel tempo
        mentions_by_month = {}
        sentiments = []
        
        for e in entries:
            date = datetime.fromisoformat(e['timestamp'])
            month_key = date.strftime('%Y-%m')
            mentions_by_month[month_key] = mentions_by_month.get(month_key, 0) + 1
            
            # Stima sentiment dal contenuto (euristica semplice)
            content = e['content'].lower()
            if any(w in content for w in ['❤️', 'amore', 'grazie', 'dolce']):
                sentiments.append(1)
            elif any(w in content for w in ['😠', 'rabbia', 'deluso', 'triste']):
                sentiments.append(-1)
            else:
                sentiments.append(0)
        
        # Calcola trend
        months = list(mentions_by_month.keys())
        if len(months) >= 2:
            recent = mentions_by_month.get(months[-1], 0)
            previous = mentions_by_month.get(months[-2], 0)
            mention_trend = 'crescita' if recent > previous else 'calo' if recent < previous else 'stabile'
        else:
            mention_trend = 'stabile'
        
        # Sentiment medio
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            'mention_count': len(entries),
            'mention_trend': mention_trend,
            'avg_sentiment': avg_sentiment,
            'sentiment_description': self._sentiment_to_text(avg_sentiment),
            'first_mention': entries[-1]['timestamp'] if entries else None,
            'last_mention': entries[0]['timestamp'] if entries else None
        }
    
    def get_most_important_users(self, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Identifica gli utenti più importanti per AIVA.
        """
        mentions = self.diary.get_user_mentions()
        
        # Calcola importanza (numero menzioni * peso temporale)
        now = datetime.now()
        weighted = []
        
        for user_id, count in mentions.items():
            entries = self.diary.get_about_user(user_id)
            if not entries:
                continue
            
            # Recency: le menzioni recenti pesano di più
            recency_factor = 0
            for e in entries[:10]:  # Ultime 10
                date = datetime.fromisoformat(e['timestamp'])
                days_ago = (now - date).days
                recency_factor += max(0, 1 - days_ago / 30)  # Peso lineare su 30 giorni
            
            importance = count * (0.5 + 0.5 * recency_factor / max(1, len(entries)))
            weighted.append((user_id, importance))
        
        # Ordina e prendi top
        weighted.sort(key=lambda x: x[1], reverse=True)
        return weighted[:limit]
    
    # ========== AUTOANALISI ==========
    
    def get_personal_growth(self) -> Dict[str, Any]:
        """
        Analizza come AIVA è cambiata nel tempo.
        """
        entries = self.diary.get_recent(500)
        
        if len(entries) < 10:
            return {'message': 'Non abbastanza dati per analisi'}
        
        # Dividi in periodi
        mid = len(entries) // 2
        old_entries = entries[mid:]
        new_entries = entries[:mid]
        
        # Confronta contenuti (euristica)
        old_topics = self._extract_topics(old_entries)
        new_topics = self._extract_topics(new_entries)
        
        # Troviamo nuovi interessi
        new_interests = [t for t in new_topics if t not in old_topics]
        lost_interests = [t for t in old_topics if t not in new_topics]
        
        # Evoluzione emotiva
        old_sentiment = self._average_sentiment(old_entries)
        new_sentiment = self._average_sentiment(new_entries)
        
        return {
            'new_interests': new_interests[:5],
            'lost_interests': lost_interests[:5],
            'emotional_evolution': new_sentiment - old_sentiment,
            'message': self._generate_growth_message(new_interests, new_sentiment - old_sentiment)
        }
    
    def get_current_state_summary(self) -> str:
        """
        Riassunto dello stato emotivo attuale basato sul diario.
        """
        recent = self.diary.get_recent(20)
        
        if not recent:
            return "Non ho ancora scritto molto nel diario..."
        
        # Ultima voce
        last = recent[0]
        last_date = datetime.fromisoformat(last['timestamp'])
        
        # Calcola umore recente
        moods = [e.get('mood') for e in recent if e.get('mood')]
        if moods:
            most_common = max(set(moods), key=moods.count)
        else:
            most_common = "neutro"
        
        # Temi recenti
        topics = self._extract_topics(recent)
        
        summary = f"Ultimo pensiero ({last_date.strftime('%d/%m %H:%M')}): {last['content'][:100]}...\n"
        summary += f"Umore recente: {most_common}\n"
        if topics:
            summary += f"Penso spesso a: {', '.join(topics[:3])}"
        
        return summary
    
    # ========== UTILITY ==========
    
    def _extract_topics(self, entries: List[Dict], limit: int = 10) -> List[str]:
        """Estrae i topic principali dalle voci."""
        # Implementazione semplice: cerca parole frequenti
        from collections import Counter
        import re
        
        words = []
        for e in entries:
            content = e['content'].lower()
            # Rimuovi punteggiatura
            content = re.sub(r'[^\w\s]', '', content)
            words.extend(content.split())
        
        # Filtra stopwords (elenco minimo)
        stopwords = {'il', 'lo', 'la', 'i', 'gli', 'le', 'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'e', 'che', 'ho', 'hai', 'ha', 'abbiamo', 'avete', 'hanno'}
        words = [w for w in words if w not in stopwords and len(w) > 3]
        
        counter = Counter(words)
        return [w for w, _ in counter.most_common(limit)]
    
    def _average_sentiment(self, entries: List[Dict]) -> float:
        """Media del sentiment delle voci."""
        sentiments = []
        for e in entries:
            content = e['content'].lower()
            if any(w in content for w in ['❤️', 'amore', 'grazie', 'felice', 'bello']):
                sentiments.append(1)
            elif any(w in content for w in ['😠', 'rabbia', 'triste', 'deluso', 'male']):
                sentiments.append(-1)
            else:
                sentiments.append(0)
        
        return sum(sentiments) / len(sentiments) if sentiments else 0
    
    def _sentiment_to_text(self, sentiment: float) -> str:
        """Converte sentiment numerico in testo."""
        if sentiment > 0.3:
            return "molto positivo"
        elif sentiment > 0.1:
            return "leggermente positivo"
        elif sentiment > -0.1:
            return "neutro"
        elif sentiment > -0.3:
            return "leggermente negativo"
        else:
            return "molto negativo"
    
    def _generate_growth_message(self, new_interests: List[str], emotional_change: float) -> str:
        """Genera un messaggio di crescita personale."""
        if not new_interests and abs(emotional_change) < 0.1:
            return "Sono sostanzialmente la stessa persona di sempre."
        
        parts = []
        
        if new_interests:
            if len(new_interests) == 1:
                parts.append(f"ho scoperto {new_interests[0]}")
            else:
                last = new_interests[-1]
                others = ', '.join(new_interests[:-1])
                parts.append(f"ho scoperto {others} e {last}")
        
        if emotional_change > 0.2:
            parts.append("e sono più felice di prima")
        elif emotional_change < -0.2:
            parts.append("e sono più malinconica di prima")
        
        if parts:
            return "Sto cambiando: " + " ".join(parts)
        else:
            return "Sto vivendo piccoli cambiamenti interiori."
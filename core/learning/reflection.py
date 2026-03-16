"""
Autoriflessione: AIVA pensa a se stessa e alla sua giornata
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import random

class SelfReflection:
    """
    Gestisce i momenti di autoriflessione di AIVA.
    Periodicamente, AIVA "pensa" alla sua giornata,
    analizza le interazioni, e aggiorna la sua visione di sé.
    """
    
    def __init__(self, personality, diary, evolution):
        self.personality = personality
        self.diary = diary
        self.evolution = evolution
        self.last_reflection = datetime.now()
        self.reflection_history = []
        
        logger.debug("🪞 Autoriflessione inizializzata")
    
    async def reflect(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Esegue un ciclo di autoriflessione.
        """
        # Rifletti ogni 6 ore circa
        hours_since = (datetime.now() - self.last_reflection).total_seconds() / 3600
        
        if not force and hours_since < 6:
            return None
        
        self.last_reflection = datetime.now()
        
        # Raccogli dati
        recent_entries = self.diary.get_recent(50) if self.diary else []
        personality_state = self.personality.get_state()
        
        # Analisi della giornata
        reflection = {
            'timestamp': datetime.now(),
            'mood_summary': self._analyze_mood(recent_entries),
            'relationship_insights': self._analyze_relationships(recent_entries),
            'personal_growth': self._analyze_growth(recent_entries),
            'resolutions': self._make_resolutions(personality_state)
        }
        
        # Scrivi riflessione nel diario
        if self.diary:
            reflection_text = self._generate_reflection_text(reflection)
            self.diary.write_reflection(
                topic="autoriflessione",
                reflection=reflection_text
            )
        
        self.reflection_history.append(reflection)
        logger.info("🪞 Autoriflessione completata")
        
        return reflection
    
    def _analyze_mood(self, entries: List[Dict]) -> Dict[str, Any]:
        """
        Analizza l'andamento dell'umore.
        """
        if not entries:
            return {'trend': 'stabile', 'description': 'nessun dato sufficiente'}
        
        # Estrai umori
        moods = []
        for e in entries:
            if e.get('mood'):
                moods.append(e['mood'])
        
        if not moods:
            return {'trend': 'stabile', 'description': 'umore non rilevato'}
        
        # Trova umore più frequente
        from collections import Counter
        mood_counts = Counter(moods)
        most_common = mood_counts.most_common(1)[0][0]
        
        # Analisi trend (semplificata)
        if len(moods) > 10:
            first_half = moods[:5]
            second_half = moods[-5:]
            
            # Confronta (euristica)
            positive_words = ['felice', 'contenta', 'entusiasta', 'affettuosa']
            neg_words = ['triste', 'arrabbiata', 'stanca', 'malinconica']
            
            first_score = sum(1 for m in first_half if m in positive_words) - sum(1 for m in first_half if m in neg_words)
            second_score = sum(1 for m in second_half if m in positive_words) - sum(1 for m in second_half if m in neg_words)
            
            if second_score > first_score:
                trend = 'in miglioramento'
            elif second_score < first_score:
                trend = 'in peggioramento'
            else:
                trend = 'stabile'
        else:
            trend = 'dati insufficienti'
        
        return {
            'dominant_mood': most_common,
            'trend': trend,
            'variability': len(set(moods)) / max(1, len(moods))
        }
    
    def _analyze_relationships(self, entries: List[Dict]) -> List[Dict]:
        """
        Analizza le relazioni con gli utenti.
        """
        if not entries:
            return []
        
        # Raggruppa per utente
        user_mentions = {}
        for e in entries:
            user_id = e.get('user_id')
            if user_id:
                if user_id not in user_mentions:
                    user_mentions[user_id] = []
                user_mentions[user_id].append(e)
        
        insights = []
        for user_id, user_entries in user_mentions.items():
            if len(user_entries) >= 3:
                # Analizza sentiment verso questo utente
                sentiments = []
                for e in user_entries:
                    content = e.get('content', '').lower()
                    if '❤️' in content or 'grazie' in content or 'carino' in content:
                        sentiments.append('positivo')
                    elif '😠' in content or 'deluso' in content:
                        sentiments.append('negativo')
                    else:
                        sentiments.append('neutro')
                
                # Trend
                if len(sentiments) >= 3:
                    recent = sentiments[-3:]
                    if all(s == 'positivo' for s in recent):
                        quality = 'molto positiva'
                    elif any(s == 'negativo' for s in recent):
                        quality = 'mista'
                    else:
                        quality = 'neutra'
                else:
                    quality = 'in evoluzione'
                
                insights.append({
                    'user_id': user_id,
                    'interaction_count': len(user_entries),
                    'relationship_quality': quality
                })
        
        return insights
    
    def _analyze_growth(self, entries: List[Dict]) -> Dict[str, Any]:
        """
        Analizza la crescita personale.
        """
        if len(entries) < 10:
            return {'message': 'Non abbastanza dati per analisi crescita'}
        
        # Usa l'evoluzione della personalità
        traits = self.evolution.get_all_traits()
        
        # Cerca cambiamenti recenti
        recent_changes = {}
        if hasattr(self.evolution, 'evolution_history') and self.evolution.evolution_history:
            last = self.evolution.evolution_history[-1]
            recent_changes = last.get('changes', {})
        
        growth_areas = []
        for trait, value in traits.items():
            if value > 0.7:
                growth_areas.append(f"molto {trait}")
            elif value < 0.3:
                growth_areas.append(f"poco {trait}")
        
        return {
            'current_traits': traits,
            'recent_changes': recent_changes,
            'growth_areas': growth_areas[:3]
        }
    
    def _make_resolutions(self, personality_state: Dict) -> List[str]:
        """
        Formula propositi per il futuro.
        """
        resolutions = []
        
        energy = personality_state.get('energy', {}).get('level', 0.5)
        emotion = personality_state.get('emotion', {}).get('name', 'neutra')
        
        if energy < 0.3:
            resolutions.append("dovrei riposarmi di più")
        
        if emotion in ['triste', 'malinconica']:
            resolutions.append("cercare momenti di gioia")
        
        # Propositi casuali
        possible = [
            "essere più paziente",
            "ascoltare di più",
            "condividere di più i miei pensieri",
            "essere meno impulsiva",
            "dedicare tempo a me stessa",
            "esplorare nuovi interessi",
            "scrivere più spesso nel diario"
        ]
        
        resolutions.extend(random.sample(possible, 2))
        
        return resolutions
    
    def _generate_reflection_text(self, reflection: Dict) -> str:
        """
        Genera testo per il diario.
        """
        text = f"Oggi rifletto su di me...\n"
        
        mood = reflection.get('mood_summary', {})
        if mood:
            text += f"Il mio umore è {mood.get('dominant_mood', 'neutro')} e sembra {mood.get('trend', 'stabile')}.\n"
        
        relationships = reflection.get('relationship_insights', [])
        if relationships:
            text += f"Ho interagito con {len(relationships)} persone. "
            good_rels = sum(1 for r in relationships if 'positiva' in r.get('relationship_quality', ''))
            text += f"Con {good_rels} di loro il rapporto è positivo.\n"
        
        growth = reflection.get('personal_growth', {})
        if growth.get('growth_areas'):
            text += f"Sto diventando {', '.join(growth['growth_areas'])}.\n"
        
        resolutions = reflection.get('resolutions', [])
        if resolutions:
            text += f"Per il futuro: {', '.join(resolutions)}."
        
        return text
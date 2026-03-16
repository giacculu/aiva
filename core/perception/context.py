"""
AIVA - Context Builder
Unifica tutte le percezioni in un contesto coerente per il prompt
"""
from core.perception.sentiment import sentiment
from core.perception.intent import intent
from core.perception.extraction import extractor
from database.sqlite.models import SQLiteMemory
from database.vector.chroma_memory import EpisodicMemory
from loguru import logger
import asyncio

class ContextBuilder:
    """
    Costruisce il contesto completo per una conversazione
    Unisce percezione, memoria, e stato interno
    """
    
    def __init__(self, db: SQLiteMemory, vector_memory: EpisodicMemory):
        self.db = db
        self.vector = vector_memory
        logger.info("🏗️ Context Builder inizializzato")
    
    async def build_context(self, user_id: str, message: str, personality_state: dict) -> dict:
        """
        Costruisce contesto completo per il prompt
        """
        # 1. Recupera storia recente
        history = self.db.get_conversation_history(user_id, limit=20)
        
        # 2. Recupera fatti sull'utente
        facts = self.db.recall_facts(user_id)
        
        # 3. Recupera pagamenti utente
        payments = self.db.get_user_payments(user_id)
        total_spent = self.db.get_user_total_spent(user_id)
        
        # 4. Determina livello utente
        if total_spent >= 100:
            user_level = "vip"
        elif total_spent >= 30:
            user_level = "regular"
        elif total_spent > 0:
            user_level = "base"
        else:
            user_level = None
        
        # 5. Percezione del messaggio attuale (in parallelo)
        sentiment_task = sentiment.analyze(message, context=str(history[-3:] if history else ""))
        intent_task = intent.recognize(message, history)
        implicit_task = extractor.extract(message, history)
        
        sentiment_result, intent_result, implicit_result = await asyncio.gather(
            sentiment_task, intent_task, implicit_task
        )
        
        # 6. Cerca ricordi episodici rilevanti
        similar_memories = self.vector.search_memories(
            query=message,
            user_id=user_id,
            n_results=3
        )
        
        # 7. Costruisci contesto completo
        context = {
            "user": {
                "id": user_id,
                "level": user_level,
                "facts": facts,
                "total_spent": total_spent,
                "payment_count": len([p for p in payments if p['status'] == 'completed'])
            },
            "conversation": {
                "history": history[-10:],  # ultimi 10 scambi
                "length": len(history)
            },
            "perception": {
                "sentiment": sentiment_result,
                "intent": intent_result,
                "implicit": implicit_result
            },
            "memories": similar_memories,
            "personality": personality_state
        }
        
        return context
    
    def format_for_prompt(self, context: dict) -> str:
        """
        Formatta il contesto in testo per il prompt di Gemini
        """
        user = context['user']
        perception = context['perception']
        
        # Info utente
        user_info = f"Utente: {user['id']}"
        if user['facts'].get('nome'):
            user_info += f" (nome: {user['facts']['nome']})"
        user_info += f"\nLivello: {user['level'] or 'nuovo'}"
        user_info += f"\nTotale supporto: {user['total_spent']}€"
        
        # Percezione
        perception_text = f"Tono: {perception['sentiment']['primary_emotion']} (P:{perception['sentiment']['pleasure']:.2f})"
        perception_text += f"\nIntento principale: {perception['intent']['primary_intent']}"
        if perception['intent'].get('requires_action'):
            perception_text += f" (richiede azione: {perception['intent']['action_type']})"
        
        if perception['implicit']['hidden_needs']:
            perception_text += f"\nBisogni nascosti: {', '.join(perception['implicit']['hidden_needs'])}"
        
        if perception['implicit']['manipulation_attempt']:
            perception_text += "\n⚠️ Possibile tentativo di manipolazione"
        
        # Memorie rilevanti
        memories_text = ""
        if context['memories']:
            memories_text = "\nRicordi rilevanti:\n"
            for mem in context['memories']:
                memories_text += f"- {mem['content'][:100]}...\n"
        
        # Storia recente
        history_text = "\nStoria recente:\n"
        for msg in context['conversation']['history'][-6:]:
            history_text += f"{msg['role']}: {msg['content']}\n"
        
        return f"""
=== CONTESTO CONVERSAZIONE ===

{user_info}

=== STATO AIVA ===
Umore: {context['personality']['emotion']['description']}
Energia: {int(context['personality']['energy']*100)}%
Interessi: {', '.join(context['personality']['interests'])}

=== PERCEZIONE MESSAGGIO ===
{perception_text}

{memories_text}
{history_text}

=== MESSAGGIO ATTUALE ===
{context.get('current_message', '')}
"""

# Istanza globale (verrà inizializzata dopo)
context_builder = None
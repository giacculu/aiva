"""
Gemini Engine – Il motore che genera le risposte
Connette tutti i layer a Google Gemini
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from loguru import logger
from config import config

class GeminiEngine:
    """
    Gestisce la comunicazione con Gemini
    Costruisce prompt complessi e gestisce le risposte
    """
    
    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(config.AI_MODEL)
        
        # Cache delle risposte per evitare ripetizioni
        self.response_cache = {}
        
        # Statistiche
        self.total_requests = 0
        self.total_tokens = 0
        
        self.logger = logger.bind(module="gemini")
        self.logger.info(f"🤖 Gemini inizializzato con modello {config.AI_MODEL}")
    
    async def generate(self,
                      prompt: str,
                      context: Dict,
                      temperature: float = 0.9,
                      max_retries: int = 3) -> str:
        """
        Genera una risposta con retry automatico
        """
        self.total_requests += 1
        
        for attempt in range(max_retries):
            try:
                # Aggiungi contesto al prompt
                enhanced_prompt = self._enhance_prompt(prompt, context)
                
                # Genera risposta
                response = await self._call_gemini(enhanced_prompt, temperature)
                
                # Post-processing
                cleaned = self._clean_response(response)
                
                # Verifica qualità
                if self._check_quality(cleaned, context):
                    return cleaned
                else:
                    self.logger.warning(f"⚠️ Risposta di bassa qualità, tentativo {attempt+1}")
                    
            except Exception as e:
                self.logger.error(f"❌ Errore Gemini (tentativo {attempt+1}): {e}")
                await asyncio.sleep(1 * (attempt + 1))  # Backoff esponenziale
        
        # Fallback
        return self._get_fallback_response(context)
    
    def _enhance_prompt(self, base_prompt: str, context: Dict) -> str:
        """
        Arricchisce il prompt con tutto il contesto disponibile
        """
        sections = []
        
        # 1. Personalità e stato interiore
        if 'inner_state' in context:
            state = context['inner_state']
            sections.append(f"🎭 **IL TUO STATO ATTUALE:**")
            sections.append(f"- Umore: {state.get('mood_description', 'normale')}")
            sections.append(f"- Energia: {int(state.get('energy_mental', 0.5)*100)}%")
            sections.append(f"- Momento: {state.get('time_of_day', 'giorno')}")
            sections.append(f"- Interessi: {state.get('interests', 'vari')}")
        
        # 2. Cosa sai dell'utente
        if 'memory' in context and context['memory']:
            sections.append(f"\n📝 **COSA SAI DI CHI TI SCRIVE:**")
            sections.append(context['memory'])
        
        # 3. Preferenze apprese
        if 'learned_prefs' in context:
            prefs = context['learned_prefs']
            if prefs.get('profile_summary'):
                sections.append(f"\n💡 **COSA HAI IMPARATO SU DI LUI/LEI:**")
                sections.append(prefs['profile_summary'])
        
        # 4. Contesto conversazione
        if 'perception' in context:
            p = context['perception']
            sections.append(f"\n💬 **CONTESTO DELLA CONVERSAZIONE:**")
            sections.append(f"- Intento: {p['intent']['primary']} (confidenza: {int(p['intent']['confidence']*100)}%)")
            sections.append(f"- Bisogno emotivo: {p['intent']['need_description']}")
            sections.append(f"- Sentiment: {p['sentiment']['primary_emotion']} ({p['sentiment']['valence']:.1f})")
            
            if 'context_summary' in p:
                sections.append(f"- {p['context_summary']}")
        
        # 5. Messaggio attuale
        sections.append(f"\n📨 **MESSAGGIO APPENA RICEVUTO:**")
        sections.append(f'"{context.get("user_message", "")}"')
        
        # 6. Prompt base
        sections.append(f"\n🎯 **RISPONDI COME {config.AI_NAME}:**")
        sections.append(base_prompt)
        
        return "\n".join(sections)
    
    async def _call_gemini(self, prompt: str, temperature: float) -> str:
        """
        Chiamata effettiva a Gemini
        """
        response = self.model.generate_content(
            prompt,
            generation_config={
                'temperature': temperature,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 500,
            }
        )
        
        # Aggiorna statistiche (approssimative)
        self.total_tokens += len(prompt.split()) + len(response.text.split())
        
        return response.text
    
    def _clean_response(self, response: str) -> str:
        """
        Pulisce la risposta da artefatti
        """
        # Rimuovi "AIVA:" o "Assistente:" all'inizio
        import re
        response = re.sub(r'^(AIVA:|Assistente:|AI:)\s*', '', response, flags=re.IGNORECASE)
        
        # Rimuovi virgolette esterne
        response = response.strip('"\'')
        
        # Limita lunghezza se necessario (ma con intelligenza)
        words = response.split()
        if len(words) > 200:
            response = ' '.join(words[:200]) + '...'
        
        return response.strip()
    
    def _check_quality(self, response: str, context: Dict) -> bool:
        """
        Verifica che la risposta abbia una qualità minima
        """
        # Troppo corta?
        if len(response.split()) < 3:
            return False
        
        # Troppo generica?
        generic = ['non lo so', 'boh', 'mah', 'forse', 'non saprei']
        if any(g in response.lower() for g in generic) and len(response) < 30:
            return False
        
        # Ripete la domanda?
        user_msg = context.get('user_message', '').lower()
        if user_msg and user_msg in response.lower() and len(user_msg) > 20:
            return False
        
        return True
    
    def _get_fallback_response(self, context: Dict) -> str:
        """
        Risposta di fallback quando tutto fallisce
        """
        fallbacks = [
            "Scusa, ho avuto un problema di connessione. Ridimmi?",
            "Non mi funziona benissimo ora... riprova tra un attimo 💕",
            "Oddio, mi sono persa. Cosa dicevi?",
            "Scusa, ho un po' di problemi tecnici. Ci risentiamo dopo?"
        ]
        import random
        return random.choice(fallbacks)
    
    def get_stats(self) -> Dict:
        """
        Statistiche di utilizzo
        """
        return {
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'cache_size': len(self.response_cache)
        }

# Istanza globale
gemini_engine = GeminiEngine()
"""
Test per i moduli di apprendimento
"""
import pytest
from datetime import datetime, timedelta
from core.learning.feedback import ImplicitFeedback
from core.learning.reinforcement import ImplicitRLHF
from core.learning.evolution import PersonalityEvolution
from core.learning.reflection import SelfReflection

class TestImplicitFeedback:
    """Test per feedback implicito."""
    
    def setup_method(self):
        self.feedback = ImplicitFeedback()
    
    def test_analyze_response(self):
        """Test analisi risposta."""
        result = self.feedback.analyze_response(
            user_id="test_user",
            user_message="Grazie! 😊",
            bot_response="Prego!",
            response_time=10,
            conversation_context={}
        )
        
        assert 'engagement' in result
        assert 'satisfaction' in result
        assert 'interest' in result
        assert 0 <= result['engagement'] <= 1
        assert 0 <= result['satisfaction'] <= 1
    
    def test_engagement_calculation(self):
        """Test calcolo engagement."""
        # Risposta veloce e lunga
        high = self.feedback._calculate_engagement(
            "Questo è un messaggio molto lungo con molte parole per testare l'engagement", 
            5
        )
        
        # Risposta lenta e corta
        low = self.feedback._calculate_engagement("Ok", 600)
        
        assert high > low
    
    def test_satisfaction_calculation(self):
        """Test calcolo soddisfazione."""
        # Positivo
        pos = self.feedback._calculate_satisfaction("Grazie mille! ❤️ Perfetto!")
        # Negativo
        neg = self.feedback._calculate_satisfaction("No, non mi piace")
        
        assert pos > 0.5
        assert neg < 0.5
    
    def test_get_user_trend(self):
        """Test trend utente."""
        # Aggiungi alcuni feedback
        for i in range(5):
            self.feedback.analyze_response(
                user_id="trend_user",
                user_message=f"Messaggio {i}",
                bot_response="Risposta",
                response_time=10,
                conversation_context={}
            )
        
        trend = self.feedback.get_user_trend("trend_user")
        assert isinstance(trend, dict)


class TestImplicitRLHF:
    """Test per RLHF implicito."""
    
    def setup_method(self):
        self.rlhf = ImplicitRLHF()
    
    def test_initial_weights(self):
        """Test pesi iniziali."""
        weights = self.rlhf.get_behavior_params()
        assert 'curiosity' in weights
        assert 'affection' in weights
        assert 'humor' in weights
    
    def test_update_from_feedback(self):
        """Test aggiornamento da feedback."""
        signals = {
            'increase_engagement': 0.8,
            'improve_quality': 0.5
        }
        
        old_curiosity = self.rlhf.weights['curiosity']
        
        adjustments = self.rlhf.update_from_feedback(signals, "test_user")
        
        assert 'curiosity' in adjustments
        assert self.rlhf.weights['curiosity'] > old_curiosity
    
    def test_behavior_decisions(self):
        """Test decisioni comportamentali."""
        # Dovrebbe restituire booleani
        assert isinstance(self.rlhf.should_ask_question(), bool)
        assert isinstance(self.rlhf.should_use_emoji(), bool)
        assert isinstance(self.rlhf.should_be_funny(), bool)


class TestPersonalityEvolution:
    """Test evoluzione personalità."""
    
    def setup_method(self):
        # Mock personality
        class MockPersonality:
            def __init__(self):
                self.traits = {}
        
        self.evolution = PersonalityEvolution(MockPersonality())
    
    def test_initial_traits(self):
        """Test tratti iniziali."""
        traits = self.evolution.get_all_traits()
        assert len(traits) > 0
        assert 'ottimismo' in traits
    
    def test_update_from_experiences(self):
        """Test aggiornamento da esperienze."""
        interactions = [
            {'user_id': 'user1', 'sentiment': 0.5},
            {'user_id': 'user1', 'sentiment': 0.6},
            {'user_id': 'user2', 'sentiment': -0.3}
        ]
        
        old_optimism = self.evolution.traits['ottimismo']
        
        changes = self.evolution.update_from_experiences(interactions, days_passed=1)
        
        # Potrebbe non cambiare sempre, ma non deve crashare
        assert isinstance(changes, dict)
    
    def test_personality_description(self):
        """Test descrizione personalità."""
        desc = self.evolution.get_personality_description()
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestSelfReflection:
    """Test autoriflessione."""
    
    def setup_method(self):
        # Mock
        class MockPersonality:
            def get_state(self):
                return {'energy': {'level': 0.5}, 'emotion': {'name': 'neutra'}}
        
        class MockDiary:
            def __init__(self):
                self.entries = []
            def get_recent(self, limit):
                return self.entries
            def write_reflection(self, topic, reflection):
                pass
        
        class MockEvolution:
            def get_all_traits(self):
                return {'ottimismo': 0.6, 'pazienza': 0.5}
            def evolution_history(self):
                return []
        
        self.reflection = SelfReflection(
            MockPersonality(),
            MockDiary(),
            MockEvolution()
        )
    
    @pytest.mark.asyncio
    async def test_reflect(self):
        """Test ciclo riflessione."""
        result = await self.reflection.reflect(force=True)
        
        assert result is not None
        assert 'mood_summary' in result
        assert 'resolutions' in result
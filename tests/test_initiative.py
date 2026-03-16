"""
Test per i moduli di iniziativa
"""
import pytest
from datetime import datetime, timedelta
from core.initiative.scheduler import InitiativeScheduler
from core.initiative.triggers import InitiativeTriggers

class TestInitiativeScheduler:
    """Test per scheduler iniziative."""
    
    def setup_method(self):
        self.scheduler = InitiativeScheduler()
    
    def test_should_take_initiative(self):
        """Test calcolo probabilità iniziativa."""
        now = datetime.now()
        
        # Utente con interazione recente
        prob_recent = self.scheduler.should_take_initiative(
            user_id="test",
            last_interaction=now - timedelta(hours=2),
            relationship_level="regular",
            current_mood="felice",
            hour=14
        )
        
        # Utente con interazione vecchia
        prob_old = self.scheduler.should_take_initiative(
            user_id="test",
            last_interaction=now - timedelta(days=3),
            relationship_level="vip",
            current_mood="entusiasta",
            hour=20
        )
        
        assert prob_old > prob_recent
        assert 0 <= prob_recent <= 1
        assert 0 <= prob_old <= 1
    
    def test_get_initiative_reason(self):
        """Test generazione ragioni."""
        # Diversi livelli
        vip_reason = self.scheduler.get_initiative_reason(
            "test", "vip", "felice"
        )
        new_reason = self.scheduler.get_initiative_reason(
            "test", None, "normale"
        )
        
        assert isinstance(vip_reason, str)
        assert isinstance(new_reason, str)
        assert len(vip_reason) > 0
        assert len(new_reason) > 0
    
    def test_register_initiative(self):
        """Test registrazione iniziativa."""
        self.scheduler.register_initiative("user1")
        self.scheduler.register_initiative("user2")
        
        assert len(self.scheduler.initiative_history) == 2
        assert self.scheduler.initiative_history[0][1] == "user1"
        assert self.scheduler.initiative_history[1][1] == "user2"


class TestInitiativeTriggers:
    """Test per trigger iniziative."""
    
    def setup_method(self):
        self.triggers = InitiativeTriggers()
    
    def test_check_triggers(self):
        """Test verifica trigger."""
        now = datetime.now()
        
        active = self.triggers.check_triggers(
            user_id="test",
            relationship_level="regular",
            last_interaction=now - timedelta(days=2),
            current_mood="felice"
        )
        
        assert isinstance(active, list)
        # Alcuni trigger potrebbero essere attivi
        
        # Verifica che ogni trigger abbia i campi necessari
        for trigger in active:
            assert 'type' in trigger
            assert 'name' in trigger
            assert 'message' in trigger
            assert 'probability' in trigger
    
    def test_time_triggers_exist(self):
        """Test che i trigger temporali esistano."""
        assert len(self.triggers.time_triggers) > 0
        
        # Verifica struttura
        for trigger in self.triggers.time_triggers:
            assert 'name' in trigger
            assert 'hours' in trigger
            assert 'message' in trigger
            assert 'condition' in trigger
    
    def test_get_random_thought(self):
        """Test generazione pensieri casuali."""
        thought = self.triggers.get_random_thought("test")
        
        if thought is not None:
            assert isinstance(thought, str)
            assert len(thought) > 0
    
    def test_register_trigger_used(self):
        """Test registrazione trigger usato."""
        trigger = {'name': 'test_trigger', 'type': 'test'}
        self.triggers.register_trigger_used(trigger)
        
        assert len(self.triggers.triggers_history) == 1
        assert self.triggers.triggers_history[0]['trigger'] == 'test_trigger'
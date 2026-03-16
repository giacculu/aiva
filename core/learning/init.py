"""
Pacchetto apprendimento: feedback implicito, RLHF, evoluzione e autoriflessione
"""
from core.learning.feedback import ImplicitFeedback
from core.learning.reinforcement import ImplicitRLHF
from core.learning.evolution import PersonalityEvolution
from core.learning.reflection import SelfReflection

__all__ = [
    'ImplicitFeedback',
    'ImplicitRLHF',
    'PersonalityEvolution',
    'SelfReflection'
]
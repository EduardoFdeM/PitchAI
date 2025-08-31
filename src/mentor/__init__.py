"""
Mentor Engine - Sistema de mentoring e gamificação
================================================

Módulo principal do sistema de coaching em tempo real.
"""

from .mentor_engine import MentorEngine
from .coach_feedback import CoachFeedback
from .xp_rules import (
    compute_xp, 
    level_from_xp, 
    get_level_progress, 
    get_xp_breakdown,
    get_level_requirements
)

__all__ = [
    "MentorEngine",
    "CoachFeedback", 
    "compute_xp",
    "level_from_xp",
    "get_level_progress",
    "get_xp_breakdown",
    "get_level_requirements"
] 
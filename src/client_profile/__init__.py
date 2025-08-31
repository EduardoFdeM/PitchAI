"""
Client Profile - Gerenciamento de perfis de clientes
==================================================

Módulo para análise e classificação de clientes.
"""

from .service import ClientProfileService
from .scorer import (
    complexity_score,
    infer_stage,
    extract_topics,
    calculate_engagement_metrics
)

__all__ = [
    "ClientProfileService",
    "complexity_score",
    "infer_stage", 
    "extract_topics",
    "calculate_engagement_metrics"
] 
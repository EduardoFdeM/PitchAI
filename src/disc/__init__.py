"""
DISC Analysis Module
===================

Sistema de análise DISC baseado em transcrições de vendas:
- Extração de features linguísticas/prosódicas
- Cálculo de scores DISC (Dominância, Influência, eStabilidade, Consciência)
- Detecção de lacunas comportamentais
- Geração de planos de treino personalizados
"""

from .extractor import DiscFeatureExtractor
from .scorer import DiscScorer
from .recommender import DiscRecommender
from .batch import DiscBatchJob

__all__ = [
    'DiscFeatureExtractor',
    'DiscScorer', 
    'DiscRecommender',
    'DiscBatchJob'
] 
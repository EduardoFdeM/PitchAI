"""
Sentiment Analysis Module - Feature 3
====================================

Análise de Sentimento Multi-Dimensional para o PitchAI.
Combina análise de texto, prosódia e expressões faciais
para inferir sentimento e engajamento em tempo real.
"""

from .sentiment_service import SentimentService
from .text_analyzer import TextAnalyzer
from .prosody_analyzer import ProsodyAnalyzer
from .vision_analyzer import VisionAnalyzer
from .fusion_engine import FusionEngine
from .keyword_detector import KeywordDetector
from .models import SentimentSample, SentimentEvent, DashboardData, SentimentConfig

__all__ = [
    'SentimentService',
    'TextAnalyzer', 
    'ProsodyAnalyzer',
    'VisionAnalyzer',
    'FusionEngine',
    'KeywordDetector',
    'SentimentSample',
    'SentimentEvent', 
    'DashboardData',
    'SentimentConfig'
] 
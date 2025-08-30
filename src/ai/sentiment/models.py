"""
Modelos de Dados - Feature 3
===========================

Estruturas de dados para análise de sentimento multi-dimensional.
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SentimentSample:
    """Amostra de sentimento conforme SRS."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    call_id: str = ""
    ts_start_ms: int = 0
    ts_end_ms: int = 0
    score_valence: float = 0.0          # -1..+1
    score_engagement: float = 0.0       # 0..1
    weights: Dict[str, float] = field(default_factory=dict)  # pesos usados na fusão
    details: Dict[str, Any] = field(default_factory=dict)    # confidences, features, labels


@dataclass
class SentimentEvent:
    """Evento de sentimento (alerta, sinal)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    call_id: str = ""
    ts_ms: int = 0
    kind: str = ""                      # 'buying_signal'|'risk'|'keyword'|'alert'
    label: str = ""                     # "preco", "ROI", "piloto"
    strength: float = 0.0               # 0..1


@dataclass
class DashboardData:
    """Dados para o dashboard em tempo real."""
    sentiment_percent: int = 0          # 0-100
    engagement_percent: int = 0         # 0-100
    buying_signals_count: int = 0
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    sparkline_data: List[float] = field(default_factory=list)  # últimos 90s


@dataclass
class ProsodyFeatures:
    """Features extraídas da prosódia."""
    f0_mean: float = 0.0               # Frequência fundamental média
    f0_std: float = 0.0                # Desvio padrão F0
    energy_mean: float = 0.0           # Energia média
    energy_std: float = 0.0            # Desvio padrão energia
    speaking_rate: float = 0.0         # Taxa de fala (sílabas/segundo)
    pause_ratio: float = 0.0           # Proporção de pausas
    jitter: float = 0.0                # Jitter (variação F0)
    shimmer: float = 0.0               # Shimmer (variação amplitude)


@dataclass
class KeywordMatch:
    """Match de palavra-gatilho."""
    keyword: str = ""
    confidence: float = 0.0
    position: int = 0                  # posição no texto
    context: str = ""                  # contexto ao redor


@dataclass
class Face:
    """Detecção de face."""
    bbox: List[int] = field(default_factory=list)  # [x, y, w, h]
    landmarks: List[List[int]] = field(default_factory=list)  # pontos faciais
    confidence: float = 0.0


@dataclass
class Expression:
    """Expressão facial detectada."""
    face_id: int = 0
    expression: str = ""               # "joy", "surprise", "doubt", etc.
    confidence: float = 0.0
    intensity: float = 0.0             # 0..1


class SentimentConfig:
    """Configurações de sentimento."""
    
    def __init__(self):
        # Pesos de fusão
        self.text_weight: float = 0.5
        self.voice_weight: float = 0.3
        self.vision_weight: float = 0.2
        
        # Janelas de análise
        self.text_window_s: float = 5.0
        self.prosody_window_s: float = 3.0
        self.vision_window_s: float = 1.0
        
        # Thresholds
        self.sentiment_threshold: float = 0.1
        self.engagement_threshold: float = 0.3
        self.alert_threshold: float = 0.7
        
        # Palavras-gatilho
        self.keywords: List[str] = [
            "preço", "custo", "caro", "barato",
            "contrato", "acordo", "termos",
            "prazo", "tempo", "urgente",
            "piloto", "teste", "demonstração",
            "ROI", "retorno", "investimento",
            "orçamento", "valor", "pagamento",
            "negociação", "desconto", "oferta"
        ]
        
        # Configurações de análise
        self.enable_vision: bool = False
        self.sparkline_window_s: int = 90  # segundos
        self.max_alerts: int = 10 
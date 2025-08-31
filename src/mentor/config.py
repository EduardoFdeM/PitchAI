"""
Mentor Engine - Configuração
==========================

Configurações específicas para o Mentor Engine.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class MentorConfig:
    """Configuração do Mentor Engine."""
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hora
    metrics_cache_ttl_seconds: int = 1800  # 30 minutos
    patterns_cache_ttl_seconds: int = 7200  # 2 horas
    
    # XP settings
    xp_base_values: Dict[str, int] = None
    xp_bonus_values: Dict[str, int] = None
    
    # Coaching settings
    max_tips_per_call: int = 5
    max_feedback_bullets: int = 8
    llm_timeout_seconds: float = 2.0
    
    # Performance settings
    max_concurrent_calls: int = 100
    processing_timeout_ms: int = 5000
    
    # Logging settings
    log_level: str = "INFO"
    enable_performance_logging: bool = True
    enable_debug_logging: bool = False
    
    def __post_init__(self):
        """Configurações pós-inicialização."""
        if self.xp_base_values is None:
            self.xp_base_values = {
                "facil": 10,
                "medio": 20,
                "dificil": 40
            }
        
        if self.xp_bonus_values is None:
            self.xp_bonus_values = {
                "objeção_dominante": 10,
                "avanço_stage": 15,
                "equilíbrio_fala": 5,
                "redução_complexidade": 10,
                "engajamento_alto": 5,
                "sentimento_positivo": 5
            }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MentorConfig':
        """Criar configuração a partir de dict."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dict."""
        return {
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "metrics_cache_ttl_seconds": self.metrics_cache_ttl_seconds,
            "patterns_cache_ttl_seconds": self.patterns_cache_ttl_seconds,
            "xp_base_values": self.xp_base_values,
            "xp_bonus_values": self.xp_bonus_values,
            "max_tips_per_call": self.max_tips_per_call,
            "max_feedback_bullets": self.max_feedback_bullets,
            "llm_timeout_seconds": self.llm_timeout_seconds,
            "max_concurrent_calls": self.max_concurrent_calls,
            "processing_timeout_ms": self.processing_timeout_ms,
            "log_level": self.log_level,
            "enable_performance_logging": self.enable_performance_logging,
            "enable_debug_logging": self.enable_debug_logging
        }


# Configuração padrão
DEFAULT_CONFIG = MentorConfig() 
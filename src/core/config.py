"""
PitchAI - Configuração da Aplicação
================================

Configurações centralizadas para todos os módulos da aplicação.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioConfig:
    """Configuração de áudio."""
    sample_rate: int = 16000
    chunk_duration_ms: int = 1000
    chunk_size: int = 1024  # frames por buffer
    channels: int = 1
    device_name: Optional[str] = None  # None = dispositivo padrão


@dataclass
class Config:
    """Configuração principal da aplicação."""
    
    # ===== DIRETÓRIOS =====
    app_dir: Path
    data_dir: Path
    models_dir: Path
    logs_dir: Path
    cache_dir: Path
    
    # ===== AUDIO =====
    audio: AudioConfig
    
    # ===== AI =====
    onnx_providers: list = None  # ['CPUExecutionProvider']
    model_cache_dir: Optional[Path] = None
    
    # ===== SENTIMENT =====
    sentiment_update_interval_ms: int = 500
    sentiment_threshold: float = 0.6
    
    # ===== UI =====
    window_width: int = 480
    window_height: int = 853  # 9:16 ratio
    theme: str = "glassmorphism"
    
    def __post_init__(self):
        """Configurações pós-inicialização."""
        if self.onnx_providers is None:
            self.onnx_providers = ['CPUExecutionProvider']
        
        if self.model_cache_dir is None:
            self.model_cache_dir = self.cache_dir / "models"
        
        # Criar diretórios se não existirem
        for directory in [self.data_dir, self.models_dir, self.logs_dir, 
                         self.cache_dir, self.model_cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_model_path(self, filename: str) -> Path:
        """Obter caminho completo para um arquivo de modelo."""
        return self.models_dir / filename


def create_config(app_dir: Optional[Path] = None) -> Config:
    """Criar configuração padrão da aplicação."""
    if app_dir is None:
        # Usar diretório atual se não especificado
        app_dir = Path.cwd()
    
    return Config(
        app_dir=app_dir,
        data_dir=app_dir / "data",
        models_dir=app_dir / "models",
        logs_dir=app_dir / "logs",
        cache_dir=app_dir / "cache",
        
        # Configurações de áudio
        audio=AudioConfig(
            sample_rate=16000,
            chunk_duration_ms=1000,
            chunk_size=1024,
            channels=1
        ),
        
        # Configurações AI
        onnx_providers=['CPUExecutionProvider'],
        
        # Configurações de sentimento
        sentiment_update_interval_ms=500,
        sentiment_threshold=0.6,
        
        # Configurações UI
        window_width=480,
        window_height=853,
        theme="glassmorphism"
    )

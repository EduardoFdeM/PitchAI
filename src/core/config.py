"""
Configurações Globais do PitchAI
===============================

Gerencia todas as configurações da aplicação,
incluindo paths, parâmetros de IA e interface.
"""

import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Configurações de áudio."""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format: str = "int16"
    device_index: int = None  # Auto-detect


@dataclass
class AIConfig:
    """Configurações de IA e NPU."""
    use_npu: bool = True
    model_precision: str = "fp16"  # fp16, fp32
    max_concurrent_models: int = 5
    whisper_model: str = "whisper-base"
    sentiment_model: str = "distilbert-sentiment"
    
    # Paths dos modelos
    models_dir: Path = Path("models")
    cache_dir: Path = Path("cache")


@dataclass
class UIConfig:
    """Configurações de interface."""
    theme: str = "glassmorphism"
    window_width: int = 1200
    window_height: int = 800
    always_on_top: bool = False
    minimize_to_tray: bool = True


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados."""
    db_path: Path = Path("data/pitchai.db")
    backup_enabled: bool = True
    backup_interval: int = 3600  # segundos


class Config:
    """Configuração principal do PitchAI."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent.parent
        self.audio = AudioConfig()
        self.ai = AIConfig()
        self.ui = UIConfig()
        self.database = DatabaseConfig()
        
        # Criar diretórios necessários
        self._create_directories()
        
    def _create_directories(self):
        """Criar diretórios necessários."""
        directories = [
            self.app_dir / "data",
            self.app_dir / "models", 
            self.app_dir / "cache",
            self.app_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def get_model_path(self, model_name: str) -> Path:
        """Obter caminho para um modelo específico."""
        return self.app_dir / "models" / f"{model_name}.onnx"
    
    def get_database_path(self) -> Path:
        """Obter caminho completo do banco de dados."""
        return self.app_dir / self.database.db_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            "audio": self.audio.__dict__,
            "ai": self.ai.__dict__, 
            "ui": self.ui.__dict__,
            "database": self.database.__dict__
        }

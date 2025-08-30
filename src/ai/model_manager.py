"""
Model Manager - Gerenciador de Modelos ONNX
==========================================

Gerencia carregamento e configuração de modelos ONNX
para todas as features do PitchAI.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️ ONNX Runtime não disponível.")


@dataclass
class ModelEntry:
    """Entrada de modelo no manifesto."""
    name: str
    path: str
    ep: List[str]
    input_type: str
    quant: str
    description: str
    version: str
    size_mb: int
    latency_target_ms: int


class ModelManager:
    """Gerenciador de modelos ONNX."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.manifest_path = config.app_dir / "models" / "manifest.json"
        self.models: Dict[str, ModelEntry] = {}
        self.loaded_sessions: Dict[str, any] = {}
        
    def load_manifest(self):
        """Carregar manifesto de modelos."""
        try:
            if not self.manifest_path.exists():
                self.logger.warning(f"⚠️ Manifesto não encontrado: {self.manifest_path}")
                return
            
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Converter para ModelEntry
            for name, data in manifest_data.items():
                model_entry = ModelEntry(
                    name=name,
                    path=data.get("path", ""),
                    ep=data.get("ep", []),
                    input_type=data.get("input", ""),
                    quant=data.get("quant", ""),
                    description=data.get("description", ""),
                    version=data.get("version", ""),
                    size_mb=data.get("size_mb", 0),
                    latency_target_ms=data.get("latency_target_ms", 1000)
                )
                self.models[name] = model_entry
            
            self.logger.info(f"✅ Manifesto carregado: {len(self.models)} modelos")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar manifesto: {e}")
    
    def get_model_entry(self, model_name: str) -> Optional[ModelEntry]:
        """Obter entrada de modelo."""
        return self.models.get(model_name)
    
    def get_available_providers(self) -> List[str]:
        """Obter providers ONNX disponíveis."""
        if not ONNX_AVAILABLE:
            return []
        
        providers = ort.get_available_providers()
        self.logger.info(f"Providers disponíveis: {providers}")
        return providers
    
    def create_provider_list(self, model_entry: ModelEntry) -> List:
        """Criar lista de providers para um modelo."""
        if not ONNX_AVAILABLE:
            return []
        
        providers = []
        available_providers = self.get_available_providers()
        
        # Mapear providers do manifesto para ONNX Runtime
        provider_mapping = {
            "QNN": "QNNExecutionProvider",
            "CPU": "CPUExecutionProvider",
            "DML": "DmlExecutionProvider",
            "CUDA": "CUDAExecutionProvider"
        }
        
        for ep in model_entry.ep:
            onnx_provider = provider_mapping.get(ep, ep)
            if onnx_provider in available_providers:
                if onnx_provider == "QNNExecutionProvider":
                    providers.append((onnx_provider, {}))
                else:
                    providers.append(onnx_provider)
                self.logger.info(f"✅ Provider {ep} ({onnx_provider}) adicionado")
            else:
                self.logger.warning(f"⚠️ Provider {ep} ({onnx_provider}) não disponível")
        
        # Garantir que pelo menos CPU está disponível
        if "CPUExecutionProvider" not in providers and "CPUExecutionProvider" in available_providers:
            providers.append("CPUExecutionProvider")
            self.logger.info("✅ CPU provider adicionado como fallback")
        
        return providers
    
    def load_model_session(self, model_name: str) -> Optional[any]:
        """Carregar sessão ONNX para um modelo."""
        if not ONNX_AVAILABLE:
            self.logger.warning("⚠️ ONNX Runtime não disponível")
            return None
        
        if model_name in self.loaded_sessions:
            return self.loaded_sessions[model_name]
        
        model_entry = self.get_model_entry(model_name)
        if not model_entry:
            self.logger.error(f"❌ Modelo {model_name} não encontrado no manifesto")
            return None
        
        try:
            # Construir caminho completo
            model_path = self.config.app_dir / model_entry.path
            
            if not model_path.exists():
                self.logger.warning(f"⚠️ Arquivo de modelo não encontrado: {model_path}")
                return None
            
            # Criar lista de providers
            providers = self.create_provider_list(model_entry)
            
            if not providers:
                self.logger.error(f"❌ Nenhum provider disponível para {model_name}")
                return None
            
            # Carregar sessão
            session = ort.InferenceSession(str(model_path), providers=providers)
            
            # Fazer warmup
            self._warmup_session(session, model_entry)
            
            # Armazenar sessão
            self.loaded_sessions[model_name] = session
            
            self.logger.info(f"✅ Modelo {model_name} carregado com sucesso")
            self.logger.info(f"   Path: {model_path}")
            self.logger.info(f"   Providers: {providers}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar modelo {model_name}: {e}")
            return None
    
    def _warmup_session(self, session, model_entry: ModelEntry):
        """Fazer warmup da sessão."""
        try:
            # Criar input dummy baseado no tipo
            if model_entry.input_type == "audio_16k_mono":
                # Áudio dummy: 1 segundo de ruído
                dummy_input = np.random.normal(0, 0.1, 16000).astype(np.float32)
                dummy_input = dummy_input[np.newaxis, :]  # [1, T]
            elif model_entry.input_type == "text_tokens":
                # Tokens dummy: sequência de IDs
                dummy_input = np.array([[1, 2, 3, 4, 5]], dtype=np.int64)
            else:
                # Input genérico
                dummy_input = np.random.normal(0, 1, (1, 10)).astype(np.float32)
            
            # Inferência dummy
            input_name = session.get_inputs()[0].name
            session.run(None, {input_name: dummy_input})
            
            self.logger.info(f"✅ Warmup concluído para {model_entry.name}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro no warmup de {model_entry.name}: {e}")
    
    def get_session(self, model_name: str) -> Optional[any]:
        """Obter sessão de modelo (carrega se necessário)."""
        if model_name not in self.loaded_sessions:
            return self.load_model_session(model_name)
        return self.loaded_sessions[model_name]
    
    def list_models(self) -> List[str]:
        """Listar modelos disponíveis."""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Obter informações de um modelo."""
        model_entry = self.get_model_entry(model_name)
        if not model_entry:
            return None
        
        return {
            "name": model_entry.name,
            "path": model_entry.path,
            "description": model_entry.description,
            "version": model_entry.version,
            "size_mb": model_entry.size_mb,
            "latency_target_ms": model_entry.latency_target_ms,
            "loaded": model_name in self.loaded_sessions
        }
    
    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando recursos do Model Manager...")
        self.loaded_sessions.clear()
        self.logger.info("✅ Model Manager limpo") 
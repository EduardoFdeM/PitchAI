"""
ONNX Manager - Gerenciador de Modelos ONNX
==========================================

Coordena todos os modelos ONNX para processamento simultâneo
de áudio e análise. Integra com ModelManager para carregamento unificado.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = None


class ONNXWorkerThread(QThread):
    """Thread worker para processamento ONNX."""
    
    result_ready = pyqtSignal(str, dict)  # model_name, result
    
    def __init__(self, model_name: str, model_path: str, input_data: Any):
        super().__init__()
        self.model_name = model_name
        self.model_path = model_path
        self.input_data = input_data
        self.session = None
    
    def run(self):
        """Executar inferência ONNX."""
        try:
            # TODO: Implementar inferência real
            # Por enquanto, simular resultado
            if self.model_name == "whisper":
                result = {
                    "text": "Texto transcrito de exemplo",
                    "confidence": 0.95,
                    "speaker_id": "vendor"
                }
            elif self.model_name == "sentiment":
                result = {
                    "sentiment": 0.72,
                    "emotion": "positive",
                    "engagement": 0.85
                }
            else:
                result = {"status": "processed"}
            
            self.result_ready.emit(self.model_name, result)
            
        except Exception as e:
            logging.error(f"Erro no worker ONNX {self.model_name}: {e}")


class ONNXManager(QObject):
    """Gerenciador principal de modelos ONNX."""
    
    # Sinais
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas
    objection_detected = pyqtSignal(str, list) # objeção, sugestões
    onnx_status_changed = pyqtSignal(str)        # status
    
    def __init__(self, config, model_manager=None):
        super().__init__()
        self.config = config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Estado do ONNX
        self.is_initialized = False
        self.available_providers = []
        self.loaded_models = {}
        self.active_workers = {}
        
        # Timer para simular processamento contínuo
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self._simulate_processing)
    
    def initialize(self):
        """Inicializar ONNX e carregar modelos."""
        try:
            self.logger.info("Inicializando ONNX Manager...")
            
            # Verificar disponibilidade do ONNX Runtime
            if not ONNX_AVAILABLE:
                raise ImportError("ONNX Runtime nao disponivel")
            
            # Verificar providers disponíveis
            self._check_available_providers()
            
            # Carregar modelos essenciais
            self._load_models()
            
            self.is_initialized = True
            self.onnx_status_changed.emit("connected")
            self.logger.info("ONNX Manager inicializado")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar ONNX: {e}")
            self.onnx_status_changed.emit("error")
            # Continuar em modo simulação
            self._enable_simulation_mode()
    
    def _check_available_providers(self):
        """Verificar providers ONNX disponíveis."""
        self.available_providers = ort.get_available_providers()
        self.logger.info(f"Providers disponiveis: {self.available_providers}")
        
        # Verificar providers disponíveis
        if "CPUExecutionProvider" in self.available_providers:
            self.logger.info("CPU Execution Provider detectado")
        if "CUDAExecutionProvider" in self.available_providers:
            self.logger.info("CUDA Execution Provider detectado")
        if "DmlExecutionProvider" in self.available_providers:
            self.logger.info("DirectML Execution Provider detectado")
    
    def _load_models(self):
        """Carregar modelos ONNX."""
        if self.model_manager:
            # Usar ModelManager se disponível
            self.model_manager.load_manifest()
            
            # Carregar modelos essenciais
            essential_models = ["whisper_base", "distilbert_sentiment", "bert_objection"]
            
            for model_name in essential_models:
                try:
                    session = self.model_manager.load_model_session(model_name)
                    if session:
                        self.loaded_models[model_name] = {
                            "session": session,
                            "status": "loaded"
                        }
                        self.logger.info(f"Modelo {model_name} carregado via ModelManager")
                    else:
                        self.logger.warning(f"Modelo {model_name} nao pode ser carregado")
                except Exception as e:
                    self.logger.error(f"Erro ao carregar {model_name}: {e}")
        else:
            # Fallback para carregamento manual
            models_to_load = {
                "whisper": "whisper-base.onnx",
                "sentiment": "distilbert-sentiment.onnx", 
                "objection": "bert-objection.onnx",
                "speaker": "ecapa-speaker.onnx"
            }
            
            for model_name, filename in models_to_load.items():
                model_path = self.config.models_dir / filename
                
                if model_path.exists():
                    try:
                        # TODO: Carregar modelo real
                        # session = ort.InferenceSession(str(model_path), providers=...)
                        self.loaded_models[model_name] = {
                            "path": model_path,
                            "status": "loaded"
                        }
                        self.logger.info(f"Modelo {model_name} carregado")
                    except Exception as e:
                        self.logger.error(f"Erro ao carregar {model_name}: {e}")
                else:
                    self.logger.warning(f"Modelo {filename} nao encontrado")
    
    def _enable_simulation_mode(self):
        """Habilitar modo de simulação."""
        self.logger.info("Habilitando modo de simulacao ONNX")
        self.is_initialized = True
        self.onnx_status_changed.emit("simulation")
        
        # Simular modelos carregados
        self.loaded_models = {
            "whisper": {"status": "simulated"},
            "sentiment": {"status": "simulated"},
            "objection": {"status": "simulated"},
            "speaker": {"status": "simulated"}
        }
    
    def process_audio(self, audio_data: np.ndarray):
        """Processar áudio através da pipeline ONNX."""
        if not self.is_initialized:
            return
        
        try:
            # Iniciar processamento assíncrono para múltiplos modelos
            self._process_transcription(audio_data)
            self._process_sentiment_analysis(audio_data)
            self._process_objection_detection(audio_data)
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de audio: {e}")
    
    def _process_transcription(self, audio_data: np.ndarray):
        """Processar transcrição via Whisper."""
        if "whisper" not in self.loaded_models:
            return
        
        # Criar worker thread para Whisper
        worker = ONNXWorkerThread("whisper", "", audio_data)
        worker.result_ready.connect(self._handle_transcription_result)
        worker.start()
        
        self.active_workers["whisper"] = worker
    
    def _process_sentiment_analysis(self, audio_data: np.ndarray):
        """Processar análise de sentimento."""
        if "sentiment" not in self.loaded_models:
            return
        
        worker = ONNXWorkerThread("sentiment", "", audio_data)
        worker.result_ready.connect(self._handle_sentiment_result)
        worker.start()
        
        self.active_workers["sentiment"] = worker
    
    def _process_objection_detection(self, audio_data: np.ndarray):
        """Processar detecção de objeções."""
        if "objection" not in self.loaded_models:
            return
        
        # TODO: Implementar detecção real de objeções
        pass
    
    def _handle_transcription_result(self, model_name: str, result: dict):
        """Processar resultado da transcrição."""
        if model_name == "whisper":
            text = result.get("text", "")
            speaker_id = result.get("speaker_id", "unknown")
            
            if text.strip():
                self.transcription_ready.emit(text, speaker_id)
                
                # Verificar se há objeções no texto
                self._check_for_objections(text)
    
    def _handle_sentiment_result(self, model_name: str, result: dict):
        """Processar resultado da análise de sentimento."""
        if model_name == "sentiment":
            self.sentiment_updated.emit(result)
    
    def _check_for_objections(self, text: str):
        """Verificar objeções no texto e sugerir respostas."""
        objection_keywords = ["caro", "preço", "barato", "concorrente", "pensar"]
        
        text_lower = text.lower()
        for keyword in objection_keywords:
            if keyword in text_lower:
                # Simular sugestões
                suggestions = [
                    {
                        "text": f"Entendo sua preocupacao sobre {keyword}. Vamos falar sobre o valor...",
                        "confidence": 0.9,
                        "category": "Objeção de Preço"
                    },
                    {
                        "text": "Posso mostrar um case de sucesso similar ao seu...",
                        "confidence": 0.85,
                        "category": "Prova Social"
                    }
                ]
                
                self.objection_detected.emit(keyword, suggestions)
                break
    
    def _simulate_processing(self):
        """Simular processamento contínuo para demo."""
        # Simular transcrição periódica
        import random
        
        sample_texts = [
            "Estou interessado na sua solução",
            "Qual é o preço do sistema?",
            "Preciso conversar com minha equipe",
            "Isso parece interessante"
        ]
        
        if random.random() < 0.3:  # 30% chance
            text = random.choice(sample_texts)
            speaker = random.choice(["vendor", "client"])
            self.transcription_ready.emit(text, speaker)
    
    def start_demo_mode(self):
        """Iniciar modo de demonstração."""
        self.processing_timer.start(5000)  # A cada 5 segundos
    
    def stop_demo_mode(self):
        """Parar modo de demonstração."""
        self.processing_timer.stop()
    
    def cleanup(self):
        """Limpar recursos do ONNX."""
        self.logger.info("Limpando recursos ONNX...")
        
        # Parar workers ativos
        for worker in self.active_workers.values():
            if worker.isRunning():
                worker.quit()
                worker.wait()
        
        self.active_workers.clear()
        self.loaded_models.clear()
        self.stop_demo_mode()
        
        # Limpar ModelManager se disponível
        if self.model_manager:
            self.model_manager.cleanup()
        
        self.logger.info("ONNX Manager finalizado")


# Alias para compatibilidade
NPUManager = ONNXManager

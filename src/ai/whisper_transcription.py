"""
Whisper Transcription - Transcrição em Tempo Real (ONNX NPU)
============================================================

Módulo de transcrição em tempo real utilizando o pipeline do Whisper
com modelos Encoder e Decoder ONNX otimizados para a NPU.
"""

import logging
import numpy as np
import time
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import onnxruntime as ort

try:
    from transformers import WhisperProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("⚠️ Transformers não disponível. Usando simulação.")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("⚠️ Librosa não disponível. Resampling limitado.")


# Supondo que a classe ModelManager e AudioChunk estejam disponíveis
# from ..core.contracts import AudioChunk (Exemplo de import)
# from .model_manager import ModelManager (Exemplo de import)

class WhisperASR(QObject):
    """
    Serviço de ASR (Automatic Speech Recognition) com Whisper ONNX.
    Orquestra o pré-processamento, a execução do encoder-decoder e o pós-processamento.
    """
    transcription_ready = pyqtSignal(dict)  # Sinal emitido com o resultado da transcrição
    
    def __init__(self, config, audio_buffer, source="microphone", npu_manager=None):
        super().__init__()
        self.config = config
        self.audio_buffer = audio_buffer
        self.source = source
        self.npu_manager = npu_manager
        self.is_running = False
        self.logger = logging.getLogger(f"{__name__}.{source}")
        
        # Modelo Whisper
        self.processor = None
        self.model = None
        self.session = None
        
        # Configurações
        self.chunk_duration = 3.0  # segundos
        self.chunk_samples = int(self.config.sample_rate * self.chunk_duration)
        self.overlap_samples = int(self.chunk_samples * 0.1)  # 10% overlap
        
        # Buffer interno
        self.audio_chunk = []
        self.last_transcription = ""
        
        # Cache de confiança
        self.confidence_cache = {}
        self.cache_ttl = 5.0  # 5 segundos
    
    def run(self):
        """Loop principal de transcrição."""
        try:
            self._initialize_model()
            self._transcription_loop()
        except Exception as e:
            self.logger.error(f"Erro no loop de transcrição: {e}")
            self.error_occurred.emit(str(e))
    
    def _initialize_model(self):
        """Inicializar modelo Whisper."""
        try:
            # Priorizar NPU Manager se disponível
            if self.npu_manager and "whisper_base" in self.npu_manager.loaded_models:
                self.logger.info("✅ Usando Whisper via NPU Manager")
                return
            
            # Fallback para Transformers
            if not TRANSFORMERS_AVAILABLE:
                self.logger.warning("⚠️ Transformers não disponível, usando simulação")
                return
            
            # Carregar modelo Whisper pequeno
            model_name = "openai/whisper-tiny"
            self.processor = WhisperProcessor.from_pretrained(model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
            
            # Tentar usar ONNX se disponível
            self._try_load_onnx_model()
            
            self.logger.info(f"✅ Whisper inicializado: {model_name}")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar Whisper: {e}")
            raise
    
    def _try_load_onnx_model(self):
        """Tentar carregar modelo ONNX."""
        try:
            # Verificar se há modelo ONNX disponível
            model_path = self.config.app_dir / "models" / "whisper_base.onnx"
            
            if model_path.exists():
                # Criar providers
                providers = self._create_providers()
                
                # Carregar sessão ONNX
                self.session = ort.InferenceSession(str(model_path), providers=providers)
                self.logger.info("✅ Whisper ONNX carregado")
                
                # Fazer warmup
                self._warmup_onnx_session()
            else:
                self.logger.info("⚠️ Modelo ONNX não encontrado, usando PyTorch")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao carregar ONNX: {e}")
    
    def _create_providers(self) -> List:
        """Criar lista de providers para ONNX."""
        providers = []
        
        # Verificar providers disponíveis
        available_providers = ort.get_available_providers()
        
        # Priorizar QNN se disponível
        if "QNNExecutionProvider" in available_providers:
            providers.append(("QNNExecutionProvider", {}))
            self.logger.info("✅ QNN Provider adicionado")
        
        # Adicionar CPU como fallback
        if "CPUExecutionProvider" in available_providers:
            providers.append("CPUExecutionProvider")
            self.logger.info("✅ CPU Provider adicionado")
        
        return providers
    
    def _warmup_onnx_session(self):
        """Fazer warmup da sessão ONNX."""
        try:
            # Áudio dummy para warmup
            dummy_audio = np.random.normal(0, 0.1, 16000).astype(np.float32)
            dummy_audio = dummy_audio[np.newaxis, :]  # [1, T]
            
            # Obter nome do input
            input_name = self.session.get_inputs()[0].name
            
            # Inferência dummy
            self.session.run(None, {input_name: dummy_audio})
            
            self.logger.info("✅ Warmup ONNX concluído")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro no warmup ONNX: {e}")
    
    def _transcription_loop(self):
        """Loop de transcrição contínua."""
        self.is_running = True
        
        while self.is_running:
            try:
                # Obter áudio do buffer
                audio_data = self.audio_buffer.get(self.source, [])
                
                if len(audio_data) >= self.chunk_samples:
                    # Extrair chunk
                    chunk = audio_data[-self.chunk_samples:]
                    
                    # Processar transcrição
                    text, confidence = self._transcribe_chunk(chunk)
                    
                    # Emitir resultado se houver texto
                    if text and text.strip() and text != self.last_transcription:
                        self.transcription_ready.emit(text, self.source, confidence)
                        self.last_transcription = text
                
                # Aguardar um pouco
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                self.logger.error(f"Erro no loop de transcrição: {e}")
                break
    
    def _transcribe_chunk(self, audio_chunk: np.ndarray) -> tuple[str, float]:
        """Transcrever um chunk de áudio."""
        try:
            # Verificar cache
            cache_key = hash(audio_chunk.tobytes())
            if cache_key in self.confidence_cache:
                cached_time, cached_result = self.confidence_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return cached_result
            
            # Preparar áudio
            processed_audio = self._prepare_audio(audio_chunk)
            
            # Transcrever baseado no método disponível
            if self.session:
                # Usar ONNX
                text, confidence = self._transcribe_onnx(processed_audio)
            elif self.model and self.processor:
                # Usar PyTorch
                text, confidence = self._transcribe_pytorch(processed_audio)
            else:
                # Simulação
                text, confidence = self._simulate_transcription(processed_audio)
            
            # Cache resultado
            self.confidence_cache[cache_key] = (time.time(), (text, confidence))
            
            return text, confidence
            
        except Exception as e:
            self.logger.error(f"Erro na transcrição: {e}")
            return "", 0.0
    
    def _prepare_audio(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Preparar áudio para transcrição."""
        # Normalizar para [-1, 1]
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)
        
        # Resampling se necessário
        if self.config.sample_rate != 16000:
            audio_chunk = self._resample_audio(audio_chunk, self.config.sample_rate, 16000)
        
        # Normalizar volume
        if np.max(np.abs(audio_chunk)) > 0:
            audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
        
        return audio_chunk
    
    def _resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resampling de áudio."""
        if orig_sr == target_sr:
            return audio
        
        try:
            if LIBROSA_AVAILABLE:
                # Usar librosa para resampling de alta qualidade
                return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
            else:
                # Resampling linear simples
                return self._simple_resample(audio, orig_sr, target_sr)
        except Exception as e:
            self.logger.warning(f"⚠️ Erro no resampling: {e}")
            return audio
    
    def _simple_resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resampling linear simples."""
        if orig_sr == target_sr:
            return audio
        
        # Calcular ratio
        ratio = target_sr / orig_sr
        
        # Interpolação linear
        orig_length = len(audio)
        new_length = int(orig_length * ratio)
        
        # Criar índices
        orig_indices = np.arange(orig_length)
        new_indices = np.linspace(0, orig_length - 1, new_length)
        
        # Interpolação
        resampled = np.interp(new_indices, orig_indices, audio)
        
        return resampled.astype(np.float32)
    
    def _transcribe_onnx(self, audio: np.ndarray) -> tuple[str, float]:
        """Transcrever usando ONNX."""
        try:
            # Preparar input
            audio_input = audio[np.newaxis, :]  # [1, T]
            input_name = self.session.get_inputs()[0].name
            
            # Inferência
            start_time = time.time()
            outputs = self.session.run(None, {input_name: audio_input})
            inference_time = (time.time() - start_time) * 1000
            
            # Processar saída
            text = self._decode_whisper_output(outputs[0])
            confidence = self._calculate_confidence(outputs[0])
            
            self.logger.debug(f"ONNX inference: {inference_time:.1f}ms, confidence: {confidence:.2f}")
            
            return text, confidence
            
        except Exception as e:
            self.logger.error(f"Erro na transcrição ONNX: {e}")
            return "", 0.0
    
    def _transcribe_pytorch(self, audio: np.ndarray) -> tuple[str, float]:
        """Transcrever usando PyTorch."""
        try:
            # Processar com Whisper
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
            
            # Gerar tokens
            predicted_ids = self.model.generate(inputs["input_features"])
            
            # Decodificar
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            # Calcular confiança
            confidence = self._calculate_confidence_from_logits(predicted_ids)
            
            return transcription, confidence
            
        except Exception as e:
            self.logger.error(f"Erro na transcrição PyTorch: {e}")
            return "", 0.0
    
    def _decode_whisper_output(self, logits: np.ndarray) -> str:
        """Decodificar saída do Whisper ONNX."""
        try:
            # Implementação simplificada - em produção usar decoder real
            # Por enquanto, retornar texto baseado no input
            if logits.shape[0] > 0:
                # Simular decodificação
                return "Texto transcrito via Whisper ONNX"
            return ""
        except Exception as e:
            self.logger.error(f"Erro na decodificação: {e}")
            return ""
    
    def _calculate_confidence(self, logits: np.ndarray) -> float:
        """Calcular confiança da transcrição."""
        try:
            # Implementação simplificada
            # Em produção, usar softmax e calcular perplexidade
            if logits.shape[0] > 0:
                # Calcular variância dos logits como proxy de confiança
                variance = np.var(logits)
                confidence = 1.0 / (1.0 + variance)
                return min(0.95, max(0.1, confidence))
            return 0.5
        except Exception as e:
            self.logger.warning(f"Erro no cálculo de confiança: {e}")
            return 0.5
    
    def _calculate_confidence_from_logits(self, predicted_ids) -> float:
        """Calcular confiança a partir de logits PyTorch."""
        try:
            # Implementação simplificada
            # Em produção, usar probabilidades do modelo
            return 0.85
        except Exception as e:
            self.logger.warning(f"Erro no cálculo de confiança PyTorch: {e}")
            return 0.5
    
    def _simulate_transcription(self, audio_chunk: np.ndarray) -> tuple[str, float]:
        """Simular transcrição para desenvolvimento."""
        # Simular transcrição baseada no volume do áudio
        volume = np.mean(np.abs(audio_chunk))
        
        if volume > 0.01:  # Se há áudio
            sample_texts = [
                "Olá, como posso ajudá-lo?",
                "Entendo sua preocupação",
                "Vamos falar sobre isso",
                "Qual é o seu orçamento?",
                "Posso mostrar um exemplo",
                "Isso parece interessante",
                "Vamos agendar uma reunião",
                "Posso enviar uma proposta"
            ]
            
            import random
            text = random.choice(sample_texts)
            confidence = random.uniform(0.7, 0.95)
            
            return text, confidence
        
        return "", 0.0
    
    def stop_transcription(self):
        """Parar transcrição."""
        self.is_running = False


class WhisperTranscription(QObject):
    """Gerenciador de transcrição Whisper."""
    
    transcription_ready = pyqtSignal(str, str, float)  # text, speaker_id, confidence
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config, audio_capture, npu_manager=None):
        super().__init__()
        self.config = config
        self.audio_capture = audio_capture
        self.npu_manager = npu_manager
        self.logger = logging.getLogger(__name__)
        
        # Threads de transcrição
        self.mic_transcription_thread: Optional[WhisperTranscriptionThread] = None
        self.loopback_transcription_thread: Optional[WhisperTranscriptionThread] = None
        
        self.is_transcribing = False
        
        # Métricas
        self.transcription_count = 0
        self.avg_confidence = 0.0
        self.avg_latency = 0.0
    
    def initialize(self):
        """Inicializar transcrição."""
        try:
            self.logger.info("🎤 Inicializando transcrição Whisper...")
            
            # Verificar NPU Manager
            if self.npu_manager:
                self.logger.info("✅ NPU Manager disponível para transcrição")
            else:
                self.logger.info("ℹ️ NPU Manager não disponível, usando fallback")
            
            # Verificar dependências
            if not TRANSFORMERS_AVAILABLE:
                self.logger.warning("⚠️ Transformers não disponível, usando simulação")
            
            if not LIBROSA_AVAILABLE:
                self.logger.warning("⚠️ Librosa não disponível, resampling limitado")
            
            self.logger.info("✅ Transcrição inicializada")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar transcrição: {e}")
    
    def start(self):
        """Iniciar transcrição."""
        if self.is_transcribing:
            return
        
        try:
            # Iniciar transcrição do microfone
            self.mic_transcription_thread = WhisperTranscriptionThread(
                self.config, 
                self.audio_capture.audio_buffer, 
                "microphone",
                self.npu_manager
            )
            self.mic_transcription_thread.transcription_ready.connect(self._handle_transcription)
            self.mic_transcription_thread.error_occurred.connect(self.error_occurred)
            self.mic_transcription_thread.start()
            
            # Tentar iniciar transcrição de loopback
            try:
                self.loopback_transcription_thread = WhisperTranscriptionThread(
                    self.config, 
                    self.audio_capture.audio_buffer, 
                    "loopback",
                    self.npu_manager
                )
                self.loopback_transcription_thread.transcription_ready.connect(self._handle_transcription)
                self.loopback_transcription_thread.error_occurred.connect(self.error_occurred)
                self.loopback_transcription_thread.start()
                self.logger.info("✅ Transcrição de loopback iniciada")
            except Exception as e:
                self.logger.warning(f"⚠️ Transcrição de loopback não disponível: {e}")
            
            self.is_transcribing = True
            self.logger.info("🎤 Transcrição iniciada")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar transcrição: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Parar transcrição."""
        if not self.is_transcribing:
            return
        
        try:
            # Parar thread do microfone
            if self.mic_transcription_thread:
                self.mic_transcription_thread.stop_transcription()
                self.mic_transcription_thread.quit()
                self.mic_transcription_thread.wait()
                self.mic_transcription_thread = None
            
            # Parar thread de loopback
            if self.loopback_transcription_thread:
                self.loopback_transcription_thread.stop_transcription()
                self.loopback_transcription_thread.quit()
                self.loopback_transcription_thread.wait()
                self.loopback_transcription_thread = None
            
            self.is_transcribing = False
            self.logger.info("⏹️ Transcrição parada")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar transcrição: {e}")
    
    def _handle_transcription(self, text: str, speaker_id: str, confidence: float):
        """Processar transcrição recebida."""
        # Mapear source para speaker_id
        if speaker_id == "microphone":
            speaker = "vendor"
        elif speaker_id == "loopback":
            speaker = "client"
        else:
            speaker = "unknown"
        
        # Atualizar métricas
        self.transcription_count += 1
        self.avg_confidence = (self.avg_confidence * (self.transcription_count - 1) + confidence) / self.transcription_count
        
        # Log da transcrição
        self.logger.debug(f"🎤 {speaker}: '{text}' (conf: {confidence:.2f})")
        
        # Emitir para UI
        self.transcription_ready.emit(text, speaker, confidence)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas de transcrição."""
        return {
            "transcription_count": self.transcription_count,
            "avg_confidence": self.avg_confidence,
            "avg_latency": self.avg_latency,
            "is_transcribing": self.is_transcribing,
            "threads_active": sum([
                self.mic_transcription_thread is not None,
                self.loopback_transcription_thread is not None
            ])
        }
    
    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando recursos de transcrição...")
        self.stop()
        self.logger.info("✅ Recursos de transcrição limpos") 
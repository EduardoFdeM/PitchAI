"""
Whisper Transcription - Transcrição em Tempo Real
================================================

Módulo de transcrição usando Whisper otimizado para NPU.
"""

import logging
import numpy as np
import time
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import onnxruntime as ort

try:
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers não disponível. Usando simulação.")

class WhisperTranscriptionThread(QThread):
    """Thread para transcrição contínua."""
    
    transcription_ready = pyqtSignal(str, str, float)  # text, speaker_id, confidence
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config, audio_buffer, source="microphone"):
        super().__init__()
        self.config = config
        self.audio_buffer = audio_buffer
        self.source = source
        self.is_running = False
        
        # Modelo Whisper
        self.processor = None
        self.model = None
        self.session = None
        
        # Configurações
        self.chunk_duration = 3.0  # segundos
        self.chunk_samples = int(self.config.audio.sample_rate * self.chunk_duration)
        self.overlap_samples = int(self.chunk_samples * 0.1)  # 10% overlap
        
        # Buffer interno
        self.audio_chunk = []
        self.last_transcription = ""
    
    def run(self):
        """Loop principal de transcrição."""
        try:
            self._initialize_model()
            self._transcription_loop()
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _initialize_model(self):
        """Inicializar modelo Whisper."""
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers não disponível, usando simulação")
            return
        
        try:
            # Carregar modelo Whisper pequeno
            model_name = "openai/whisper-tiny"
            self.processor = WhisperProcessor.from_pretrained(model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
            
            # Tentar usar NPU se disponível
            providers = ["QNNExecutionProvider", "CPUExecutionProvider"]
            try:
                # Converter modelo para ONNX se necessário
                # TODO: Implementar conversão ONNX
                pass
            except Exception as e:
                logging.warning(f"NPU não disponível para Whisper: {e}")
            
            logging.info(f"✅ Whisper inicializado: {model_name}")
            
        except Exception as e:
            logging.error(f"Erro ao inicializar Whisper: {e}")
            raise
    
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
                    if self.model and self.processor:
                        text, confidence = self._transcribe_chunk(chunk)
                    else:
                        text, confidence = self._simulate_transcription(chunk)
                    
                    # Emitir resultado se houver texto
                    if text and text.strip() and text != self.last_transcription:
                        self.transcription_ready.emit(text, self.source, confidence)
                        self.last_transcription = text
                
                # Aguardar um pouco
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                logging.error(f"Erro no loop de transcrição: {e}")
                break
    
    def _transcribe_chunk(self, audio_chunk: np.ndarray) -> tuple[str, float]:
        """Transcrever um chunk de áudio."""
        try:
            # Preparar áudio para o modelo
            # Whisper espera áudio em 16kHz
            if self.config.audio.sample_rate != 16000:
                # TODO: Implementar resampling
                pass
            
            # Processar com Whisper
            inputs = self.processor(audio_chunk, sampling_rate=16000, return_tensors="pt")
            
            # Gerar tokens
            predicted_ids = self.model.generate(inputs["input_features"])
            
            # Decodificar
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            # Calcular confiança (simplificado)
            confidence = 0.9  # TODO: Implementar cálculo real de confiança
            
            return transcription, confidence
            
        except Exception as e:
            logging.error(f"Erro na transcrição: {e}")
            return "", 0.0
    
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
                "Posso mostrar um exemplo"
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
    
    def __init__(self, config, audio_capture):
        super().__init__()
        self.config = config
        self.audio_capture = audio_capture
        self.logger = logging.getLogger(__name__)
        
        # Threads de transcrição
        self.mic_transcription_thread: Optional[WhisperTranscriptionThread] = None
        self.loopback_transcription_thread: Optional[WhisperTranscriptionThread] = None
        
        self.is_transcribing = False
    
    def initialize(self):
        """Inicializar transcrição."""
        try:
            self.logger.info("🎤 Inicializando transcrição Whisper...")
            
            if not TRANSFORMERS_AVAILABLE:
                self.logger.warning("⚠️ Transformers não disponível, usando simulação")
            
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
                "microphone"
            )
            self.mic_transcription_thread.transcription_ready.connect(self._handle_transcription)
            self.mic_transcription_thread.error_occurred.connect(self.error_occurred)
            self.mic_transcription_thread.start()
            
            # Tentar iniciar transcrição de loopback
            try:
                self.loopback_transcription_thread = WhisperTranscriptionThread(
                    self.config, 
                    self.audio_capture.audio_buffer, 
                    "loopback"
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
        
        # Emitir para UI
        self.transcription_ready.emit(text, speaker, confidence)
    
    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando recursos de transcrição...")
        self.stop()
        self.logger.info("✅ Recursos de transcrição limpos") 
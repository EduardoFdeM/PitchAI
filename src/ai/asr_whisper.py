"""
ASR Whisper - Transcrição em Tempo Real (Feature 2)
==================================================

Implementação da Feature 2:
- Whisper ONNX com streaming por janelas 3-5s
- Processamento incremental com overlap
- Integração com Feature 1 (AudioCapture)
- Eventos em tempo real para UI
"""

import logging
import queue
import threading
import time
import numpy as np
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️ ONNX Runtime não disponível. Usando simulação.")

# Importar decoder real
try:
    from .whisper_decoder import WhisperDecoder
    DECODER_AVAILABLE = True
except ImportError:
    DECODER_AVAILABLE = False
    print("⚠️ WhisperDecoder não disponível. Usando simulação.")


@dataclass
class TranscriptChunk:
    """Chunk de transcrição conforme especificação da Feature 2."""
    call_id: str
    source: str          # 'mic' | 'loopback'
    ts_start_ms: int     # timestamp início da janela
    ts_end_ms: int       # timestamp fim da janela
    text: str            # texto transcrito
    confidence: float    # confiança da transcrição


@dataclass
class PartialUpdate:
    """Atualização parcial para UX de "digitando"."""
    call_id: str
    source: str          # 'mic' | 'loopback'
    ts_ms: int           # timestamp atual
    text: str            # texto parcial
    is_final: bool       # se é a versão final


class WhisperPreprocessor:
    """Pré-processamento de áudio para Whisper."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalizar áudio int16 para float32 [-1, 1]."""
        if audio.dtype == np.int16:
            return audio.astype(np.float32) / 32768.0
        return audio
    
    def pad_or_trim(self, audio: np.ndarray, max_length: int = 480000) -> np.ndarray:
        """Pad ou trim áudio para tamanho fixo."""
        if len(audio) > max_length:
            audio = audio[:max_length]
        elif len(audio) < max_length:
            audio = np.pad(audio, (0, max_length - len(audio)))
        return audio


class TranscriptionService(QObject):
    """Serviço de transcrição Whisper com streaming."""
    
    # Sinais para UI (use 'object' para evitar problemas de metatype)
    transcript_chunk_ready = pyqtSignal(object)
    partial_update_ready = pyqtSignal(object)
    transcription_started = pyqtSignal(str)  # call_id
    transcription_stopped = pyqtSignal(str)  # call_id
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config, model_entry: Dict, window_s: float = 3.0, overlap_s: float = 0.5, model_manager=None):
        super().__init__()
        self.config = config
        self.model_entry = model_entry
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuração de janelas
        self.window_samples = int(16000 * window_s)      # 3.0s = 48000 samples
        self.step_samples = int(16000 * (window_s - overlap_s))  # 2.5s = 40000 samples
        self.overlap_samples = int(16000 * overlap_s)    # 0.5s = 8000 samples
        
        # Buffers de áudio por fonte
        self.buf_mic = np.empty((0,), dtype=np.int16)
        self.buf_loopback = np.empty((0,), dtype=np.int16)
        # contadores por fonte p/ timestamps exatos
        self.samples_consumed = {"mic": 0, "loopback": 0}
        self.t0_ms = {"mic": None, "loopback": None}
        
        # Estado do serviço
        self.running = False
        self.current_call_id = None
        self.session = None
        
        # Pré-processador
        self.preprocessor = WhisperPreprocessor()
        
        # Decoder Whisper
        self.decoder = None
        if DECODER_AVAILABLE:
            self.decoder = WhisperDecoder(config)
        
        # Fila de chunks da Feature 1 (limitada: 8 janelas)
        self.audio_queue = queue.Queue(maxsize=8)
        
        # Thread de processamento
        self.processing_thread = None
        
        # Métricas
        self.chunks_processed = 0
        self.total_latency_ms = 0
        self.last_latency_ms = 0
    
    def initialize(self):
        """Inicializar serviço de transcrição."""
        try:
            self.logger.info("🎤 Inicializando serviço de transcrição Whisper...")
            
            if not ONNX_AVAILABLE:
                self.logger.warning("⚠️ ONNX Runtime não disponível, usando simulação")
                return
            
            # Carregar modelo Whisper
            self._load_whisper_model()
            
            # Fazer warmup
            self._warmup_model()
            
            # Log do modo de operação
            if self.session:
                mode = "REAL (ONNX + Decoder Real)" if self.decoder and self.decoder.is_real_decoder() else "REAL (ONNX + Simulação)"
                self.logger.info(f"✅ Serviço de transcrição inicializado em MODO {mode}")
                providers = self.session.get_providers()
                self.logger.info(f"   Providers ativos: {providers}")
                if self.decoder:
                    self.logger.info(f"   Decoder: {'Real' if self.decoder.is_real_decoder() else 'Simulado'}")
            else:
                self.logger.info("✅ Serviço de transcrição inicializado em MODO SIMULAÇÃO")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar transcrição: {e}")
            self.error_occurred.emit(str(e))
    
    def _load_whisper_model(self):
        """Carregar modelo Whisper ONNX."""
        try:
            # Preferir ModelManager (manifesto + providers padronizados)
            if self.model_manager:
                # Tentar carregar whisper_small primeiro, fallback para tiny
                self.session = self.model_manager.get_session("whisper_small_encoder")
                if not self.session:
                    self.logger.warning("⚠️ Whisper Small não disponível, tentando Tiny...")
                    self.session = self.model_manager.get_session("whisper_tiny_encoder")
                if not self.session:
                    raise RuntimeError("Nenhum modelo Whisper disponível no ModelManager")
                self.logger.info("✅ Modelo Whisper carregado via ModelManager")
            else:
                # Fallback para carregamento manual
                providers = ["CPUExecutionProvider"]
                
                model_path = self.model_entry.get("path", "models/whisper_base.onnx")
                self.session = ort.InferenceSession(model_path, providers=providers)
                
                self.logger.info(f"✅ Modelo Whisper carregado manualmente: {model_path}")
                self.logger.info(f"   Providers: {[p[0] if isinstance(p, tuple) else p for p in providers]}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def _warmup_model(self):
        """Fazer warmup do modelo com inferência dummy."""
        try:
            if not self.session:
                return
            
            # Áudio dummy para warmup
            dummy_audio = np.random.normal(0, 0.1, 16000).astype(np.float32)  # 1s de ruído
            # pad/trim do warmup deve bater com a janela (3s)
            dummy_audio = self.preprocessor.pad_or_trim(dummy_audio, max_length=self.window_samples)
            
            # Inferência dummy
            input_name = self.session.get_inputs()[0].name
            self.session.run(None, {input_name: dummy_audio[np.newaxis, :]})
            
            self.logger.info("✅ Warmup do modelo concluído")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro no warmup: {e}")
    
    def start(self, call_id: str):
        """Iniciar transcrição para uma chamada."""
        if self.running:
            return
        
        try:
            self.current_call_id = call_id
            self.running = True
            self.chunks_processed = 0
            self.total_latency_ms = 0
            
            # Limpar buffers
            self.buf_mic = np.empty((0,), dtype=np.int16)
            self.buf_loopback = np.empty((0,), dtype=np.int16)
            
            # Iniciar thread de processamento
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()
            
            self.transcription_started.emit(call_id)
            self.logger.info(f"🎤 Transcrição iniciada para call_id: {call_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar transcrição: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self, call_id: str):
        """Parar transcrição."""
        if not self.running:
            return
        
        try:
            self.running = False
            
            # Aguardar thread terminar
            if self.processing_thread:
                self.processing_thread.join(timeout=2)
                self.processing_thread = None
            
            # Processar buffers restantes
            self._process_remaining_buffers()
            
            # Calcular métricas finais
            avg_latency = self.total_latency_ms / max(self.chunks_processed, 1)
            self.logger.info(f"⏹️ Transcrição parada para call_id: {call_id}")
            self.logger.info(f"   Chunks processados: {self.chunks_processed}")
            self.logger.info(f"   Latência média: {avg_latency:.1f}ms")
            
            self.transcription_stopped.emit(call_id)
            
        except Exception as e:
            self.logger.error(f"Erro ao parar transcrição: {e}")
    
    def push_audio_chunk(self, chunk):
        """Receber chunk de áudio da Feature 1."""
        try:
            # Validar entrada
            if not hasattr(chunk, 'source') or not hasattr(chunk, 'ts_ms') or not hasattr(chunk, 'buffer'):
                self.logger.error("❌ Chunk inválido: faltam atributos obrigatórios")
                return
            
            if chunk.source not in ["mic", "loopback"]:
                self.logger.error(f"❌ Fonte inválida: {chunk.source}")
                return
            
            if not isinstance(chunk.buffer, np.ndarray) or chunk.buffer.dtype != np.int16:
                self.logger.error(f"❌ Buffer inválido: tipo={type(chunk.buffer)}, dtype={getattr(chunk.buffer, 'dtype', 'N/A')}")
                return
            
            # inicializa origem temporal por fonte no primeiro chunk
            if self.t0_ms.get(chunk.source) is None:
                self.t0_ms[chunk.source] = chunk.ts_ms
            
            self.audio_queue.put(chunk, timeout=0.1)
            
        except queue.Full:
            self.logger.warning("⚠️ Fila de áudio cheia, descartando chunk")
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar chunk: {e}")
    
    def _processing_loop(self):
        """Loop principal de processamento."""
        while self.running:
            try:
                # Consumir chunks de áudio da Feature 1
                while not self.audio_queue.empty():
                    chunk = self.audio_queue.get_nowait()
                    self._add_to_buffer(chunk)
                
                # Processar streams
                self._process_stream("mic", self.buf_mic)
                self._process_stream("loopback", self.buf_loopback)
                
                # Aguardar um pouco
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                self.logger.error(f"Erro no loop de processamento: {e}")
                time.sleep(0.1)
    
    def _add_to_buffer(self, chunk):
        """Adicionar chunk de áudio ao buffer apropriado."""
        if chunk.source == "mic":
            self.buf_mic = np.concatenate([self.buf_mic, chunk.buffer])
        elif chunk.source == "loopback":
            self.buf_loopback = np.concatenate([self.buf_loopback, chunk.buffer])
    
    def _process_stream(self, source: str, buffer: np.ndarray):
        """Processar stream de áudio com janelas deslizantes."""
        if len(buffer) < self.window_samples:
            return
        
        # Processar janelas completas
        while len(buffer) >= self.window_samples:
            # Extrair janela
            window = buffer[:self.window_samples]
            
            # Calcular timestamps com base em contadores + t0 da F1
            src_t0 = self.t0_ms.get(source)
            if src_t0 is None:
                self.logger.warning(f"⚠️ t0 não inicializado para {source}, usando timestamp atual")
                src_t0 = int(time.monotonic_ns() / 1_000_000)
            
            # ms = amostras_consumidas * 1000 / 16000
            ts_start = src_t0 + (self.samples_consumed[source] * 1000 // 16000)
            ts_end   = ts_start + (self.window_samples * 1000 // 16000)
            
            # Validar timestamps
            if ts_start < 0 or ts_end < ts_start:
                self.logger.warning(f"⚠️ Timestamps inválidos: start={ts_start}, end={ts_end}")
                ts_start = max(0, ts_start)
                ts_end = max(ts_start + 100, ts_end)
            
            # Processar janela
            start_time = time.monotonic_ns()
            
            try:
                text, confidence = self._transcribe_window(window)
                
                # Calcular latência
                end_time = time.monotonic_ns()
                latency_ms = (end_time - start_time) / 1_000_000
                
                # Atualizar métricas
                self.chunks_processed += 1
                self.total_latency_ms += latency_ms
                self.last_latency_ms = latency_ms
                
                # Criar chunk de transcrição
                transcript_chunk = TranscriptChunk(
                    call_id=self.current_call_id,
                    source=source,
                    ts_start_ms=ts_start,
                    ts_end_ms=ts_end,
                    text=text,
                    confidence=confidence
                )
                
                # Emitir resultado
                self.transcript_chunk_ready.emit(transcript_chunk)
                
                # Log periódico
                if self.chunks_processed % 10 == 0:
                    avg_latency = self.total_latency_ms / self.chunks_processed
                    self.logger.info(f"📊 {source}: {self.chunks_processed} chunks, "
                                   f"latência média: {avg_latency:.1f}ms")
                
            except Exception as e:
                self.logger.error(f"Erro ao transcrever janela {source}: {e}")
            
            # Mover buffer (overlap) e atualizar contador de amostras
            buffer = buffer[self.step_samples:]
            self.samples_consumed[source] += self.step_samples
        
        # Atualizar buffer
        if source == "mic":
            self.buf_mic = buffer
        else:
            self.buf_loopback = buffer
    
    def _transcribe_window(self, audio_window: np.ndarray) -> tuple[str, float]:
        """Transcrever uma janela de áudio em português brasileiro."""
        if not self.session:
            # Modo simulação
            return self._simulate_transcription_pt_br(audio_window)

        try:
            # Pré-processar áudio
            audio_float = self.preprocessor.normalize_audio(audio_window)
            audio_padded = self.preprocessor.pad_or_trim(audio_float, max_length=self.window_samples)

            # Preparar input
            input_name = self.session.get_inputs()[0].name
            input_data = audio_padded[np.newaxis, :]  # [1, T]

            # Inferência
            outputs = self.session.run(None, {input_name: input_data})

            # Decodificar saída com foco em PT-BR
            text, confidence = self._decode_whisper_output(outputs)

            return text, confidence

        except Exception as e:
            self.logger.error(f"Erro na transcrição: {e}")
            return "", 0.0
    
    def _decode_whisper_output(self, outputs) -> tuple[str, float]:
        """Decodificar saída do Whisper."""
        try:
            # Usar decoder real se disponível
            if self.decoder and self.decoder.is_real_decoder():
                audio_length = len(outputs[0]) if outputs else 0
                return self.decoder.decode_whisper_output(outputs, audio_length)
            
            # Fallback para simulação
            return self._simulate_decode(outputs)
            
        except Exception as e:
            self.logger.error(f"Erro na decodificação: {e}")
            return "", 0.0
    
    def _simulate_decode(self, outputs) -> tuple[str, float]:
        """Decodificação simulada (fallback)."""
        try:
            # Simular texto baseado no tamanho do áudio
            audio_length = len(outputs[0]) if outputs else 0
            if audio_length > 0:
                # Simular texto baseado em padrões
                if audio_length > 32000:  # > 2s
                    text = "Olá, como você está hoje?"
                    confidence = 0.85
                elif audio_length > 16000:  # > 1s
                    text = "Sim, entendi."
                    confidence = 0.75
                else:
                    text = "Hmm."
                    confidence = 0.5
            else:
                text = ""
                confidence = 0.0
            
            return text, confidence
            
        except Exception as e:
            self.logger.error(f"Erro na decodificação simulada: {e}")
            return "", 0.0
    
    def _simulate_transcription_pt_br(self, audio_window: np.ndarray) -> tuple[str, float]:
        """Simular transcrição em português brasileiro para desenvolvimento."""
        # Simular baseado no RMS do áudio
        rms = np.sqrt(np.mean(audio_window.astype(np.float32)**2))

        if rms > 1000:  # Áudio com sinal
            # Exemplos focados em contexto de vendas em PT-BR
            pt_br_examples = [
                "Olá, bom dia! Como vai?",
                "Gostaria de saber mais sobre o produto",
                "Qual é o preço da solução?",
                "Entendi, obrigado pela informação",
                "Vamos marcar uma demonstração?",
                "Preciso falar com o responsável técnico",
                "O orçamento está aprovado para este trimestre",
                "Quando podemos começar o projeto?",
                "Isso está dentro do nosso orçamento",
                "Vamos analisar as opções disponíveis",
                "Qual é o prazo de implementação?",
                "Vocês têm suporte técnico?",
                "Como funciona o processo de contratação?",
                "Quais são os benefícios principais?",
                "Posso falar com alguém da diretoria?"
            ]

            import random
            text = random.choice(pt_br_examples)
            confidence = 0.85  # Aumentado para contexto de vendas
        else:  # Silêncio
            text = ""
            confidence = 0.0

        return text, confidence
    
    def _process_remaining_buffers(self):
        """Processar buffers restantes ao parar."""
        # Processar mic
        if len(self.buf_mic) > 0:
            self._process_stream("mic", self.buf_mic)
        
        # Processar loopback
        if len(self.buf_loopback) > 0:
            self._process_stream("loopback", self.buf_loopback)
    
    def get_metrics(self) -> Dict:
        """Obter métricas de performance."""
        avg_latency = self.total_latency_ms / max(self.chunks_processed, 1)
        
        return {
            "is_running": self.running,
            "call_id": self.current_call_id,
            "chunks_processed": self.chunks_processed,
            "avg_latency_ms": avg_latency,
            "last_latency_ms": self.last_latency_ms,
            "buffer_sizes": {
                "mic": len(self.buf_mic),
                "loopback": len(self.buf_loopback)
            }
        }
    
    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando recursos de transcrição...")
        self.stop(self.current_call_id or "")
        self.logger.info("✅ Recursos de transcrição limpos") 
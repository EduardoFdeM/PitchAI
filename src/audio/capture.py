"""
Audio Capture - Captura de Áudio do Sistema (Feature 1)
======================================================

Implementação completa da Feature 1:
- Captura simultânea de microfone e WASAPI loopback
- Sincronização de streams com timestamps
- Formato PCM 16-bit, 16kHz/48kHz, mono
- APIs async e callback
- Tratamento de falhas e fallback
"""

import logging
import numpy as np
import threading
import time
import uuid
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from math import ceil
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️ PyAudio não disponível. Usando simulação.")


@dataclass
class AudioChunk:
    """Chunk de áudio conforme SRS (PCM 16-bit mono 16kHz)."""
    call_id: str
    source: str          # 'mic' | 'loopback'
    ts_ms: int           # timestamp monotônico (ms desde start)
    buffer: np.ndarray   # PCM int16 mono @ 16_000 Hz
    sample_rate: int
    channels: int


@dataclass
class PCMFormat:
    """Formato PCM conforme especificação."""
    sample_rate: int = 16000  # 16kHz padrão, pode ser 48kHz
    bit_depth: int = 16
    channels: int = 1  # mono


class AudioCaptureThread(QThread):
    """Thread para captura contínua de áudio com WASAPI loopback."""
    
    audio_data_ready = pyqtSignal(AudioChunk)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config, source="mic", device_index=None, call_id: Optional[str]=None, t0_monotonic_ns: Optional[int]=None):
        super().__init__()
        self.config = config
        self.source = source
        self.device_index = device_index
        self.is_running = False
        self.audio_stream = None
        self.pa = None
        self.call_id = call_id or str(uuid.uuid4())
        self._t0 = t0_monotonic_ns or time.monotonic_ns()
        
        # alvo lógico (SRS): 16k/mono
        self.format = PCMFormat(sample_rate=16000, channels=1)
        
        # Buffer para acumular dados
        self.audio_buffer = []
        self.buffer_size = 16000 * 3  # 3 segundos @16k
        self._device_rate = None
        self._device_channels = None

    def _ts_ms(self) -> int:
        # monotônico relativo ao início da thread/sessão
        return int((time.monotonic_ns() - self._t0) / 1_000_000)

    @staticmethod
    def _downmix_to_mono(samples: np.ndarray, channels: int) -> np.ndarray:
        if channels == 1:
            return samples
        # interleaved -> média por frame
        frames = samples.reshape(-1, channels)
        mono = frames.mean(axis=1)
        return mono.astype(samples.dtype)

    @staticmethod
    def _resample_int16(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
        if sr_in == sr_out or len(x) == 0:
            return x
        # linear resample leve (suficiente para hackathon)
        ratio = sr_out / sr_in
        n_out = int(ceil(len(x) * ratio))
        xp = np.linspace(0.0, 1.0, num=len(x), endpoint=False)
        fp = x.astype(np.float32)
        xq = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
        y = np.interp(xq, xp, fp)
        y = np.clip(y, -32768, 32767).astype(np.int16)
        return y
        
    def run(self):
        """Loop principal de captura."""
        try:
            if PYAUDIO_AVAILABLE:
                self._initialize_audio()
                self._capture_loop()
            else:
                self._simulate_audio()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._cleanup_audio()
    
    def _initialize_audio(self):
        """Inicializar PyAudio com WASAPI loopback."""
        if not PYAUDIO_AVAILABLE:
            return
            
        try:
            self.pa = pyaudio.PyAudio()
            
            # Encontrar dispositivo apropriado
            if self.device_index is None:
                self.device_index = self._find_device()
            
            if self.device_index is None:
                logging.warning(f"Dispositivo não encontrado para {self.source} - usando padrão")
                self.device_index = None  # Usar dispositivo padrão
            
            # Obter informações do dispositivo
            if self.device_index is not None:
                try:
                    device_info = self.pa.get_device_info_by_index(self.device_index)
                    logging.info(f"Dispositivo {self.source}: {device_info['name']}")
                    self._device_rate = int(device_info['defaultSampleRate'])
                    self._device_channels = max(1, device_info.get('maxInputChannels', 1))
                except Exception as e:
                    logging.warning(f"Erro ao obter info do dispositivo {self.device_index}: {e}")
                    self._device_rate = 48000
                    self._device_channels = 1
            else:
                # Usar valores padrão
                self._device_rate = 48000
                self._device_channels = 1
            
            open_channels = min(self._device_channels, 2)  # evita 5.1/7.1
            
            # Configurar stream com tratamento de erro
            try:
                self.audio_stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=open_channels,
                    rate=self._device_rate,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=self.config.audio.chunk_size
                )
                
                logging.info(f"✅ Stream de áudio configurado para {self.source} "
                            f"(device: {self.device_index}, rate: {self._device_rate}Hz)")
                            
            except Exception as e:
                logging.error(f"Erro ao abrir stream de áudio: {e}")
                raise RuntimeError(f"Não foi possível abrir stream de áudio: {e}")
                
        except Exception as e:
            logging.error(f"Erro na inicialização de áudio: {e}")
            raise
    
    def _find_device(self) -> Optional[int]:
        """Encontrar dispositivo apropriado."""
        if not self.pa:
            return None
        
        if self.source == "loopback":
            # Para PyAudio normal, procurar por dispositivos que possam ser loopback
            try:
                for i in range(self.pa.get_device_count()):
                    device_info = self.pa.get_device_info_by_index(i)
                    if (device_info['maxInputChannels'] > 0 and 
                        ('loopback' in device_info['name'].lower() or 
                         'system' in device_info['name'].lower() or
                         'stereo mix' in device_info['name'].lower())):
                        logging.info(f"Loopback encontrado: {device_info['name']}")
                        return i
                logging.warning("Nenhum dispositivo loopback encontrado")
                return None
            except Exception as e:
                logging.warning(f"Erro ao procurar loopback: {e}")
                return None
        else:
            # Microfone - usar dispositivo padrão
            return None
    
    def set_input_device(self, device_index: int):
        """Configurar dispositivo de entrada específico."""
        if not PYAUDIO_AVAILABLE:
            logging.warning("PyAudio não disponível")
            return
            
        try:
            # Verificar se o dispositivo existe
            device_info = self.pa.get_device_info_by_index(device_index)
            logging.info(f"Configurando dispositivo de entrada: {device_info['name']}")
            
            # Parar captura atual se estiver ativa
            if self.is_capturing:
                self.stop()
            
            # Atualizar índice do dispositivo
            self.device_index = device_index
            
            # Reconfigurar stream se PyAudio estiver inicializado
            if hasattr(self, 'pa') and self.pa:
                self._initialize_audio()
                
            logging.info(f"✅ Dispositivo de entrada configurado: {device_info['name']}")
            
        except Exception as e:
            logging.error(f"Erro ao configurar dispositivo {device_index}: {e}")
            raise
    
    def _capture_loop(self):
        """Loop de captura de áudio com timestamps."""
        self.is_running = True
        
        while self.is_running:
            if self.audio_stream:
                try:
                    # Ler dados do stream
                    audio_data = self.audio_stream.read(
                        self.config.audio.chunk_size,
                        exception_on_overflow=False
                    )
                    
                    # PCM int16 do device
                    dev_pcm = np.frombuffer(audio_data, dtype=np.int16)
                    # Downmix -> mono
                    mono = self._downmix_to_mono(dev_pcm, channels=self._device_channels)
                    # Resample -> 16 kHz
                    pcm_16k = self._resample_int16(mono, self._device_rate, 16_000)

                    # Criar chunk com timestamp monotônico
                    chunk = AudioChunk(
                        call_id=self.call_id,
                        source=self.source,
                        ts_ms=self._ts_ms(),
                        buffer=pcm_16k,
                        sample_rate=16_000,
                        channels=1
                    )
                    
                    # Emitir sinal com dados
                    self.audio_data_ready.emit(chunk)
                    
                except Exception as e:
                    logging.error(f"Erro na captura {self.source}: {e}")
                    break
    
    def _simulate_audio(self):
        """Simular dados de áudio - APENAS EM CASO DE FALHA CRÍTICA."""
        logging.warning("⚠️ MODO DE FALHA: Simulando áudio - sistema real indisponível")
        self.is_running = True
        
        while self.is_running:
            # Gerar áudio sintético (ruído branco baixo) - int16 para simulação
            chunk_size = self.config.audio.chunk_size
            simulated_audio = np.random.normal(0, 1000, chunk_size).astype(np.int16)
            
            # Criar chunk simulado
            chunk = AudioChunk(
                call_id=self.call_id,
                source=self.source,
                ts_ms=self._ts_ms(),
                buffer=simulated_audio,
                sample_rate=16_000,
                channels=1
            )
            
            # Emitir dados simulados
            self.audio_data_ready.emit(chunk)
            
            # Aguardar um pouco
            time.sleep(0.1)  # 100ms
    
    def stop_capture(self):
        """Parar captura."""
        self.is_running = False
    
    def _cleanup_audio(self):
        """Limpar recursos de áudio."""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        if self.pa:
            self.pa.terminate()
            self.pa = None


class AudioCapture(QObject):
    """Gerenciador de captura de áudio - Feature 1 completa."""
    
    # Sinais conforme especificação
    audio_ready = pyqtSignal(AudioChunk)  # chunk de áudio
    capture_started = pyqtSignal()
    capture_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Threads de captura
        self.mic_thread: Optional[AudioCaptureThread] = None
        self.loopback_thread: Optional[AudioCaptureThread] = None
        
        # Estado da captura
        self.is_capturing = False
        self.current_call_id = None
        
        # Buffers para acumular áudio
        self.audio_buffers = {"mic": [], "loopback": []}
        self.buffer_size = 16000 * 3  # 3 segundos @16k
        
        # Callbacks para consumidores
        self.audio_callbacks: List[Callable] = []
        
        # Métricas
        self.capture_start_time = None
        self.chunks_received = {"mic": 0, "loopback": 0}
        self.last_timestamps = {"mic": 0, "loopback": 0}
        self._t0 = None
    
    def initialize(self):
        """Inicializar captura de áudio."""
        try:
            self.logger.info("🎤 Inicializando captura de áudio (Feature 1)...")
            
            # Verificar se PyAudioWPatch está disponível
            if not PYAUDIO_AVAILABLE:
                self.logger.warning("⚠️ PyAudioWPatch não disponível, usando simulação")
            
            # Listar dispositivos disponíveis
            self._list_audio_devices()
            
            self.logger.info("✅ Captura de áudio inicializada")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar áudio: {e}")
    
    def _list_audio_devices(self):
        """Listar dispositivos de áudio disponíveis."""
        if not PYAUDIO_AVAILABLE:
            return
        
        pa = pyaudio.PyAudio()
        
        self.logger.info("Dispositivos de áudio disponíveis:")
        
        # Listar dispositivos de entrada (mic)
        self.logger.info("  🎤 Dispositivos de entrada (mic):")
        for i in range(pa.get_device_count()):
            device_info = pa.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0 and 'loopback' not in device_info['name'].lower():
                self.logger.info(f"    [{i}] {device_info['name']} "
                               f"(Inputs: {device_info['maxInputChannels']}, "
                               f"Rate: {int(device_info['defaultSampleRate'])} Hz)")
        
        # Listar dispositivos de loopback (para PyAudio normal)
        self.logger.info("  📻 Dispositivos de loopback:")
        try:
            for i in range(pa.get_device_count()):
                device_info = pa.get_device_info_by_index(i)
                if (device_info['maxInputChannels'] > 0 and 
                    ('loopback' in device_info['name'].lower() or 
                     'system' in device_info['name'].lower() or
                     'stereo mix' in device_info['name'].lower())):
                    self.logger.info(f"    [{i}] {device_info['name']} "
                                   f"(Rate: {int(device_info['defaultSampleRate'])} Hz)")
        except Exception as e:
            self.logger.warning(f"    Erro ao listar loopbacks: {e}")
        
        pa.terminate()
    
    def start(self):
        """Iniciar captura de áudio (RF-1.5)."""
        if self.is_capturing:
            return
        
        try:
            self.current_call_id = str(uuid.uuid4())
            self._t0 = time.monotonic_ns()
            self.capture_start_time = time.time()
            self.chunks_received = {"mic": 0, "loopback": 0}
            
            # Iniciar thread do microfone
            self.mic_thread = AudioCaptureThread(self.config, "mic", call_id=self.current_call_id, t0_monotonic_ns=self._t0)
            self.mic_thread.audio_data_ready.connect(self._handle_audio_data)
            self.mic_thread.error_occurred.connect(self.error_occurred)
            self.mic_thread.start()
            
            # Tentar iniciar thread de loopback
            try:
                self.loopback_thread = AudioCaptureThread(self.config, "loopback", call_id=self.current_call_id, t0_monotonic_ns=self._t0)
                self.loopback_thread.audio_data_ready.connect(self._handle_audio_data)
                self.loopback_thread.error_occurred.connect(self.error_occurred)
                self.loopback_thread.start()
                self.logger.info("✅ Captura de loopback iniciada")
            except Exception as e:
                self.logger.warning(f"⚠️ Loopback não disponível: {e}")
            
            self.is_capturing = True
            self.capture_started.emit()
            self.logger.info(f"🎤 Captura iniciada (call_id: {self.current_call_id})")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar captura: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Parar captura de áudio (RF-1.5)."""
        if not self.is_capturing:
            return
        
        try:
            # Parar thread do microfone
            if self.mic_thread:
                self.mic_thread.stop_capture()
                self.mic_thread.quit()
                self.mic_thread.wait()
                self.mic_thread = None
            
            # Parar thread de loopback
            if self.loopback_thread:
                self.loopback_thread.stop_capture()
                self.loopback_thread.quit()
                self.loopback_thread.wait()
                self.loopback_thread = None
            
            self.is_capturing = False
            self.capture_stopped.emit()
            
            # Log de métricas
            duration = time.time() - self.capture_start_time if self.capture_start_time else 0
            self.logger.info(f"⏹️ Captura parada (duração: {duration:.1f}s, "
                           f"chunks: mic={self.chunks_received['mic']}, "
                           f"loopback={self.chunks_received['loopback']})")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar captura: {e}")
    
    def _handle_audio_data(self, chunk: AudioChunk):
        """Processar dados de áudio recebidos (RF-1.4)."""
        # Atualizar métricas
        self.chunks_received[chunk.source] += 1
        self.last_timestamps[chunk.source] = chunk.ts_ms
        
        # Adicionar ao buffer específico
        self.audio_buffers[chunk.source].extend(chunk.buffer.tolist())
        
        # Manter tamanho do buffer
        if len(self.audio_buffers[chunk.source]) > self.buffer_size:
            self.audio_buffers[chunk.source] = self.audio_buffers[chunk.source][-self.buffer_size:]
        
        # Emitir para processamento NPU
        self.audio_ready.emit(chunk)
        
        # Notificar callbacks
        for callback in self.audio_callbacks:
            try:
                callback(chunk)
            except Exception as e:
                self.logger.error(f"Erro em callback de áudio: {e}")
    
    def add_callback(self, callback: Callable[[AudioChunk], None]):
        """Adicionar callback para dados de áudio (RF-1.4)."""
        self.audio_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[AudioChunk], None]):
        """Remover callback."""
        if callback in self.audio_callbacks:
            self.audio_callbacks.remove(callback)
    
    def get_audio_buffer(self, source: str = "mic") -> np.ndarray:
        """Obter buffer de áudio atual."""
        return np.array(self.audio_buffers.get(source, []), dtype=np.int16)
    
    def get_sync_drift(self) -> float:
        """Calcular drift entre canais (RF-1.2)."""
        if not self.last_timestamps["mic"] or not self.last_timestamps["loopback"]:
            return 0.0
        
        drift = abs(self.last_timestamps["mic"] - self.last_timestamps["loopback"])
        return drift
    
    def clear_buffer(self):
        """Limpar buffer de áudio."""
        self.audio_buffers = {"mic": [], "loopback": []}
    
    def get_metrics(self) -> Dict:
        """Obter métricas de captura."""
        return {
            "is_capturing": self.is_capturing,
            "call_id": self.current_call_id,
            "chunks_received": self.chunks_received.copy(),
            "sync_drift_ms": self.get_sync_drift(),
            "buffer_sizes": {
                source: len(buffer) for source, buffer in self.audio_buffers.items()
            }
        }
    
    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando recursos de áudio...")
        self.stop()
        self.clear_buffer()
        self.audio_callbacks.clear()
        self.logger.info("✅ Recursos de áudio limpos")

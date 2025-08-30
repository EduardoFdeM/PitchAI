"""
Audio Capture - Captura de Áudio do Sistema
===========================================

Captura o mix de áudio do Windows via WASAPI loopback
para análise em tempo real.
"""

import logging
import numpy as np
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

try:
    import pyaudio
except ImportError:
    pyaudio = None


class AudioCaptureThread(QThread):
    """Thread para captura contínua de áudio."""
    
    audio_data_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        self.audio_stream = None
        self.pa = None
        
    def run(self):
        """Loop principal de captura."""
        try:
            self._initialize_audio()
            self._capture_loop()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._cleanup_audio()
    
    def _initialize_audio(self):
        """Inicializar PyAudio."""
        if not pyaudio:
            raise ImportError("PyAudio não disponível")
        
        self.pa = pyaudio.PyAudio()
        
        # Encontrar dispositivo de loopback (WASAPI)
        device_index = self._find_loopback_device()
        
        # Configurar stream
        self.audio_stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=self.config.audio.channels,
            rate=self.config.audio.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.config.audio.chunk_size
        )
        
        logging.info(f"✅ Stream de áudio configurado (device: {device_index})")
    
    def _find_loopback_device(self) -> Optional[int]:
        """Encontrar dispositivo de loopback do Windows."""
        if not self.pa:
            return None
        
        # Procurar por dispositivo WASAPI loopback
        for i in range(self.pa.get_device_count()):
            device_info = self.pa.get_device_info_by_index(i)
            device_name = device_info.get('name', '').lower()
            
            # Procurar indicadores de loopback
            if any(indicator in device_name for indicator in 
                  ['stereo mix', 'loopback', 'what u hear', 'mix']):
                logging.info(f"Dispositivo loopback encontrado: {device_info['name']}")
                return i
        
        # Fallback para dispositivo padrão
        logging.warning("Dispositivo loopback não encontrado, usando padrão")
        return None
    
    def _capture_loop(self):
        """Loop de captura de áudio."""
        self.is_running = True
        
        while self.is_running:
            if self.audio_stream:
                try:
                    # Ler dados do stream
                    audio_data = self.audio_stream.read(
                        self.config.audio.chunk_size,
                        exception_on_overflow=False
                    )
                    
                    # Converter para numpy array
                    np_data = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Normalizar para float32
                    normalized_data = np_data.astype(np.float32) / 32768.0
                    
                    # Emitir sinal com dados
                    self.audio_data_ready.emit(normalized_data)
                    
                except Exception as e:
                    logging.error(f"Erro na captura: {e}")
                    break
    
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
    """Gerenciador de captura de áudio."""
    
    audio_ready = pyqtSignal(np.ndarray)
    capture_started = pyqtSignal()
    capture_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.capture_thread: Optional[AudioCaptureThread] = None
        self.is_capturing = False
        
        # Buffer para acumular áudio
        self.audio_buffer = []
        self.buffer_size = config.audio.sample_rate * 3  # 3 segundos
        
        # Timer para simulação (quando PyAudio não disponível)
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._simulate_audio)
    
    def initialize(self):
        """Inicializar captura de áudio."""
        try:
            self.logger.info("🎤 Inicializando captura de áudio...")
            
            # Verificar se PyAudio está disponível
            if not pyaudio:
                self.logger.warning("⚠️ PyAudio não disponível, usando simulação")
                self._enable_simulation()
                return
            
            # Testar dispositivos disponíveis
            self._list_audio_devices()
            
            self.logger.info("✅ Captura de áudio inicializada")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar áudio: {e}")
            self._enable_simulation()
    
    def _list_audio_devices(self):
        """Listar dispositivos de áudio disponíveis."""
        if not pyaudio:
            return
        
        pa = pyaudio.PyAudio()
        
        self.logger.info("Dispositivos de áudio disponíveis:")
        for i in range(pa.get_device_count()):
            device_info = pa.get_device_info_by_index(i)
            self.logger.info(f"  [{i}] {device_info['name']} "
                           f"(Inputs: {device_info['maxInputChannels']})")
        
        pa.terminate()
    
    def _enable_simulation(self):
        """Habilitar modo de simulação."""
        self.logger.info("🎭 Habilitando simulação de áudio")
        # Configuração já permite simulação
    
    def start(self):
        """Iniciar captura de áudio."""
        if self.is_capturing:
            return
        
        try:
            if pyaudio:
                self._start_real_capture()
            else:
                self._start_simulation()
            
            self.is_capturing = True
            self.capture_started.emit()
            self.logger.info("🎤 Captura iniciada")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar captura: {e}")
            self.error_occurred.emit(str(e))
    
    def _start_real_capture(self):
        """Iniciar captura real de áudio."""
        self.capture_thread = AudioCaptureThread(self.config)
        self.capture_thread.audio_data_ready.connect(self._handle_audio_data)
        self.capture_thread.error_occurred.connect(self.error_occurred)
        self.capture_thread.start()
    
    def _start_simulation(self):
        """Iniciar simulação de áudio."""
        self.simulation_timer.start(100)  # A cada 100ms
    
    def stop(self):
        """Parar captura de áudio."""
        if not self.is_capturing:
            return
        
        try:
            if self.capture_thread:
                self.capture_thread.stop_capture()
                self.capture_thread.quit()
                self.capture_thread.wait()
                self.capture_thread = None
            
            if self.simulation_timer.isActive():
                self.simulation_timer.stop()
            
            self.is_capturing = False
            self.capture_stopped.emit()
            self.logger.info("⏹️ Captura parada")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar captura: {e}")
    
    def _handle_audio_data(self, audio_data: np.ndarray):
        """Processar dados de áudio recebidos."""
        # Adicionar ao buffer
        self.audio_buffer.extend(audio_data)
        
        # Manter tamanho do buffer
        if len(self.audio_buffer) > self.buffer_size:
            self.audio_buffer = self.audio_buffer[-self.buffer_size:]
        
        # Emitir para processamento NPU
        self.audio_ready.emit(audio_data)
    
    def _simulate_audio(self):
        """Simular dados de áudio para desenvolvimento."""
        # Gerar áudio sintético (ruído branco baixo)
        chunk_size = self.config.audio.chunk_size
        simulated_audio = np.random.normal(0, 0.01, chunk_size).astype(np.float32)
        
        # Emitir dados simulados
        self.audio_ready.emit(simulated_audio)
    
    def get_audio_buffer(self) -> np.ndarray:
        """Obter buffer de áudio atual."""
        return np.array(self.audio_buffer, dtype=np.float32)
    
    def clear_buffer(self):
        """Limpar buffer de áudio."""
        self.audio_buffer.clear()
    
    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando recursos de áudio...")
        self.stop()
        self.clear_buffer()
        self.logger.info("✅ Recursos de áudio limpos")

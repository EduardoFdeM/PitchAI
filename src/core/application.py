"""
PitchAI - Classe Principal da Aplicação
=====================================

Coordena todos os módulos da aplicação:
- Interface PyQt6  
- Pipeline de IA na NPU
- Captura de áudio
- Gerenciamento de dados
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .config import Config
from ui.main_window import MainWindow
from ai.npu_manager import NPUManager
from audio.capture import AudioCapture
from data.database import DatabaseManager


class PitchAIApp(QObject):
    """Classe principal da aplicação PitchAI."""
    
    # Sinais para comunicação entre threads
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas de sentimento
    objection_detected = pyqtSignal(str, list) # objeção, sugestões
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.main_window: Optional[MainWindow] = None
        
        # Componentes principais
        self.npu_manager: Optional[NPUManager] = None
        self.audio_capture: Optional[AudioCapture] = None
        self.database: Optional[DatabaseManager] = None
        
        # Estado da aplicação
        self.is_recording = False
        self.current_session_id = None
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurar sistema de logging."""
        log_file = self.config.app_dir / "logs" / "pitchai.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Inicializar todos os componentes da aplicação."""
        try:
            self.logger.info("🚀 Inicializando PitchAI...")
            
            # 1. Inicializar banco de dados
            self._initialize_database()
            
            # 2. Inicializar gerenciador NPU
            self._initialize_npu()
            
            # 3. Inicializar captura de áudio
            self._initialize_audio()
            
            # 4. Inicializar interface
            self._initialize_ui()
            
            # 5. Conectar sinais
            self._connect_signals()
            
            self.logger.info("✅ PitchAI inicializado com sucesso!")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {e}")
            raise
    
    def _initialize_database(self):
        """Inicializar gerenciador de banco de dados."""
        self.database = DatabaseManager(self.config)
        self.database.initialize()
        self.logger.info("✅ Banco de dados inicializado")
    
    def _initialize_npu(self):
        """Inicializar gerenciador NPU."""
        self.npu_manager = NPUManager(self.config)
        self.npu_manager.initialize()
        self.logger.info("✅ NPU inicializada")
    
    def _initialize_audio(self):
        """Inicializar captura de áudio."""
        self.audio_capture = AudioCapture(self.config)
        self.audio_capture.initialize()
        self.logger.info("✅ Captura de áudio inicializada")
    
    def _initialize_ui(self):
        """Inicializar interface PyQt6."""
        self.main_window = MainWindow(self.config, self)
        self.logger.info("✅ Interface inicializada")
    
    def _connect_signals(self):
        """Conectar sinais entre componentes."""
        if self.audio_capture and self.npu_manager:
            # Áudio → NPU
            self.audio_capture.audio_ready.connect(
                self.npu_manager.process_audio
            )
            
            # NPU → UI
            self.npu_manager.transcription_ready.connect(
                self.transcription_ready
            )
            self.npu_manager.sentiment_updated.connect(
                self.sentiment_updated
            )
            self.npu_manager.objection_detected.connect(
                self.objection_detected
            )
        
        self.logger.info("✅ Sinais conectados")
    
    def show(self):
        """Exibir a janela principal."""
        if self.main_window:
            self.main_window.show()
    
    def start_recording(self):
        """Iniciar gravação e análise."""
        if not self.is_recording:
            self.logger.info("🎤 Iniciando gravação...")
            self.current_session_id = self.database.create_session()
            self.audio_capture.start()
            self.is_recording = True
    
    def stop_recording(self):
        """Parar gravação e gerar resumo."""
        if self.is_recording:
            self.logger.info("⏹️ Parando gravação...")
            self.audio_capture.stop()
            self.is_recording = False
            
            # Gerar resumo da sessão
            if self.current_session_id:
                self._generate_session_summary()
    
    def _generate_session_summary(self):
        """Gerar resumo da sessão atual."""
        # TODO: Implementar geração de resumo
        self.logger.info(f"📋 Gerando resumo da sessão {self.current_session_id}")
    
    def shutdown(self):
        """Encerrar aplicação graciosamente."""
        self.logger.info("🔄 Encerrando PitchAI...")
        
        if self.is_recording:
            self.stop_recording()
        
        if self.audio_capture:
            self.audio_capture.cleanup()
        
        if self.npu_manager:
            self.npu_manager.cleanup()
        
        if self.database:
            self.database.close()
        
        self.logger.info("✅ PitchAI encerrado")

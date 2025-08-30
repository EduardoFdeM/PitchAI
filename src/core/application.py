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
import time
from typing import Optional
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .config import Config
from ui.main_window import MainWindow
from ai.npu_manager import NPUManager
from ai.sentiment import SentimentService, SentimentConfig
from ai.rag_service import RAGService
from audio.capture import AudioCapture
from data.database import DatabaseManager


class PitchAIApp(QObject):
    """Classe principal da aplicação PitchAI."""
    
    # Sinais para comunicação entre threads
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas de sentimento
    objection_detected = pyqtSignal(str, list) # objeção, sugestões
    rag_suggestions_ready = pyqtSignal(object)  # RAGResult
    rag_error = pyqtSignal(str)                 # erro do RAG
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.main_window: Optional[MainWindow] = None
        
        # Componentes principais
        self.npu_manager: Optional[NPUManager] = None
        self.sentiment_service: Optional[SentimentService] = None
        self.rag_service: Optional[RAGService] = None
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
            
            # 3. Inicializar serviço de sentimento
            self._initialize_sentiment()
            
            # 4. Inicializar serviço RAG
            self._initialize_rag()
            
            # 5. Inicializar captura de áudio
            self._initialize_audio()
            
            # 6. Inicializar interface
            self._initialize_ui()
            
            # 7. Conectar sinais
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
    
    def _initialize_sentiment(self):
        """Inicializar serviço de sentimento."""
        sentiment_config = SentimentConfig()
        self.sentiment_service = SentimentService(sentiment_config, self.npu_manager)
        self.sentiment_service.initialize()
        self.logger.info("✅ Serviço de sentimento inicializado")
    
    def _initialize_rag(self):
        """Inicializar serviço RAG."""
        self.rag_service = RAGService(self.config)
        self.logger.info("✅ Serviço RAG inicializado")
    
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
        if self.audio_capture and self.npu_manager and self.sentiment_service and self.rag_service:
            # Áudio → NPU
            self.audio_capture.audio_ready.connect(
                self.npu_manager.process_audio
            )
            
            # Áudio → Sentiment Service (para análise de prosódia)
            self.audio_capture.audio_ready.connect(
                self._process_audio_for_sentiment
            )
            
            # NPU → Sentiment Service (para análise de texto)
            self.npu_manager.transcription_ready.connect(
                self._process_transcription_for_sentiment
            )
            
            # Sentiment Service → UI
            self.sentiment_service.sentiment_updated.connect(
                self.sentiment_updated
            )
            self.sentiment_service.alert_triggered.connect(
                self._handle_sentiment_alert
            )
            self.sentiment_service.dashboard_updated.connect(
                self._update_sentiment_dashboard
            )
            
            # NPU → UI (mantendo compatibilidade)
            self.npu_manager.transcription_ready.connect(
                self.transcription_ready
            )
            self.npu_manager.objection_detected.connect(
                self._handle_objection_detected
            )
            
            # RAG Service → UI
            self.rag_service.suggestions_ready.connect(
                self.rag_suggestions_ready
            )
            self.rag_service.rag_error.connect(
                self.rag_error
            )
        
        self.logger.info("✅ Sinais conectados")
    
    def _handle_objection_detected(self, objection_text: str, suggestions: list):
        """Manusear objeção detectada e processar com RAG."""
        self.logger.info(f"🚨 Objeção detectada: {objection_text}")
        
        # Emitir sinal original para compatibilidade
        self.objection_detected.emit(objection_text, suggestions)
        
        # Processar com RAG se disponível
        if self.rag_service and self.current_session_id:
            from ai.rag_service import ObjectionEvent
            
            # Criar evento de objeção
            objection_event = ObjectionEvent(
                call_id=self.current_session_id,
                category=self._classify_objection(objection_text),
                text=objection_text,
                context_snippet=objection_text,
                timestamp_ms=int(time.time() * 1000)
            )
            
            # Processar com RAG
            self.rag_service.process_objection(objection_event)
    
    def _classify_objection(self, objection_text: str) -> str:
        """Classificar objeção em categoria."""
        text_lower = objection_text.lower()
        
        if any(word in text_lower for word in ['preço', 'custo', 'caro', 'valor', 'dinheiro']):
            return 'preco'
        elif any(word in text_lower for word in ['tempo', 'depois', 'agora', 'urgente', 'pressa']):
            return 'timing'
        elif any(word in text_lower for word in ['chefe', 'superior', 'decisão', 'autoridade']):
            return 'autoridade'
        elif any(word in text_lower for word in ['preciso', 'necessidade', 'problema', 'solução']):
            return 'necessidade'
        else:
            return 'geral'
    
    def _process_audio_for_sentiment(self, audio_data, ts_start_ms, ts_end_ms):
        """Processar áudio para análise de sentimento."""
        if self.sentiment_service and self.is_recording:
            self.sentiment_service.process_audio_chunk(audio_data, ts_start_ms, ts_end_ms)
    
    def _process_transcription_for_sentiment(self, text, speaker_id, ts_start_ms, ts_end_ms):
        """Processar transcrição para análise de sentimento."""
        if self.sentiment_service and self.is_recording:
            # Só processar transcrição do cliente (speaker_id == 'loopback')
            if speaker_id == 'loopback':
                self.sentiment_service.process_text_chunk(text, ts_start_ms, ts_end_ms)
    
    def _handle_sentiment_alert(self, event):
        """Manusear alertas de sentimento."""
        self.logger.info(f"🚨 Alerta de sentimento: {event.kind} - {event.label}")
        if self.main_window:
            self.main_window.add_sentiment_alert(event)
    
    def _update_sentiment_dashboard(self, dashboard_data):
        """Atualizar dashboard de sentimento."""
        if self.main_window:
            self.main_window.update_sentiment_dashboard(dashboard_data)
    
    def show(self):
        """Exibir a janela principal."""
        if self.main_window:
            self.main_window.show()
    
    def start_recording(self):
        """Iniciar gravação e análise."""
        if not self.is_recording:
            self.logger.info("🎤 Iniciando gravação...")
            self.current_session_id = self.database.create_session()
            
            # Iniciar captura de áudio
            self.audio_capture.start()
            
            # Iniciar análise de sentimento
            if self.sentiment_service:
                self.sentiment_service.start(self.current_session_id)
            
            self.is_recording = True
    
    def stop_recording(self):
        """Parar gravação e gerar resumo."""
        if self.is_recording:
            self.logger.info("⏹️ Parando gravação...")
            
            # Parar captura de áudio
            self.audio_capture.stop()
            
            # Parar análise de sentimento
            if self.sentiment_service and self.current_session_id:
                self.sentiment_service.stop(self.current_session_id)
            
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
        
        if self.sentiment_service:
            self.sentiment_service.cleanup()
        
        if self.rag_service:
            self.rag_service.cleanup()
        
        if self.npu_manager:
            self.npu_manager.cleanup()
        
        if self.database:
            self.database.close()
        
        self.logger.info("✅ PitchAI encerrado")

"""
PitchAI - Classe Principal da Aplicação
=====================================

Coordena todos os módulos da aplicação:
- Interface PyQt6  
- Pipeline de IA com ONNX
- Captura de áudio
- Gerenciamento de dados
- Mentor Engine
"""

import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .config import Config
from .error_handler import ErrorHandler, ErrorContext, ErrorSeverity, ErrorCategory, handle_errors
from .performance_monitor import PerformanceMonitor, profile_operation
from .cache_manager import CacheManager, cache_result
from ui.main_window import MainWindow
from ai.onnx_manager import ONNXManager
from audio.capture import AudioCapture
from data.database import DatabaseManager
from .dashboard_service import DashboardService


class PitchAIApp(QObject):
    """Classe principal da aplicação PitchAI."""
    
    # Sinais para comunicação entre threads
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas de sentimento
    objection_detected = pyqtSignal(str, list) # objeção, sugestões
    opportunity_detected = pyqtSignal(str, list) # oportunidade, sugestões
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.main_window: Optional[MainWindow] = None
        
        # Componentes principais
        self.onnx_manager: Optional[ONNXManager] = None
        self.audio_capture: Optional[AudioCapture] = None
        self.database: Optional[DatabaseManager] = None

        # Componente do Dashboard
        self.dashboard_service: Optional[DashboardService] = None
        
        # Sistema de tratamento de erros
        self.error_handler: Optional[ErrorHandler] = None
        
        # Sistema de monitoramento de performance
        self.performance_monitor: Optional[PerformanceMonitor] = None
        
        # Sistema de cache
        self.cache_manager: Optional[CacheManager] = None
        
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
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Inicializar todos os componentes da aplicação."""
        try:
            self.logger.info("Inicializando PitchAI...")
            
            # 0. Inicializar sistemas de performance e cache
            self._initialize_error_handler()
            self._initialize_performance_monitor()
            self._initialize_cache_manager()
            
            # 1. Inicializar banco de dados
            self._initialize_database()

            # 2. Inicializar gerenciador ONNX
            self._initialize_onnx()

            # 3. Inicializar Dashboard Service
            self._initialize_dashboard_service()
            
            # 6. Inicializar captura de áudio
            self._initialize_audio()
            
            # 6. Inicializar interface
            self._initialize_ui()
            
            # 7. Conectar sinais
            self._connect_signals()
            
            self.logger.info("PitchAI inicializado com sucesso!")
            
        except Exception as e:
            # Usar sistema de tratamento de erros
            if self.error_handler:
                context = ErrorContext(
                    component="application",
                    operation="initialize"
                )
                self.error_handler.handle_error(
                    e, context, 
                    severity=ErrorSeverity.CRITICAL,
                    category=ErrorCategory.CONFIGURATION
                )
            else:
                self.logger.error(f"❌ Erro na inicialização: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    @handle_errors(severity=ErrorSeverity.HIGH, category=ErrorCategory.DATABASE, retry=True)
    def _initialize_database(self):
        """Inicializar gerenciador de banco de dados."""
        db_path = str(self.config.data_dir / "pitchai.db")
        self.database = DatabaseManager(db_path)
        self.logger.info("Banco de dados inicializado")
    
    @handle_errors(severity=ErrorSeverity.HIGH, category=ErrorCategory.AI_MODEL, retry=True)
    def _initialize_onnx(self):
        """Inicializar gerenciador ONNX."""
        self.onnx_manager = ONNXManager(self.config)
        self.onnx_manager.initialize()
        self.logger.info("✅ ONNX inicializada")
    

    
    @handle_errors(severity=ErrorSeverity.MEDIUM, category=ErrorCategory.DATABASE, retry=True)
    def _initialize_dashboard_service(self):
        """Inicializar Dashboard Service."""
        self.dashboard_service = DashboardService(self.database)
        self.logger.info("✅ Dashboard Service inicializado")
    
    def _initialize_error_handler(self):
        """Inicializar sistema de tratamento de erros."""
        self.error_handler = ErrorHandler(self.config)
        
        # Configurar estratégias de retry para operações críticas
        self.error_handler.register_retry_strategy("database_operation", max_retries=3, timeout=10.0)
        self.error_handler.register_retry_strategy("network_request", max_retries=2, timeout=30.0)
        self.error_handler.register_retry_strategy("audio_processing", max_retries=2, timeout=15.0)
        
        self.logger.info("✅ Sistema de tratamento de erros inicializado")
    
    def _initialize_performance_monitor(self):
        """Inicializar sistema de monitoramento de performance."""
        self.performance_monitor = PerformanceMonitor(self.config)
        self.performance_monitor.start_monitoring()
        
        self.logger.info("✅ Sistema de monitoramento de performance inicializado")
    
    def _initialize_cache_manager(self):
        """Inicializar sistema de cache."""
        self.cache_manager = CacheManager(self.config)
        self.logger.info("✅ Sistema de cache inicializado")
    
    @handle_errors(severity=ErrorSeverity.MEDIUM, category=ErrorCategory.AUDIO, fallback=True)
    def _initialize_audio(self):
        """Inicializar captura de áudio."""
        self.audio_capture = AudioCapture(self.config)
        self.audio_capture.initialize()
        self.logger.info("✅ Captura de áudio inicializada")
    
    def _initialize_ai_services(self):
        """Inicializar serviços de IA."""
        # Inicializar LLM Service com AnythingLLM
        from ai.llm_service import LLMService
        self.llm_service = LLMService(
            model_dir=self.config.app_dir / "models",
            use_simulation=False,
            use_anythingllm=True
        )
        self.llm_service.initialize()

        # Inicializar Summary Service com LLM Service
        self.summary_service = SummaryService(self.config, self.llm_service, self.database)
        self.logger.info("✅ Serviços de IA inicializados (com AnythingLLM)")

    def _initialize_call_manager(self):
        """Inicializar gerenciador de chamadas."""
        self.call_manager = CallManager(
            self.database,
            self.onnx_manager,
            self.summary_service
        )
        self.logger.info("✅ Gerenciador de chamadas inicializado")
    
    def _initialize_ui(self):
        """Inicializar interface PyQt6."""
        self.main_window = MainWindow(self.config, self)
        self.logger.info("Interface inicializada")
    
    def _connect_signals(self):
        """Conectar sinais entre componentes."""
        if self.audio_capture and self.onnx_manager:
            # Áudio → ONNX
            self.audio_capture.audio_ready.connect(
                self.onnx_manager.process_audio
            )

            # ONNX → UI
            self.onnx_manager.transcription_ready.connect(
                self.transcription_ready
            )
            self.onnx_manager.sentiment_updated.connect(
                self.sentiment_updated
            )
            self.onnx_manager.objection_detected.connect(
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

            # Iniciar nova sessão
            self.current_session_id = self.database.create_session()

            # Iniciar captura de áudio
            if self.audio_capture:
                self.audio_capture.start()

            self.is_recording = True

    def stop_recording(self):
        """Parar gravação e gerar resumo."""
        if self.is_recording:
            self.logger.info("⏹️ Parando gravação...")

            # Parar captura de áudio
            if self.audio_capture:
                self.audio_capture.stop()

            self.is_recording = False

            # Gerar resumo da sessão
            if self.current_session_id:
                self._generate_session_summary()
    
    def _generate_session_summary(self):
        """Gerar resumo da sessão atual."""
        try:
            if not self.current_session_id:
                self.logger.warning("Nenhuma sessão ativa para gerar resumo")
                return
            
            self.logger.info(f"📋 Gerando resumo da sessão {self.current_session_id}")
            
            # Coletar dados da sessão
            session_data = self._collect_session_data()
            
            # Gerar resumo simples
            summary = self._generate_simple_summary(session_data)
            self.logger.info(f"✅ Resumo simples gerado: {len(summary)} chars")
            
            # Salvar resumo
            self._save_session_summary(summary)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar resumo: {e}")
    
    def _collect_session_data(self) -> Dict[str, Any]:
        """Coletar dados da sessão atual."""
        try:
            # Obter transcrições
            transcriptions = []
            if hasattr(self, 'whisper_transcription') and self.whisper_transcription:
                # Aqui você coletaria as transcrições da sessão
                pass
            
            # Objeções serão implementadas posteriormente
            objections = []
            
            # Obter métricas
            metrics = {
                "duration_seconds": 0,  # Calcular duração real
                "transcriptions_count": len(transcriptions),
                "objections_total": len(objections),
                "objections_resolved": sum(1 for obj in objections if obj.get("resolved", False))
            }
            
            return {
                "session_id": self.current_session_id,
                "transcriptions": transcriptions,
                "objections": objections,
                "metrics": metrics
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao coletar dados da sessão: {e}")
            return {"session_id": self.current_session_id, "error": str(e)}
    
    def _generate_simple_summary(self, session_data: Dict[str, Any]) -> str:
        """Gerar resumo simples da sessão."""
        try:
            session_id = session_data.get("session_id", "unknown")
            metrics = session_data.get("metrics", {})
            objections = session_data.get("objections", [])
            
            summary = f"""# Resumo da Sessão {session_id}

## Métricas Gerais
- Duração: {metrics.get('duration_seconds', 0)} segundos
- Transcrições: {metrics.get('transcriptions_count', 0)}
- Objeções detectadas: {metrics.get('objections_total', 0)}
- Objeções resolvidas: {metrics.get('objections_resolved', 0)}

## Objeções Detectadas
"""
            
            if objections:
                for obj in objections:
                    status = "✅ RESOLVIDA" if obj.get("resolved") else "❌ PENDENTE"
                    summary += f"- {obj.get('category', 'unknown').upper()}: {status}\n"
            else:
                summary += "- Nenhuma objeção detectada\n"
            
            summary += "\n## Próximos Passos\n- Revisar gravação da sessão\n- Implementar melhorias identificadas\n- Agendar follow-up se necessário"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar resumo simples: {e}")
            return f"Erro ao gerar resumo da sessão {session_data.get('session_id', 'unknown')}: {e}"
    
    def _save_session_summary(self, summary: str):
        """Salvar resumo da sessão."""
        try:
            # Salvar em arquivo
            summary_file = self.config.app_dir / "sessions" / f"{self.current_session_id}_summary.md"
            summary_file.parent.mkdir(exist_ok=True)
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            self.logger.info(f"✅ Resumo salvo em: {summary_file}")
            
            # Publicar evento
            self.event_bus.publish("summary.generated", {
                "session_id": self.current_session_id,
                "summary": summary,
                "file_path": str(summary_file)
            })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar resumo: {e}")
    
    def get_mentor_analytics(self, seller_id: str = "default_seller"):
        """Obter analytics (implementação futura)."""
        # Analytics será implementado posteriormente
        return {
            "seller_id": seller_id,
            "status": "not_implemented",
            "message": "Analytics será implementado em versão futura"
        }
    
    def shutdown(self):
        """Encerrar aplicação graciosamente."""
        self.logger.info("Encerrando PitchAI...")
        
        if self.is_recording:
            self.stop_recording()
        
        if self.audio_capture:
            self.audio_capture.cleanup()
        
        if self.onnx_manager:
            self.onnx_manager.cleanup()
        
        if self.database:
            self.database.close()
        
        self.logger.info("✅ PitchAI encerrado")
"""
PitchAI - Classe Principal da Aplicação
=====================================

Coordena todos os módulos da aplicação:
- Interface PyQt6  
- Pipeline de IA na NPU
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
from ai.npu_manager import NPUManager
from ai.anythingllm_client import AnythingLLMClient
from audio.capture import AudioCapture
from data.database import DatabaseManager
from data.dao_mentor import DAOMentor
from client_profile.service import ClientProfileService
from mentor.mentor_engine import MentorEngine
from mentor.coach_feedback import CoachFeedback
from .dashboard_service import DashboardService


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
        
        # Componentes de IA e LLM
        self.anythingllm_client: Optional[AnythingLLMClient] = None
        
        # Componentes do Mentor Engine
        self.dao_mentor: Optional[DAOMentor] = None
        self.client_profile_service: Optional[ClientProfileService] = None
        self.coach_feedback: Optional[CoachFeedback] = None
        self.mentor_engine: Optional[MentorEngine] = None
        
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
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize(self):
        """Inicializar todos os componentes da aplicação."""
        try:
            self.logger.info("🚀 Inicializando PitchAI...")
            
            # 0. Inicializar sistemas de performance e cache
            self._initialize_error_handler()
            self._initialize_performance_monitor()
            self._initialize_cache_manager()
            
            # 1. Inicializar banco de dados
            self._initialize_database()
            
            # 2. Inicializar gerenciador NPU
            self._initialize_npu()
            
            # 3. Inicializar AnythingLLM
            self._initialize_anythingllm()
            
            # 4. Inicializar Mentor Engine
            self._initialize_mentor_engine()
            
            # 5. Inicializar Dashboard Service
            self._initialize_dashboard_service()
            
            # 6. Inicializar captura de áudio
            self._initialize_audio()
            
            # 6. Inicializar interface
            self._initialize_ui()
            
            # 7. Conectar sinais
            self._connect_signals()
            
            self.logger.info("✅ PitchAI inicializado com sucesso!")
            
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
        self.database = DatabaseManager(self.config)
        self.database.initialize()
        self.logger.info("✅ Banco de dados inicializado")
    
    @handle_errors(severity=ErrorSeverity.HIGH, category=ErrorCategory.AI_MODEL, retry=True)
    def _initialize_npu(self):
        """Inicializar gerenciador NPU."""
        self.npu_manager = NPUManager(self.config)
        self.npu_manager.initialize()
        self.logger.info("✅ NPU inicializada")
    
    @handle_errors(severity=ErrorSeverity.MEDIUM, category=ErrorCategory.NETWORK, fallback=True)
    def _initialize_anythingllm(self):
        """Inicializar cliente AnythingLLM."""
        self.anythingllm_client = AnythingLLMClient(
            base_url=self.config.anythingllm_url,
            api_key=self.config.anythingllm_api_key,
            timeout=self.config.anythingllm_timeout
        )
        
        if self.anythingllm_client.health_check():
            self.logger.info("✅ AnythingLLM conectado")
        else:
            self.logger.warning("⚠️ AnythingLLM não disponível - usando fallback")
    
    @handle_errors(severity=ErrorSeverity.HIGH, category=ErrorCategory.CONFIGURATION, retry=True)
    def _initialize_mentor_engine(self):
        """Inicializar Mentor Engine."""
        # 1. Inicializar DAO Mentor
        self.dao_mentor = DAOMentor(self.database.connection)
        
        # 2. Inicializar Client Profile Service
        self.client_profile_service = ClientProfileService(self.dao_mentor)
        
        # 3. Inicializar Coach Feedback com AnythingLLM
        self.coach_feedback = CoachFeedback(
            llm_client=self.anythingllm_client,
            dao_mentor=self.dao_mentor,
            timeout_s=self.config.anythingllm_timeout
        )
        
        # 4. Inicializar Mentor Engine
        self.mentor_engine = MentorEngine(
            event_bus=self._create_event_bus(),
            dao=self.dao_mentor,
            client_profile_service=self.client_profile_service,
            coach=self.coach_feedback
        )
        
        self.logger.info("✅ Mentor Engine inicializado")
    
    @handle_errors(severity=ErrorSeverity.MEDIUM, category=ErrorCategory.DATABASE, retry=True)
    def _initialize_dashboard_service(self):
        """Inicializar Dashboard Service."""
        self.dashboard_service = DashboardService(self.database, self.dao_mentor)
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
        
        # Configurar prefetch para operações comuns
        self.cache_manager.register_prefetch_pattern(
            "rag_passages", 
            lambda key: self._prefetch_rag_passages(key)
        )
        
        self.logger.info("✅ Sistema de cache inicializado")
    
    def _prefetch_rag_passages(self, key: str):
        """Prefetch de passagens RAG."""
        try:
            # Extrair categoria da chave
            if "preco" in key:
                return self._get_prefetch_passages("preco")
            elif "timing" in key:
                return self._get_prefetch_passages("timing")
            # Adicionar mais categorias conforme necessário
        except Exception as e:
            self.logger.warning(f"Erro no prefetch: {e}")
            return None
    
    def _get_prefetch_passages(self, category: str):
        """Obter passagens para prefetch."""
        # Implementação simples - em produção seria mais sofisticada
        return [{"id": f"prefetch_{category}", "content": f"Conteúdo {category}"}]
    
    def _create_event_bus(self):
        """Criar um EventBus robusto para o Mentor Engine."""
        from .event_bus import EventBus
        
        # Usar EventBus robusto em vez do simples
        event_bus = EventBus()
        event_bus.start()  # Iniciar thread de processamento
        
        return event_bus
    
    @handle_errors(severity=ErrorSeverity.MEDIUM, category=ErrorCategory.AUDIO, fallback=True)
    def _initialize_audio(self):
        """Inicializar captura de áudio."""
        self.audio_capture = AudioCapture(self.config)
        self.audio_capture.initialize()
        self.logger.info("✅ Captura de áudio inicializada")
    
    def _initialize_ai_services(self):
        """Inicializar serviços de IA."""
        self.summary_service = SummaryService(self.npu_manager, self.database)
        self.logger.info("✅ Serviços de IA inicializados")
    
    def _initialize_call_manager(self):
        """Inicializar gerenciador de chamadas."""
        self.call_manager = CallManager(
            self.database, 
            self.npu_manager, 
            self.summary_service
        )
        self.logger.info("✅ Gerenciador de chamadas inicializado")
    
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
        
        # Conectar Mentor Engine se disponível
        if self.mentor_engine:
            # Mentor Engine → UI
            self.mentor_engine.mentor_client_context.connect(
                self._on_mentor_context
            )
            self.mentor_engine.mentor_update.connect(
                self._on_mentor_update
            )
            self.mentor_engine.mentor_coaching.connect(
                self._on_mentor_coaching
            )
            self.mentor_engine.xp_awarded.connect(
                self._on_xp_awarded
            )
            self.mentor_engine.leaderboard_updated.connect(
                self._on_leaderboard_updated
            )
        
        self.logger.info("✅ Sinais conectados")
    
    def _on_mentor_context(self, context):
        """Handler para contexto do cliente do Mentor Engine."""
        self.logger.info(f"🎯 Contexto do cliente: {context.get('tier', 'unknown')}/{context.get('stage', 'unknown')}")
    
    def _on_mentor_update(self, update):
        """Handler para atualizações do Mentor Engine."""
        self.logger.info(f"💡 Insight do mentor: {update.get('insight', 'N/A')}")
    
    def _on_mentor_coaching(self, coaching):
        """Handler para coaching do Mentor Engine."""
        self.logger.info(f"🎓 Coaching gerado para call {coaching.get('call_id', 'unknown')}")
    
    def _on_xp_awarded(self, xp_event):
        """Handler para XP concedido."""
        self.logger.info(f"⭐ XP concedido: +{xp_event.get('xp', 0)} para {xp_event.get('seller_id', 'unknown')}")
    
    def _on_leaderboard_updated(self, leaderboard):
        """Handler para atualização do leaderboard."""
        self.logger.info(f"🏆 Leaderboard atualizado: {len(leaderboard.get('top', []))} vendedores")
    
    def show(self):
        """Exibir a janela principal."""
        if self.main_window:
            self.main_window.show()
    
    def start_recording(self):
        """Iniciar gravação e análise."""
        if not self.is_recording:
            self.logger.info("🎤 Iniciando gravação...")
            
            # Iniciar nova chamada
            self.current_session_id = self.call_manager.start_call()
            
            # Iniciar captura de áudio
            if self.audio_capture:
                self.audio_capture.start()
            
            self.is_recording = True
            
            # Simular dados para desenvolvimento
            if self.config.get('demo_mode', True):
                self.call_manager.simulate_call_data()
    
    def stop_recording(self):
        """Parar gravação e gerar resumo."""
        if self.is_recording:
            self.logger.info("⏹️ Parando gravação...")
            
            # Parar captura de áudio
            if self.audio_capture:
                self.audio_capture.stop()
            
            # Finalizar chamada e gerar resumo automático
            if self.call_manager and self.call_manager.is_call_active():
                summary = self.call_manager.end_call()
                if summary:
                    self.logger.info(f"📋 Resumo gerado com {len(summary.key_points)} pontos principais")
            
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
            
            # Gerar resumo usando RAG Service se disponível
            if hasattr(self, 'rag_service') and self.rag_service:
                summary = self.rag_service.generate_session_summary(session_data)
                self.logger.info(f"✅ Resumo gerado via RAG Service: {len(summary)} chars")
            else:
                # Fallback para resumo simples
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
            
            # Obter objeções detectadas
            objections = []
            if hasattr(self, 'mentor_engine') and self.mentor_engine:
                objections_summary = self.mentor_engine.get_objections_summary(self.current_session_id)
                objections = objections_summary.get("details", [])
            
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
        """Obter analytics do Mentor Engine."""
        if self.mentor_engine:
            return self.mentor_engine.get_seller_analytics(seller_id)
        return {}
    
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

        print("💾 Persistindo resumo no banco de dados...")
        # self.database_manager.save_summary(call_id, summary)
        print(f"📄 Resumo final:\n{summary}")

    def _on_new_transcription(self, text, speaker):
        """Callback para lidar com novos trechos de transcrição."""
        self._call_transcript.append({"speaker": speaker, "text": text})
        # ...lógica para enviar à UI...

    # ...outros callbacks para objeções e métricas...
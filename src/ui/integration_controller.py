"""
Integration Controller - Controlador de Integração Backend/Frontend
================================================================

Coordena a integração entre os serviços de backend (captura de áudio,
transcrição, análise de sentimento) e os widgets do frontend PyQt6.
"""

import logging
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Imports com fallback para execução direta
try:
    from ..core.config import Config
    from ..audio.capture import AudioCapture
    from ..ai.asr_whisper import TranscriptionService, TranscriptChunk
    from ..ai.llm_service import LLMService
    from ..ai.model_manager import ModelManager
    from ..ai.sentiment.models import SentimentConfig
    from ..ai.sentiment.sentiment_service import SentimentService
    from ..ai.rag_service import RAGService
    from ..data.database import DatabaseManager
    from ..core.summary_service import PostCallSummaryService
except ImportError:
    # Fallback para execução direta
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

    from core.config import Config
    from audio.capture import AudioCapture
    from ai.asr_whisper import TranscriptionService, TranscriptChunk
    from ai.llm_service import LLMService
    from ai.model_manager import ModelManager
    from ai.sentiment.models import SentimentConfig
    from ai.sentiment.sentiment_service import SentimentService
    from ai.rag_service import RAGService
    from data.database import DatabaseManager
    from core.summary_service import PostCallSummaryService


class IntegrationController(QObject):
    """Controlador principal da integração backend/frontend."""

    # Sinais para comunicação com o frontend
    transcription_updated = pyqtSignal(object)  # TranscriptChunk
    sentiment_updated = pyqtSignal(dict)        # dados de sentimento
    audio_capture_status = pyqtSignal(bool)     # status da captura
    error_occurred = pyqtSignal(str)           # erros gerais
    summary_generated = pyqtSignal(dict)       # resumo gerado

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Serviços backend
        self.audio_capture: Optional[AudioCapture] = None
        self.transcription_service: Optional[TranscriptionService] = None
        self.llm_service: Optional[LLMService] = None
        self.model_manager: Optional[ModelManager] = None
        self.sentiment_service: Optional[SentimentService] = None
        self.rag_service: Optional[RAGService] = None
        self.database_manager: Optional[DatabaseManager] = None
        self.summary_service: Optional[PostCallSummaryService] = None

        # Estado da aplicação
        self.is_initialized = False
        self.current_call_id: Optional[str] = None
        self.is_capturing = False

        # Estatísticas
        self.stats = {
            "chunks_processed": 0,
            "transcription_latency_avg": 0.0,
            "sentiment_updates": 0,
            "errors_count": 0
        }

    def initialize(self) -> bool:
        """Inicializar todos os serviços."""
        try:
            self.logger.info("🔄 Inicializando Integration Controller...")

            # Inicializar Model Manager (para modelos ONNX)
            self.model_manager = ModelManager(self.config)
            self.model_manager.load_manifest()

            # Inicializar LLM Service
            self.llm_service = LLMService(use_simulation=False)
            if not self.llm_service.initialize():
                self.logger.warning("⚠️ LLM Service não disponível, usando simulação")

            # Inicializar serviços de IA
            self._initialize_ai_services()

            # Inicializar captura de áudio
            self._initialize_audio_capture()

            self.is_initialized = True
            self.logger.info("✅ Integration Controller inicializado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {e}")
            self.error_occurred.emit(str(e))
            return False

    def _initialize_ai_services(self):
        """Inicializar serviços de IA."""
        try:
            # Serviço de Transcrição Whisper
            self.transcription_service = TranscriptionService(
                self.config,
                model_entry=self.model_manager.get_model_entry("whisper_small_encoder"),
                model_manager=self.model_manager
            )
            self.transcription_service.initialize()

            # Conectar sinais da transcrição
            self.transcription_service.transcript_chunk_ready.connect(self._on_transcript_chunk)

            # Serviço de Análise de Sentimento
            sentiment_config = SentimentConfig()
            self.sentiment_service = SentimentService(sentiment_config, self.llm_service)

            # Serviço RAG para objeções
            self.rag_service = RAGService(self.config, self.llm_service)

            # Database Manager para armazenamento
            self.database_manager = DatabaseManager(self.config)
            self.database_manager.initialize()

            # Serviço de resumo pós-chamada
            self.summary_service = PostCallSummaryService(self.config, self.llm_service, self.database_manager)

            self.logger.info("✅ Serviços de IA e BD inicializados")

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar serviços de IA: {e}")
            raise

    def _initialize_audio_capture(self):
        """Inicializar captura de áudio."""
        try:
            self.audio_capture = AudioCapture(self.config)
            self.audio_capture.initialize()

            # Conectar sinais de áudio
            self.audio_capture.audio_ready.connect(self._on_audio_chunk)
            self.audio_capture.capture_started.connect(self._on_capture_started)
            self.audio_capture.capture_stopped.connect(self._on_capture_stopped)
            self.audio_capture.error_occurred.connect(self._on_audio_error)

            self.logger.info("✅ Captura de áudio inicializada")

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar captura de áudio: {e}")
            raise

    def connect_transcription_widget(self, transcription_widget):
        """Conectar widget de transcrição para integração."""
        if transcription_widget and self.database_manager:
            transcription_widget.database_manager = self.database_manager
            transcription_widget.summary_requested.connect(self._on_summary_requested)
            transcription_widget.transcription_saved.connect(self._on_transcription_saved)
            self.logger.info("✅ Widget de transcrição conectado")

    def _on_summary_requested(self, call_id: str):
        """Solicitação de resumo recebida."""
        try:
            self.logger.info(f"🤖 Gerando resumo para call_id: {call_id}")

            if not self.summary_service:
                self.logger.error("Serviço de resumo não disponível")
                return

            # Gerar resumo
            summary = self.summary_service.generate(call_id)

            if summary:
                self.logger.info("✅ Resumo gerado com sucesso")
                # Emitir sinal para o widget
                self.summary_generated.emit(summary)
            else:
                self.logger.error("❌ Falha ao gerar resumo")

        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")

    def _on_transcription_saved(self, call_id: str):
        """Transcrição salva no BD."""
        self.logger.info(f"💾 Transcrição salva para call_id: {call_id}")

    def get_transcription_widget(self):
        """Obter widget de transcrição configurado."""
        # Este método será usado pelo MainWindow para obter o widget configurado
        return None  # Implementação será feita no MainWindow

    def start_capture(self) -> bool:
        """Iniciar captura de áudio e processamento."""
        if not self.is_initialized:
            self.error_occurred.emit("Sistema não inicializado")
            return False

        try:
            self.logger.info("🎤 Iniciando captura integrada...")

            # Iniciar captura de áudio
            self.audio_capture.start()
            self.is_capturing = True

            # Gerar novo call_id
            import uuid
            self.current_call_id = str(uuid.uuid4())

            # Iniciar transcrição
            if self.transcription_service:
                self.transcription_service.start(self.current_call_id)

            # Iniciar análise de sentimento
            if self.sentiment_service:
                self.sentiment_service.start_analysis(self.current_call_id)

            self.audio_capture_status.emit(True)
            self.logger.info(f"✅ Captura integrada iniciada (call_id: {self.current_call_id})")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar captura: {e}")
            self.error_occurred.emit(str(e))
            return False

    def stop_capture(self) -> bool:
        """Parar captura de áudio e processamento."""
        if not self.is_capturing:
            return True

        try:
            self.logger.info("⏹️ Parando captura integrada...")

            # Parar análise de sentimento
            if self.sentiment_service:
                self.sentiment_service.stop_analysis()

            # Parar transcrição
            if self.transcription_service:
                self.transcription_service.stop(self.current_call_id)

            # Parar captura de áudio
            self.audio_capture.stop()
            self.is_capturing = False

            # Log de estatísticas
            self._log_session_stats()

            self.audio_capture_status.emit(False)
            self.logger.info("✅ Captura integrada parada")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao parar captura: {e}")
            self.error_occurred.emit(str(e))
            return False

    def _on_audio_chunk(self, chunk):
        """Receber chunk de áudio e encaminhar para transcrição."""
        if self.transcription_service and self.is_capturing:
            try:
                self.transcription_service.push_audio_chunk(chunk)
            except Exception as e:
                self.logger.error(f"Erro ao processar chunk de áudio: {e}")

    def _on_transcript_chunk(self, chunk: TranscriptChunk):
        """Receber chunk de transcrição e emitir para frontend."""
        try:
            self.stats["chunks_processed"] += 1

            # Emitir para frontend
            self.transcription_updated.emit(chunk)

            # Encaminhar para análise de sentimento
            if self.sentiment_service and self.is_capturing:
                # Simular dados de sentimento baseados na transcrição
                sentiment_data = self._extract_sentiment_from_text(chunk)
                if sentiment_data:
                    self.sentiment_updated.emit(sentiment_data)

        except Exception as e:
            self.logger.error(f"Erro ao processar chunk de transcrição: {e}")

    def _extract_sentiment_from_text(self, chunk: TranscriptChunk) -> Optional[Dict[str, Any]]:
        """Extrair sentimento básico do texto da transcrição."""
        try:
            text = chunk.text.lower()

            # Palavras positivas
            positive_words = ["ótimo", "excelente", "perfeito", "gostei", "concordo", "sim", "claro"]
            # Palavras negativas
            negative_words = ["ruim", "péssimo", "problema", "não", "infelizmente", "preocupado", "dúvida"]

            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)

            # Calcular sentimento básico (-1 a 1)
            total_words = len(text.split())
            if total_words == 0:
                return None

            sentiment_score = (positive_count - negative_count) / max(total_words * 0.1, 1)
            sentiment_score = max(-1.0, min(1.0, sentiment_score))

            # Converter para percentual
            sentiment_percent = int((sentiment_score + 1) * 50)  # 0-100

            return {
                "sentiment_percent": sentiment_percent,
                "engagement_percent": 75,  # Simulado
                "buying_signals_count": 0,  # Implementar depois
                "alerts": [],
                "source": chunk.source,
                "timestamp": chunk.ts_start_ms
            }

        except Exception as e:
            self.logger.warning(f"Erro ao extrair sentimento: {e}")
            return None

    def _on_capture_started(self):
        """Captura de áudio iniciada."""
        self.logger.info("🎤 Captura de áudio iniciada")

    def _on_capture_stopped(self):
        """Captura de áudio parada."""
        self.logger.info("⏹️ Captura de áudio parada")

    def _on_audio_error(self, error_msg: str):
        """Erro na captura de áudio."""
        self.logger.error(f"❌ Erro na captura de áudio: {error_msg}")
        self.stats["errors_count"] += 1
        self.error_occurred.emit(f"Erro na captura: {error_msg}")

    def _log_session_stats(self):
        """Log das estatísticas da sessão."""
        self.logger.info("📊 Estatísticas da sessão:")
        self.logger.info(f"   Chunks processados: {self.stats['chunks_processed']}")
        self.logger.info(f"   Latência média: {self.stats['transcription_latency_avg']:.2f}ms")
        self.logger.info(f"   Atualizações de sentimento: {self.stats['sentiment_updates']}")
        self.logger.info(f"   Erros: {self.stats['errors_count']}")

    def get_status(self) -> Dict[str, Any]:
        """Obter status do controlador."""
        return {
            "is_initialized": self.is_initialized,
            "is_capturing": self.is_capturing,
            "current_call_id": self.current_call_id,
            "services_status": {
                "audio_capture": self.audio_capture is not None,
                "transcription": self.transcription_service is not None,
                "llm_service": self.llm_service is not None and self.llm_service.is_initialized,
                "sentiment": self.sentiment_service is not None,
                "rag": self.rag_service is not None
            },
            "stats": self.stats.copy()
        }

    def cleanup(self):
        """Limpar recursos."""
        self.logger.info("🔄 Limpando Integration Controller...")

        try:
            self.stop_capture()

            if self.audio_capture:
                self.audio_capture.cleanup()
            if self.transcription_service:
                self.transcription_service.cleanup()
            if self.llm_service:
                self.llm_service.cleanup()
            if self.sentiment_service:
                self.sentiment_service.cleanup()
            if self.rag_service:
                self.rag_service.cleanup()

            self.is_initialized = False
            self.logger.info("✅ Integration Controller limpo")

        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {e}")

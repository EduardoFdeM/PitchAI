"""
AnythingLLM Integration - Integração Completa com LLM Local
=========================================================

Serviço central que integra o AnythingLLM com todos os componentes do PitchAI:
- Transcrição e análise de sentimento
- Detecção de objeções e sugestões RAG
- Geração de resumos pós-call
- Análise de performance e coaching
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

from .anythingllm_client import AnythingLLMClient, RAGPassage, RAGResponse, Suggestion
from .rag_service import RAGService, ObjectionEvent, RAGResult


@dataclass
class CallSession:
    """Dados completos de uma sessão de call."""
    call_id: str
    seller_id: str
    client_id: str
    start_time: int
    end_time: Optional[int] = None
    
    # Transcrições
    transcriptions: List[Dict[str, Any]] = None
    
    # Análises
    sentiment_data: List[Dict[str, Any]] = None
    objections: List[Dict[str, Any]] = None
    engagement_data: List[Dict[str, Any]] = None
    
    # Métricas
    metrics: Dict[str, Any] = None
    
    # Resumos
    summary: Optional[str] = None
    coaching_feedback: Optional[str] = None
    
    def __post_init__(self):
        if self.transcriptions is None:
            self.transcriptions = []
        if self.sentiment_data is None:
            self.sentiment_data = []
        if self.objections is None:
            self.objections = []
        if self.engagement_data is None:
            self.engagement_data = []
        if self.metrics is None:
            self.metrics = {}


class AnythingLLMIntegrationWorker(QThread):
    """Worker thread para processamento assíncrono com AnythingLLM."""
    
    # Sinais de resultado
    objection_processed = pyqtSignal(object)  # RAGResult
    summary_generated = pyqtSignal(str, str)  # call_id, summary
    coaching_generated = pyqtSignal(str, str)  # call_id, coaching
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, anythingllm_client: AnythingLLMClient):
        super().__init__()
        self.client = anythingllm_client
        self.current_task: Optional[Dict[str, Any]] = None
    
    def process_objection(self, objection_event: ObjectionEvent, passages: List[RAGPassage]):
        """Processar objeção em thread separada."""
        self.current_task = {
            "type": "objection",
            "objection": objection_event,
            "passages": passages
        }
        self.start()
    
    def generate_summary(self, session_data: Dict[str, Any]):
        """Gerar resumo em thread separada."""
        self.current_task = {
            "type": "summary",
            "session_data": session_data
        }
        self.start()
    
    def generate_coaching(self, session_data: Dict[str, Any]):
        """Gerar coaching em thread separada."""
        self.current_task = {
            "type": "coaching",
            "session_data": session_data
        }
        self.start()
    
    def run(self):
        """Executar tarefa atual."""
        try:
            if not self.current_task:
                self.error_occurred.emit("Nenhuma tarefa definida")
                return
            
            task_type = self.current_task["type"]
            
            if task_type == "objection":
                self._process_objection_task()
            elif task_type == "summary":
                self._generate_summary_task()
            elif task_type == "coaching":
                self._generate_coaching_task()
            else:
                self.error_occurred.emit(f"Tipo de tarefa desconhecido: {task_type}")
                
        except Exception as e:
            self.error_occurred.emit(f"Erro no worker: {e}")
    
    def _process_objection_task(self):
        """Processar tarefa de objeção."""
        objection = self.current_task["objection"]
        passages = self.current_task["passages"]
        
        # Gerar sugestões usando AnythingLLM
        response = self.client.generate_objection_suggestions(
            objection=objection.text,
            passages=passages
        )
        
        # Criar resultado
        result = RAGResult(
            call_id=objection.call_id,
            objection=objection,
            suggestions=response.suggestions,
            retrieved_passages=response.retrieved,
            latency_ms=response.latency_ms,
            model_info=response.model_info
        )
        
        self.objection_processed.emit(result)
    
    def _generate_summary_task(self):
        """Gerar resumo da sessão."""
        session_data = self.current_task["session_data"]
        call_id = session_data.get("call_id", "unknown")
        
        summary = self.client.generate_session_summary(session_data)
        self.summary_generated.emit(call_id, summary)
    
    def _generate_coaching_task(self):
        """Gerar feedback de coaching."""
        session_data = self.current_task["session_data"]
        call_id = session_data.get("call_id", "unknown")
        
        coaching = self._generate_coaching_feedback(session_data)
        self.coaching_generated.emit(call_id, coaching)
    
    def _generate_coaching_feedback(self, session_data: Dict[str, Any]) -> str:
        """Gerar feedback de coaching personalizado."""
        try:
            # Preparar contexto para coaching
            context = self._prepare_coaching_context(session_data)
            
            system_prompt = (
                "Você é um coach de vendas experiente. Analise a sessão e forneça feedback "
                "construtivo e acionável. Foque em: "
                "• Pontos fortes identificados "
                "• Áreas de melhoria "
                "• Técnicas específicas para aplicar "
                "• Próximos passos recomendados "
                "Seja específico e encorajador."
            )
            
            user_prompt = f"Analise esta sessão de vendas e forneça coaching:\n\n{context}"
            
            # Usar AnythingLLM para gerar coaching
            payload = {
                "model": self.client.default_model,
                "temperature": 0.3,
                "stream": False,
                "max_tokens": 512,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            response = self.client._make_request(payload, stream=False)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                return "Erro ao gerar feedback de coaching."
                
        except Exception as e:
            logging.error(f"Erro ao gerar coaching: {e}")
            return "Não foi possível gerar feedback de coaching."
    
    def _prepare_coaching_context(self, session_data: Dict[str, Any]) -> str:
        """Preparar contexto para coaching."""
        context_parts = []
        
        # Métricas gerais
        metrics = session_data.get("metrics", {})
        context_parts.append("MÉTRICAS DA SESSÃO:")
        context_parts.append(f"- Duração: {metrics.get('duration_seconds', 0)} segundos")
        context_parts.append(f"- Objeções: {metrics.get('objections_total', 0)} (resolvidas: {metrics.get('objections_resolved', 0)})")
        context_parts.append(f"- Sentimento médio: {metrics.get('sentiment_avg', 0):.2f}")
        context_parts.append(f"- Engajamento: {metrics.get('engagement_avg', 0):.2f}")
        
        # Objeções específicas
        objections = session_data.get("objections", [])
        if objections:
            context_parts.append("\nOBJEÇÕES DETECTADAS:")
            for obj in objections:
                status = "RESOLVIDA" if obj.get("resolved") else "PENDENTE"
                context_parts.append(f"- {obj.get('category', 'unknown')}: {status}")
        
        # Transcrições relevantes
        transcriptions = session_data.get("transcriptions", [])
        if transcriptions:
            context_parts.append("\nMOMENTOS CHAVE:")
            for trans in transcriptions[-5:]:  # Últimas 5 transcrições
                speaker = trans.get("speaker", "unknown")
                text = trans.get("text", "")[:100]  # Primeiros 100 chars
                if text:
                    context_parts.append(f"- {speaker}: {text}...")
        
        return "\n".join(context_parts)


class AnythingLLMIntegration(QObject):
    """Serviço de integração completa com AnythingLLM."""
    
    # Sinais principais
    objection_suggestions_ready = pyqtSignal(object)  # RAGResult
    session_summary_ready = pyqtSignal(str, str)      # call_id, summary
    coaching_feedback_ready = pyqtSignal(str, str)    # call_id, coaching
    integration_error = pyqtSignal(str)               # error message
    
    # Sinais de status
    llm_status_changed = pyqtSignal(bool)             # available/not available
    processing_status_changed = pyqtSignal(bool)      # processing/not processing
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cliente AnythingLLM
        self.anythingllm_client = AnythingLLMClient(
            base_url=getattr(config, 'anythingllm_url', 'http://127.0.0.1:3001'),
            api_key=getattr(config, 'anythingllm_api_key', 'local-dev'),
            timeout=getattr(config, 'anythingllm_timeout', 5.0)
        )
        
        # RAG Service
        self.rag_service = RAGService(config)
        
        # Worker thread
        self.worker = AnythingLLMIntegrationWorker(self.anythingllm_client)
        self.worker.objection_processed.connect(self._on_objection_processed)
        self.worker.summary_generated.connect(self._on_summary_generated)
        self.worker.coaching_generated.connect(self._on_coaching_generated)
        self.worker.error_occurred.connect(self._on_worker_error)
        
        # Estado
        self.is_available = False
        self.is_processing = False
        self.active_sessions: Dict[str, CallSession] = {}
        
        # Timer para health check
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_availability)
        self.health_check_timer.start(30000)  # 30 segundos
        
        # Verificação inicial
        self._check_availability()
    
    def _check_availability(self):
        """Verificar disponibilidade do AnythingLLM."""
        try:
            was_available = self.is_available
            self.is_available = self.anythingllm_client.health_check()
            
            if self.is_available != was_available:
                self.llm_status_changed.emit(self.is_available)
                
                if self.is_available:
                    self.logger.info("✅ AnythingLLM disponível para integração")
                else:
                    self.logger.warning("⚠️ AnythingLLM não disponível")
                    
        except Exception as e:
            self.logger.error(f"Erro ao verificar disponibilidade: {e}")
            self.is_available = False
            self.llm_status_changed.emit(False)
    
    def start_session(self, call_id: str, seller_id: str, client_id: str) -> bool:
        """Iniciar nova sessão de call."""
        try:
            if call_id in self.active_sessions:
                self.logger.warning(f"Sessão {call_id} já existe")
                return False
            
            session = CallSession(
                call_id=call_id,
                seller_id=seller_id,
                client_id=client_id,
                start_time=int(time.time() * 1000)
            )
            
            self.active_sessions[call_id] = session
            self.logger.info(f"✅ Sessão iniciada: {call_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar sessão: {e}")
            return False
    
    def end_session(self, call_id: str) -> Optional[CallSession]:
        """Finalizar sessão de call."""
        try:
            if call_id not in self.active_sessions:
                self.logger.warning(f"Sessão {call_id} não encontrada")
                return None
            
            session = self.active_sessions[call_id]
            session.end_time = int(time.time() * 1000)
            
            # Calcular métricas finais
            session.metrics["duration_seconds"] = (session.end_time - session.start_time) / 1000
            session.metrics["objections_total"] = len(session.objections)
            session.metrics["objections_resolved"] = sum(1 for obj in session.objections if obj.get("resolved", False))
            
            if session.sentiment_data:
                sentiments = [d.get("sentiment", 0) for d in session.sentiment_data]
                session.metrics["sentiment_avg"] = sum(sentiments) / len(sentiments)
            
            if session.engagement_data:
                engagements = [d.get("engagement", 0) for d in session.engagement_data]
                session.metrics["engagement_avg"] = sum(engagements) / len(engagements)
            
            self.logger.info(f"✅ Sessão finalizada: {call_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar sessão: {e}")
            return None
    
    def add_transcription(self, call_id: str, speaker: str, text: str, confidence: float):
        """Adicionar transcrição à sessão."""
        try:
            if call_id not in self.active_sessions:
                self.logger.warning(f"Sessão {call_id} não encontrada para transcrição")
                return
            
            session = self.active_sessions[call_id]
            transcription = {
                "speaker": speaker,
                "text": text,
                "confidence": confidence,
                "timestamp": int(time.time() * 1000)
            }
            
            session.transcriptions.append(transcription)
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar transcrição: {e}")
    
    def add_sentiment(self, call_id: str, sentiment: float, emotion: str):
        """Adicionar análise de sentimento à sessão."""
        try:
            if call_id not in self.active_sessions:
                return
            
            session = self.active_sessions[call_id]
            sentiment_data = {
                "sentiment": sentiment,
                "emotion": emotion,
                "timestamp": int(time.time() * 1000)
            }
            
            session.sentiment_data.append(sentiment_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar sentimento: {e}")
    
    def add_objection(self, call_id: str, category: str, text: str, context: str = ""):
        """Adicionar objeção detectada à sessão."""
        try:
            if call_id not in self.active_sessions:
                return
            
            session = self.active_sessions[call_id]
            objection = {
                "category": category,
                "text": text,
                "context": context,
                "timestamp": int(time.time() * 1000),
                "resolved": False
            }
            
            session.objections.append(objection)
            
            # Processar objeção com RAG se disponível
            if self.is_available:
                self._process_objection_with_rag(call_id, objection)
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar objeção: {e}")
    
    def _process_objection_with_rag(self, call_id: str, objection: Dict[str, Any]):
        """Processar objeção usando RAG."""
        try:
            # Criar evento de objeção
            objection_event = ObjectionEvent(
                call_id=call_id,
                category=objection["category"],
                text=objection["text"],
                context_snippet=objection.get("context", ""),
                timestamp_ms=objection["timestamp"]
            )
            
            # Recuperar passagens relevantes
            passages = self.rag_service.retrieve_passages(
                objection["text"],
                objection["category"],
                top_k=3
            )
            
            # Processar em thread separada
            self.worker.process_objection(objection_event, passages)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar objeção com RAG: {e}")
    
    def generate_session_summary(self, call_id: str) -> bool:
        """Gerar resumo da sessão."""
        try:
            if call_id not in self.active_sessions:
                self.logger.warning(f"Sessão {call_id} não encontrada para resumo")
                return False
            
            session = self.active_sessions[call_id]
            
            # Preparar dados da sessão
            session_data = {
                "call_id": call_id,
                "seller_id": session.seller_id,
                "client_id": session.client_id,
                "transcriptions": session.transcriptions,
                "objections": session.objections,
                "metrics": session.metrics
            }
            
            # Gerar em thread separada
            self.worker.generate_summary(session_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            return False
    
    def generate_coaching_feedback(self, call_id: str) -> bool:
        """Gerar feedback de coaching."""
        try:
            if call_id not in self.active_sessions:
                self.logger.warning(f"Sessão {call_id} não encontrada para coaching")
                return False
            
            session = self.active_sessions[call_id]
            
            # Preparar dados da sessão
            session_data = {
                "call_id": call_id,
                "seller_id": session.seller_id,
                "client_id": session.client_id,
                "transcriptions": session.transcriptions,
                "objections": session.objections,
                "metrics": session.metrics
            }
            
            # Gerar em thread separada
            self.worker.generate_coaching(session_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar coaching: {e}")
            return False
    
    def _on_objection_processed(self, result: RAGResult):
        """Callback quando objeção é processada."""
        self.logger.info(f"✅ Objeção processada: {result.call_id}")
        self.objection_suggestions_ready.emit(result)
    
    def _on_summary_generated(self, call_id: str, summary: str):
        """Callback quando resumo é gerado."""
        try:
            if call_id in self.active_sessions:
                self.active_sessions[call_id].summary = summary
            
            self.logger.info(f"✅ Resumo gerado: {call_id}")
            self.session_summary_ready.emit(call_id, summary)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar resumo: {e}")
    
    def _on_coaching_generated(self, call_id: str, coaching: str):
        """Callback quando coaching é gerado."""
        try:
            if call_id in self.active_sessions:
                self.active_sessions[call_id].coaching_feedback = coaching
            
            self.logger.info(f"✅ Coaching gerado: {call_id}")
            self.coaching_feedback_ready.emit(call_id, coaching)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar coaching: {e}")
    
    def _on_worker_error(self, error: str):
        """Callback quando worker falha."""
        self.logger.error(f"❌ Erro no worker: {error}")
        self.integration_error.emit(error)
    
    def get_session(self, call_id: str) -> Optional[CallSession]:
        """Obter sessão por ID."""
        return self.active_sessions.get(call_id)
    
    def get_all_sessions(self) -> List[CallSession]:
        """Obter todas as sessões ativas."""
        return list(self.active_sessions.values())
    
    def cleanup(self):
        """Limpar recursos."""
        try:
            # Parar timer
            if self.health_check_timer.isActive():
                self.health_check_timer.stop()
            
            # Parar worker
            if self.worker.isRunning():
                self.worker.quit()
                self.worker.wait()
            
            # Limpar RAG service
            if self.rag_service:
                self.rag_service.cleanup()
            
            self.logger.info("✅ AnythingLLM Integration limpo")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar integração: {e}") 
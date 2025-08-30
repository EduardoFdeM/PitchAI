"""
RAG Service - Integração com AnythingLLM
======================================

Serviço que integra o AnythingLLM com o sistema de detecção de objeções,
implementando RAG local com recuperação de passagens e geração de sugestões.
"""

import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .anythingllm_client import AnythingLLMClient, RAGPassage, RAGResponse, Suggestion


@dataclass
class ObjectionEvent:
    """Evento de objeção detectada."""
    call_id: str
    category: str  # 'preco', 'timing', 'autoridade', 'necessidade'
    text: str
    context_snippet: str
    timestamp_ms: int


@dataclass
class RAGResult:
    """Resultado do RAG com sugestões."""
    call_id: str
    objection: ObjectionEvent
    suggestions: List[Suggestion]
    retrieved_passages: List[RAGPassage]
    latency_ms: float
    model_info: Dict[str, str]


class RAGWorker(QThread):
    """Worker thread para processamento RAG assíncrono."""
    
    rag_complete = pyqtSignal(object)  # RAGResult
    rag_error = pyqtSignal(str)        # error message
    
    def __init__(self, anythingllm_client: AnythingLLMClient):
        super().__init__()
        self.client = anythingllm_client
        self.objection_event: Optional[ObjectionEvent] = None
        self.passages: List[RAGPassage] = []
        self.stream_callback: Optional[callable] = None
    
    def process_objection(self, objection: ObjectionEvent, passages: List[RAGPassage], 
                         stream_callback: Optional[callable] = None):
        """Processar objeção em thread separada."""
        self.objection_event = objection
        self.passages = passages
        self.stream_callback = stream_callback
        self.start()
    
    def run(self):
        """Executar processamento RAG."""
        try:
            if not self.objection_event or not self.passages:
                self.rag_error.emit("Dados insuficientes para processamento RAG")
                return
            
            # Gerar sugestões usando AnythingLLM
            response = self.client.generate_objection_suggestions(
                objection=self.objection_event.text,
                passages=self.passages,
                stream_callback=self.stream_callback
            )
            
            # Criar resultado
            result = RAGResult(
                call_id=self.objection_event.call_id,
                objection=self.objection_event,
                suggestions=response.suggestions,
                retrieved_passages=response.retrieved,
                latency_ms=response.latency_ms,
                model_info=response.model_info
            )
            
            self.rag_complete.emit(result)
            
        except Exception as e:
            self.rag_error.emit(f"Erro no processamento RAG: {e}")


class RAGService(QObject):
    """Serviço RAG integrado com AnythingLLM."""
    
    # Sinais
    suggestions_ready = pyqtSignal(object)  # RAGResult
    rag_error = pyqtSignal(str)             # error message
    llm_status_changed = pyqtSignal(bool)   # available/not available
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cliente AnythingLLM
        self.anythingllm_client = AnythingLLMClient(
            base_url=getattr(config, 'anythingllm_url', 'http://127.0.0.1:3001'),
            api_key=getattr(config, 'anythingllm_api_key', 'local-dev'),
            timeout=getattr(config, 'anythingllm_timeout', 2.0)
        )
        
        # Worker thread
        self.rag_worker = RAGWorker(self.anythingllm_client)
        self.rag_worker.rag_complete.connect(self._on_rag_complete)
        self.rag_worker.rag_error.connect(self._on_rag_error)
        
        # Estado
        self.is_available = False
        self._check_availability()
        
        # Base de conhecimento (simulada para demo)
        self._init_knowledge_base()
    
    def _check_availability(self):
        """Verificar disponibilidade do AnythingLLM."""
        self.is_available = self.anythingllm_client.health_check()
        self.llm_status_changed.emit(self.is_available)
        
        if self.is_available:
            self.logger.info("✅ AnythingLLM disponível para RAG")
        else:
            self.logger.warning("⚠️ AnythingLLM não disponível - usando fallback")
    
    def _init_knowledge_base(self):
        """Inicializar base de conhecimento (simulada)."""
        # Em produção, isso viria de um banco de dados ou arquivos
        self.knowledge_base = [
            {
                "id": "preco_001",
                "title": "Estratégias de Preço",
                "content": "Quando o cliente menciona que o preço está alto, foque no valor percebido. Apresente o ROI e os benefícios de longo prazo. Compare com alternativas mais caras no mercado.",
                "category": "preco"
            },
            {
                "id": "preco_002", 
                "title": "Flexibilidade de Pagamento",
                "content": "Ofereça opções de pagamento flexíveis: parcelamento, desconto por pagamento à vista, ou planos de assinatura. Mostre como isso se adapta ao orçamento do cliente.",
                "category": "preco"
            },
            {
                "id": "timing_001",
                "title": "Urgência e Timing",
                "content": "Crie senso de urgência mostrando oportunidades limitadas, promoções por tempo determinado, ou riscos de perder benefícios. Use dados de mercado para justificar.",
                "category": "timing"
            },
            {
                "id": "autoridade_001",
                "title": "Tomada de Decisão",
                "content": "Identifique quem realmente toma a decisão. Pergunte sobre o processo de aprovação e ofereça-se para falar com os stakeholders. Prepare materiais para diferentes níveis.",
                "category": "autoridade"
            },
            {
                "id": "necessidade_001",
                "title": "Descoberta de Necessidades",
                "content": "Use perguntas abertas para descobrir necessidades não atendidas. Relacione sua solução aos problemas específicos do cliente. Mostre casos de sucesso similares.",
                "category": "necessidade"
            },
            {
                "id": "geral_001",
                "title": "Técnica de Espelho",
                "content": "Repita a objeção do cliente para confirmar entendimento. Isso demonstra empatia e pode revelar informações adicionais sobre a preocupação real.",
                "category": "geral"
            }
        ]
    
    def retrieve_passages(self, objection_text: str, category: str, top_k: int = 3) -> List[RAGPassage]:
        """
        Recuperar passagens relevantes da base de conhecimento.
        
        Args:
            objection_text: Texto da objeção
            category: Categoria da objeção
            top_k: Número de passagens a retornar
            
        Returns:
            Lista de passagens ordenadas por relevância
        """
        # Simulação de busca semântica
        # Em produção, isso seria feito com FAISS, sqlite-vss, ou similar
        
        relevant_passages = []
        
        # Buscar por categoria
        category_matches = [p for p in self.knowledge_base if p['category'] == category]
        
        # Buscar por palavras-chave no texto
        keywords = objection_text.lower().split()
        scored_passages = []
        
        for passage in self.knowledge_base:
            score = 0.0
            
            # Score por categoria
            if passage['category'] == category:
                score += 0.5
            
            # Score por palavras-chave
            content_lower = passage['content'].lower()
            for keyword in keywords:
                if keyword in content_lower:
                    score += 0.3
            
            # Score por relevância geral
            if any(word in content_lower for word in ['objeção', 'cliente', 'venda', 'negociação']):
                score += 0.2
            
            if score > 0:
                scored_passages.append((passage, score))
        
        # Ordenar por score e pegar top-k
        scored_passages.sort(key=lambda x: x[1], reverse=True)
        
        for passage, score in scored_passages[:top_k]:
            relevant_passages.append(RAGPassage(
                id=passage['id'],
                title=passage['title'],
                snippet=passage['content'],
                score=score
            ))
        
        return relevant_passages
    
    def process_objection(
        self, 
        objection_event: ObjectionEvent,
        stream_callback: Optional[callable] = None
    ):
        """
        Processar objeção detectada e gerar sugestões.
        
        Args:
            objection_event: Evento de objeção
            stream_callback: Callback para streaming de texto
        """
        try:
            # 1. Recuperar passagens relevantes
            passages = self.retrieve_passages(
                objection_event.text,
                objection_event.category,
                top_k=3
            )
            
            if not passages:
                self.logger.warning("Nenhuma passagem relevante encontrada")
                # Criar resposta de fallback
                fallback_result = RAGResult(
                    call_id=objection_event.call_id,
                    objection=objection_event,
                    suggestions=[
                        Suggestion(
                            text="Não encontramos informações específicas para esta objeção. Considere perguntar mais sobre as preocupações do cliente.",
                            score=0.5,
                            sources=[]
                        )
                    ],
                    retrieved_passages=[],
                    latency_ms=0.0,
                    model_info={"provider": "fallback", "model": "no-rag", "temperature": 0.0}
                )
                self.suggestions_ready.emit(fallback_result)
                return
            
            # 2. Processar em thread separada
            self.rag_worker.process_objection(objection_event, passages, stream_callback)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar objeção: {e}")
            self.rag_error.emit(f"Erro no processamento: {e}")
    
    def _on_rag_complete(self, result: RAGResult):
        """Callback quando RAG é completado."""
        self.logger.info(f"✅ RAG completado em {result.latency_ms:.0f}ms")
        self.suggestions_ready.emit(result)
    
    def _on_rag_error(self, error: str):
        """Callback quando RAG falha."""
        self.logger.error(f"❌ Erro no RAG: {error}")
        self.rag_error.emit(error)
    
    def generate_session_summary(
        self, 
        session_data: Dict[str, Any],
        stream_callback: Optional[callable] = None
    ) -> str:
        """
        Gerar resumo da sessão usando AnythingLLM.
        
        Args:
            session_data: Dados da sessão
            stream_callback: Callback para streaming
            
        Returns:
            Resumo estruturado
        """
        if not self.is_available:
            return "AnythingLLM não disponível para geração de resumo."
        
        try:
            return self.anythingllm_client.generate_session_summary(
                session_data, stream_callback
            )
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            return "Erro ao gerar resumo da sessão."
    
    def health_check(self) -> bool:
        """Verificar saúde do serviço RAG."""
        return self.is_available
    
    def cleanup(self):
        """Limpar recursos do serviço."""
        if self.rag_worker.isRunning():
            self.rag_worker.quit()
            self.rag_worker.wait() 
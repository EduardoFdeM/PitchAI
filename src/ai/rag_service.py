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
        
        # Base de conhecimento real com cache
        self._init_knowledge_base()
        self._init_cache()
    
    def _check_availability(self):
        """Verificar disponibilidade do AnythingLLM."""
        self.is_available = self.anythingllm_client.health_check()
        self.llm_status_changed.emit(self.is_available)
        
        if self.is_available:
            self.logger.info("✅ AnythingLLM disponível para RAG")
        else:
            self.logger.warning("⚠️ AnythingLLM não disponível - usando fallback")
    
    def _init_knowledge_base(self):
        """Inicializar base de conhecimento real."""
        try:
            # Tentar carregar de arquivo JSON
            knowledge_file = self.config.app_dir / "data" / "knowledge_base.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                self.logger.info(f"✅ Base de conhecimento carregada: {len(self.knowledge_base)} itens")
            else:
                # Fallback para base simulada se arquivo não existir
                self._create_default_knowledge_base()
                self._save_knowledge_base()
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar base de conhecimento: {e}")
            self._create_default_knowledge_base()
    
    def _create_default_knowledge_base(self):
        """Criar base de conhecimento padrão."""
        self.knowledge_base = [
            {
                "id": "preco_001",
                "title": "Estratégias de Preço",
                "content": "Quando o cliente menciona que o preço está alto, foque no valor percebido. Apresente o ROI e os benefícios de longo prazo. Compare com alternativas mais caras no mercado.",
                "category": "preco",
                "keywords": ["preço", "custo", "valor", "orçamento", "caro", "investimento"],
                "priority": 1.0
            },
            {
                "id": "preco_002", 
                "title": "Flexibilidade de Pagamento",
                "content": "Ofereça opções de pagamento flexíveis: parcelamento, desconto por pagamento à vista, ou planos de assinatura. Mostre como isso se adapta ao orçamento do cliente.",
                "category": "preco",
                "keywords": ["pagamento", "parcelamento", "desconto", "flexível", "plano"],
                "priority": 0.9
            },
            {
                "id": "timing_001",
                "title": "Urgência e Timing",
                "content": "Crie senso de urgência mostrando oportunidades limitadas, promoções por tempo determinado, ou riscos de perder benefícios. Use dados de mercado para justificar.",
                "category": "timing",
                "keywords": ["timing", "urgência", "prazo", "tempo", "agora", "depois"],
                "priority": 0.8
            },
            {
                "id": "autoridade_001",
                "title": "Tomada de Decisão",
                "content": "Identifique quem realmente toma a decisão. Pergunte sobre o processo de aprovação e ofereça-se para falar com os stakeholders. Prepare materiais para diferentes níveis.",
                "category": "autoridade",
                "keywords": ["autoridade", "decisão", "chefe", "aprovador", "stakeholder"],
                "priority": 0.9
            },
            {
                "id": "necessidade_001",
                "title": "Descoberta de Necessidades",
                "content": "Use perguntas abertas para descobrir necessidades não atendidas. Relacione sua solução aos problemas específicos do cliente. Mostre casos de sucesso similares.",
                "category": "necessidade",
                "keywords": ["necessidade", "problema", "dor", "solução", "benefício"],
                "priority": 0.8
            },
            {
                "id": "geral_001",
                "title": "Técnica de Espelho",
                "content": "Repita a objeção do cliente para confirmar entendimento. Isso demonstra empatia e pode revelar informações adicionais sobre a preocupação real.",
                "category": "geral",
                "keywords": ["empatia", "entendimento", "confirmação", "espelho"],
                "priority": 0.7
            }
        ]
    
    def _save_knowledge_base(self):
        """Salvar base de conhecimento em arquivo."""
        try:
            knowledge_file = self.config.app_dir / "data" / "knowledge_base.json"
            knowledge_file.parent.mkdir(exist_ok=True)
            
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Base de conhecimento salva: {knowledge_file}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar base de conhecimento: {e}")
    
    def _init_cache(self):
        """Inicializar cache para melhorar performance."""
        self.cache = {}
        self.cache_ttl = 300  # 5 minutos
        self.cache_stats = {"hits": 0, "misses": 0}
    
    @cache_result(ttl=300, priority=8, key_prefix="rag_passages")
    def retrieve_passages(self, objection_text: str, category: str, top_k: int = 3) -> List[RAGPassage]:
        """
        Recuperar passagens relevantes da base de conhecimento com cache e busca semântica melhorada.
        
        Args:
            objection_text: Texto da objeção
            category: Categoria da objeção
            top_k: Número de passagens a retornar
            
        Returns:
            Lista de passagens ordenadas por relevância
        """
        # Verificar cache primeiro
        cache_key = f"{objection_text.lower()}_{category}_{top_k}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.cache_stats["hits"] += 1
                return cache_entry["passages"]
        
        self.cache_stats["misses"] += 1
        
        # Busca semântica melhorada
        relevant_passages = []
        scored_passages = []
        
        # Normalizar texto da objeção
        objection_words = set(objection_text.lower().split())
        
        for passage in self.knowledge_base:
            score = 0.0
            
            # 1. Score por categoria (maior peso)
            if passage['category'] == category:
                score += 0.4
            
            # 2. Score por palavras-chave específicas
            if 'keywords' in passage:
                keyword_matches = objection_words.intersection(set(passage['keywords']))
                score += len(keyword_matches) * 0.3
            
            # 3. Score por matching de palavras no conteúdo
            content_words = set(passage['content'].lower().split())
            word_matches = objection_words.intersection(content_words)
            score += len(word_matches) * 0.2
            
            # 4. Score por prioridade do item
            if 'priority' in passage:
                score += passage['priority'] * 0.1
            
            # 5. Score por relevância semântica (palavras relacionadas)
            semantic_matches = self._calculate_semantic_similarity(objection_text, passage['content'])
            score += semantic_matches * 0.2
            
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
        
        # Armazenar no cache
        self.cache[cache_key] = {
            "passages": relevant_passages,
            "timestamp": time.time()
        }
        
        return relevant_passages
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calcular similaridade semântica entre dois textos."""
        try:
            # Implementação simples baseada em palavras relacionadas
            # Em produção, usar embeddings ou modelos de similaridade
            
            # Palavras relacionadas para vendas
            related_words = {
                "preço": ["custo", "valor", "orçamento", "investimento", "caro", "barato"],
                "timing": ["tempo", "prazo", "urgência", "agora", "depois", "esperar"],
                "autoridade": ["decisão", "chefe", "aprovador", "stakeholder", "responsável"],
                "necessidade": ["problema", "dor", "solução", "benefício", "resultado"],
                "cliente": ["comprador", "usuário", "consumidor", "prospect"],
                "venda": ["negociação", "proposta", "oferta", "fechamento"]
            }
            
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            # Calcular similaridade direta
            direct_similarity = len(words1.intersection(words2)) / max(len(words1), len(words2), 1)
            
            # Calcular similaridade por palavras relacionadas
            related_similarity = 0.0
            for word1 in words1:
                for category, related in related_words.items():
                    if word1 in related:
                        for word2 in words2:
                            if word2 in related:
                                related_similarity += 0.1
                                break
            
            return min(1.0, direct_similarity + related_similarity)
            
        except Exception as e:
            self.logger.warning(f"Erro no cálculo de similaridade: {e}")
            return 0.0
    
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
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl
        }
    
    def clear_cache(self):
        """Limpar cache."""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0}
        self.logger.info("✅ Cache limpo")
    
    def cleanup(self):
        """Limpar recursos do serviço."""
        if self.rag_worker.isRunning():
            self.rag_worker.quit()
            self.rag_worker.wait() 
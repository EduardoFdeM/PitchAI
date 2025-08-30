"""
AnythingLLM Client - Integração com LLM Local
============================================

Cliente para comunicação com AnythingLLM rodando localmente,
usando API OpenAI-compatível para geração de sugestões de objeções
e resumos pós-chamada.
"""

import json
import logging
import requests
import time
from typing import List, Dict, Optional, Generator, Any
from dataclasses import dataclass
from urllib.parse import urljoin

try:
    import sseclient
except ImportError:
    sseclient = None
    logging.warning("sseclient-py não instalado. Streaming não disponível.")


@dataclass
class RAGPassage:
    """Representa uma passagem recuperada do RAG."""
    id: str
    title: str
    snippet: str
    score: float = 0.0


@dataclass
class Suggestion:
    """Representa uma sugestão gerada pelo LLM."""
    text: str
    score: float
    sources: List[Dict[str, str]]


@dataclass
class RAGResponse:
    """Resposta completa do RAG."""
    suggestions: List[Suggestion]
    retrieved: List[RAGPassage]
    latency_ms: float
    model_info: Dict[str, str]


class AnythingLLMClient:
    """Cliente para comunicação com AnythingLLM local."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3001", 
                 api_key: str = "local-dev", timeout: float = 2.0):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Endpoints
        self.chat_endpoint = urljoin(self.base_url, "/v1/chat/completions")
        self.models_endpoint = urljoin(self.base_url, "/v1/models")
        
        # Configuração padrão
        self.default_model = "llama3:instruct"
        self.default_temperature = 0.3
        self.max_tokens = 256
        
        self._test_connection()
    
    def _test_connection(self):
        """Testar conexão com AnythingLLM."""
        try:
            response = requests.get(self.models_endpoint, timeout=5.0)
            if response.status_code == 200:
                models = response.json()
                if models.get('data'):
                    self.default_model = models['data'][0]['id']
                    self.logger.info(f"✅ AnythingLLM conectado. Modelo: {self.default_model}")
                else:
                    self.logger.warning("⚠️ Nenhum modelo encontrado no AnythingLLM")
            else:
                self.logger.error(f"❌ Erro ao conectar com AnythingLLM: {response.status_code}")
        except Exception as e:
            self.logger.error(f"❌ Não foi possível conectar com AnythingLLM: {e}")
    
    def _make_request(self, payload: Dict[str, Any], stream: bool = True) -> requests.Response:
        """Fazer requisição para AnythingLLM."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return requests.post(
            self.chat_endpoint,
            json=payload,
            headers=headers,
            timeout=self.timeout,
            stream=stream
        )
    
    def _parse_sse_event(self, event_data: str) -> Optional[str]:
        """Parsear evento SSE para extrair conteúdo."""
        if event_data == "[DONE]":
            return None
        
        try:
            data = json.loads(event_data)
            if 'choices' in data and len(data['choices']) > 0:
                delta = data['choices'][0].get('delta', {})
                return delta.get('content', '')
        except json.JSONDecodeError:
            pass
        
        return ''
    
    def generate_objection_suggestions(
        self, 
        objection: str, 
        passages: List[RAGPassage],
        temperature: Optional[float] = None,
        stream_callback: Optional[callable] = None
    ) -> RAGResponse:
        """
        Gerar sugestões para uma objeção usando RAG.
        
        Args:
            objection: Texto da objeção detectada
            passages: Lista de passagens recuperadas do RAG
            temperature: Temperatura para geração (0.0-1.0)
            stream_callback: Callback para streaming de texto
            
        Returns:
            RAGResponse com sugestões e metadados
        """
        start_time = time.time()
        
        # Preparar contexto das passagens
        context = "\n".join([
            f"[#{i+1}] {p.snippet}" 
            for i, p in enumerate(passages)
        ])
        
        # Prompt do sistema
        system_prompt = (
            "Você é um assistente de vendas especializado em lidar com objeções. "
            "Responda em português brasileiro com 1-3 opções curtas e consultivas. "
            "Use SOMENTE os trechos fornecidos como base, citando [#id]. "
            "Se faltar evidência, diga 'não encontrado' de forma honesta. "
            "Formato: bullet points concisos."
        )
        
        # Prompt do usuário
        user_prompt = f"Objeção: {objection}\n\nContexto:\n{context}\n\nResponda em bullet points."
        
        # Payload da requisição
        payload = {
            "model": self.default_model,
            "temperature": temperature or self.default_temperature,
            "stream": True,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        try:
            # Fazer requisição
            response = self._make_request(payload, stream=True)
            
            if response.status_code != 200:
                self.logger.error(f"❌ Erro na API: {response.status_code} - {response.text}")
                return self._create_fallback_response(passages, start_time)
            
            # Processar streaming
            full_text = ""
            if sseclient:
                client = sseclient.SSEClient(response)
                for event in client.events():
                    content = self._parse_sse_event(event.data)
                    if content is None:  # [DONE]
                        break
                    full_text += content
                    if stream_callback:
                        stream_callback(content)
            else:
                # Fallback sem streaming
                data = response.json()
                full_text = data['choices'][0]['message']['content']
            
            # Processar resposta
            suggestions = self._parse_suggestions(full_text, passages)
            latency = (time.time() - start_time) * 1000
            
            return RAGResponse(
                suggestions=suggestions,
                retrieved=passages,
                latency_ms=latency,
                model_info={
                    "provider": "AnythingLLM",
                    "model": self.default_model,
                    "temperature": temperature or self.default_temperature
                }
            )
            
        except requests.exceptions.Timeout:
            self.logger.warning("⏰ Timeout na geração de sugestões")
            return self._create_fallback_response(passages, start_time)
            
        except Exception as e:
            self.logger.error(f"❌ Erro na geração: {e}")
            return self._create_fallback_response(passages, start_time)
    
    def _parse_suggestions(self, text: str, passages: List[RAGPassage]) -> List[Suggestion]:
        """Parsear texto gerado em sugestões estruturadas."""
        suggestions = []
        
        # Dividir por bullet points
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Remover marcadores comuns
            clean_line = line.lstrip('•-*→').strip()
            if not clean_line:
                continue
            
            # Extrair fontes citadas
            sources = []
            for i, passage in enumerate(passages):
                if f"[#{i+1}]" in clean_line:
                    sources.append({
                        "id": passage.id,
                        "title": passage.title
                    })
            
            # Calcular score baseado na presença de fontes
            score = min(0.9, 0.5 + len(sources) * 0.2)
            
            suggestions.append(Suggestion(
                text=clean_line,
                score=score,
                sources=sources
            ))
        
        # Se não conseguiu parsear, criar uma sugestão genérica
        if not suggestions and text.strip():
            suggestions.append(Suggestion(
                text=text.strip(),
                score=0.5,
                sources=[]
            ))
        
        return suggestions[:3]  # Máximo 3 sugestões
    
    def _create_fallback_response(self, passages: List[RAGPassage], start_time: float) -> RAGResponse:
        """Criar resposta de fallback usando apenas os snippets."""
        latency = (time.time() - start_time) * 1000
        
        # Criar sugestões baseadas nos snippets
        suggestions = []
        for i, passage in enumerate(passages[:3]):
            suggestions.append(Suggestion(
                text=f"Trecho relevante: {passage.snippet[:100]}...",
                score=0.7 - i * 0.1,
                sources=[{"id": passage.id, "title": passage.title}]
            ))
        
        return RAGResponse(
            suggestions=suggestions,
            retrieved=passages,
            latency_ms=latency,
            model_info={
                "provider": "AnythingLLM (fallback)",
                "model": "snippets-only",
                "temperature": 0.0
            }
        )
    
    def generate_session_summary(
        self, 
        session_data: Dict[str, Any],
        stream_callback: Optional[callable] = None
    ) -> str:
        """
        Gerar resumo da sessão usando AnythingLLM.
        
        Args:
            session_data: Dados da sessão (transcrições, objeções, métricas)
            stream_callback: Callback para streaming
            
        Returns:
            Resumo estruturado da sessão
        """
        # Preparar contexto da sessão
        context = self._prepare_session_context(session_data)
        
        system_prompt = (
            "Você é um assistente especializado em análise de vendas. "
            "Estruture o resumo da sessão em: "
            "• Pontos Principais "
            "• Objeções Identificadas "
            "• Próximos Passos "
            "• KPIs Relevantes "
            "Seja conciso e objetivo."
        )
        
        user_prompt = f"Analise esta sessão de vendas:\n\n{context}\n\nGere um resumo estruturado."
        
        payload = {
            "model": self.default_model,
            "temperature": 0.2,
            "stream": True,
            "max_tokens": 512,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        try:
            response = self._make_request(payload, stream=True)
            
            if response.status_code != 200:
                return "Erro ao gerar resumo da sessão."
            
            full_text = ""
            if sseclient:
                client = sseclient.SSEClient(response)
                for event in client.events():
                    content = self._parse_sse_event(event.data)
                    if content is None:
                        break
                    full_text += content
                    if stream_callback:
                        stream_callback(content)
            else:
                data = response.json()
                full_text = data['choices'][0]['message']['content']
            
            return full_text.strip()
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar resumo: {e}")
            return "Não foi possível gerar resumo da sessão."
    
    def _prepare_session_context(self, session_data: Dict[str, Any]) -> str:
        """Preparar contexto da sessão para o LLM."""
        context_parts = []
        
        # Transcrições
        if 'transcriptions' in session_data:
            context_parts.append("TRANSCRIÇÕES:")
            for trans in session_data['transcriptions']:
                context_parts.append(f"- {trans['speaker']}: {trans['text']}")
        
        # Objeções
        if 'objections' in session_data:
            context_parts.append("\nOBJEÇÕES DETECTADAS:")
            for obj in session_data['objections']:
                context_parts.append(f"- {obj['category']}: {obj['text']}")
        
        # Métricas
        if 'metrics' in session_data:
            context_parts.append("\nMÉTRICAS:")
            for key, value in session_data['metrics'].items():
                context_parts.append(f"- {key}: {value}")
        
        return "\n".join(context_parts)
    
    def health_check(self) -> bool:
        """Verificar se o AnythingLLM está disponível."""
        try:
            response = requests.get(self.models_endpoint, timeout=2.0)
            return response.status_code == 200
        except:
            return False 
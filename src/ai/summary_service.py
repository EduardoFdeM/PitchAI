"""
Post-Call Summary Service - Feature 5
===================================

Serviço para gerar resumos executivos pós-chamada usando AnythingLLM.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .anythingllm_client import AnythingLLMClient


@dataclass
class CallSummary:
    """Resumo de uma chamada."""
    call_id: str
    key_points: List[str]
    objections: List[Dict[str, Any]]
    next_steps: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    generated_at: float


class SummaryWorker(QThread):
    """Worker thread para geração de resumo assíncrono."""
    
    summary_ready = pyqtSignal(object)  # CallSummary
    summary_error = pyqtSignal(str)     # error message
    
    def __init__(self, anythingllm_client: AnythingLLMClient):
        super().__init__()
        self.client = anythingllm_client
        self.call_data: Optional[Dict[str, Any]] = None
    
    def generate_summary(self, call_data: Dict[str, Any]):
        """Gerar resumo em thread separada."""
        self.call_data = call_data
        self.start()
    
    def run(self):
        """Executar geração de resumo."""
        try:
            if not self.call_data:
                self.summary_error.emit("Dados da chamada não fornecidos")
                return
            
            # Preparar dados para o LLM
            transcript = self.call_data.get('transcript', '')
            sentiment_data = self.call_data.get('sentiment', [])
            objections = self.call_data.get('objections', [])
            duration = self.call_data.get('duration', 0)
            
            # Criar prompt estruturado
            system_prompt = """
            Você é um assistente especializado em criar resumos executivos de chamadas de vendas.
            
            Crie um resumo estruturado com:
            1. Pontos principais (3-5 bullets)
            2. Objeções tratadas (tipo e como foi respondida)
            3. Próximos passos (ações com prazo e responsável)
            4. Métricas de performance
            
            Responda em formato JSON:
            {
                "key_points": ["ponto 1", "ponto 2"],
                "objections": [{"type": "preco", "handled": true, "note": "ROI apresentado"}],
                "next_steps": [{"desc": "Enviar proposta", "due": "2025-01-17", "owner": "vendedor"}],
                "metrics": {"talk_time_vendor_pct": 0.45, "sentiment_avg": 0.78, "objections_resolved": 3}
            }
            """
            
            user_prompt = f"""
            Dados da chamada:
            - Duração: {duration} segundos
            - Transcrição: {transcript[:2000]}...
            - Análise de sentimento: {sentiment_data}
            - Objeções detectadas: {objections}
            
            Gere o resumo executivo:
            """
            
            # Configurar payload
            payload = {
                "model": self.client.default_model,
                "temperature": 0.3,
                "stream": False,
                "max_tokens": 1000,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            # Fazer requisição
            response = self.client._make_request(payload, stream=False)
            
            if response.status_code != 200:
                self.summary_error.emit(f"Erro na API: {response.status_code}")
                return
            
            # Processar resposta
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Parsear JSON
            try:
                import json
                summary_data = json.loads(content)
                
                # Criar objeto CallSummary
                summary = CallSummary(
                    call_id=self.call_data['call_id'],
                    key_points=summary_data.get('key_points', []),
                    objections=summary_data.get('objections', []),
                    next_steps=summary_data.get('next_steps', []),
                    metrics=summary_data.get('metrics', {}),
                    generated_at=time.time()
                )
                
                self.summary_ready.emit(summary)
                
            except json.JSONDecodeError:
                self.summary_error.emit("Erro ao parsear resposta do LLM")
                
        except Exception as e:
            self.summary_error.emit(f"Erro na geração de resumo: {e}")


class PostCallSummaryService(QObject):
    """Serviço de resumo pós-chamada."""
    
    # Sinais
    summary_ready = pyqtSignal(object)  # CallSummary
    summary_error = pyqtSignal(str)     # error message
    
    def __init__(self, config, anythingllm_client: AnythingLLMClient = None):
        super().__init__()
        self.config = config
        self.anythingllm_client = anythingllm_client
        self.logger = logging.getLogger(__name__)
        
        # Worker para geração assíncrona
        self.summary_worker = SummaryWorker(anythingllm_client) if anythingllm_client else None
        if self.summary_worker:
            self.summary_worker.summary_ready.connect(self.summary_ready)
            self.summary_worker.summary_error.connect(self.summary_error)
    
    def generate_summary(self, call_id: str, call_data: Dict[str, Any]):
        """Gerar resumo pós-chamada."""
        try:
            if not self.anythingllm_client:
                self.logger.warning("AnythingLLM não disponível, usando resumo básico")
                summary = self._generate_basic_summary(call_id, call_data)
                self.summary_ready.emit(summary)
                return
            
            # Adicionar call_id aos dados
            call_data['call_id'] = call_id
            
            # Gerar resumo via AnythingLLM
            if self.summary_worker:
                self.summary_worker.generate_summary(call_data)
            else:
                self.summary_error.emit("Worker de resumo não disponível")
                
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            self.summary_error.emit(str(e))
    
    def _generate_basic_summary(self, call_id: str, call_data: Dict[str, Any]) -> CallSummary:
        """Gerar resumo básico sem LLM."""
        transcript = call_data.get('transcript', '')
        duration = call_data.get('duration', 0)
        
        # Extrair pontos principais simples
        key_points = []
        if "preço" in transcript.lower():
            key_points.append("Discussão sobre preços")
        if "contrato" in transcript.lower():
            key_points.append("Negociação de contrato")
        if "prazo" in transcript.lower():
            key_points.append("Definição de prazos")
        
        if not key_points:
            key_points = ["Chamada realizada com sucesso"]
        
        # Métricas básicas
        metrics = {
            "duration_sec": duration,
            "talk_time_vendor_pct": 0.5,
            "sentiment_avg": 0.0,
            "objections_total": 0,
            "objections_resolved": 0,
            "buying_signals": 0
        }
        
        return CallSummary(
            call_id=call_id,
            key_points=key_points,
            objections=[],
            next_steps=[{"desc": "Follow-up", "due": None, "owner": "vendedor"}],
            metrics=metrics,
            generated_at=time.time()
        )
    
    def export_summary(self, summary: CallSummary, format: str = 'json') -> str:
        """Exportar resumo em diferentes formatos."""
        try:
            if format == 'json':
                import json
                return json.dumps(summary.__dict__, indent=2, ensure_ascii=False)
            
            elif format == 'markdown':
                md = f"# Resumo da Chamada {summary.call_id}\n\n"
                md += f"**Data:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(summary.generated_at))}\n\n"
                
                md += "## Pontos Principais\n"
                for point in summary.key_points:
                    md += f"- {point}\n"
                md += "\n"
                
                if summary.objections:
                    md += "## Objeções Tratadas\n"
                    for obj in summary.objections:
                        md += f"- **{obj.get('type', 'N/A')}**: {obj.get('note', 'N/A')}\n"
                    md += "\n"
                
                md += "## Próximos Passos\n"
                for step in summary.next_steps:
                    due = step.get('due', 'Não definido')
                    owner = step.get('owner', 'Vendedor')
                    md += f"- {step['desc']} (Prazo: {due}, Responsável: {owner})\n"
                md += "\n"
                
                md += "## Métricas\n"
                for key, value in summary.metrics.items():
                    md += f"- **{key}**: {value}\n"
                
                return md
            
            else:
                raise ValueError(f"Formato não suportado: {format}")
                
        except Exception as e:
            self.logger.error(f"Erro ao exportar resumo: {e}")
            return f"Erro na exportação: {e}"

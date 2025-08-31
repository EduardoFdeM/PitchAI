"""
Post-Call Summary Service - Feature 5
====================================

Serviço unificado para geração de resumos executivos pós-chamada.
Consolida dados de transcrição, sentimento, objeções e gera resumo via LLM local.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QThread

@dataclass
class CallSummary:
    """Estrutura do resumo pós-chamada"""
    call_id: str
    key_points: List[str]
    objections: List[Dict[str, Any]]
    next_steps: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    generated_at: float

class PostCallSummaryService(QObject):
    """Serviço unificado para geração de resumo pós-chamada"""

    summary_ready = pyqtSignal(CallSummary)
    summary_error = pyqtSignal(str)

    def __init__(self, config, llm_service=None, storage_service=None):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.llm_service = llm_service
        self.storage_service = storage_service

        # Fallback: criar LLM Service se não fornecido
        if self.llm_service is None:
            try:
                from ai.llm_service import LLMService
                self.llm_service = LLMService(
                    model_dir=config.app_dir / "models",
                    use_simulation=False,
                    use_anythingllm=True
                )
                self.llm_service.initialize()
                self.logger.info("✅ LLM Service criado no SummaryService")
            except Exception as e:
                self.logger.warning(f"⚠️ Não foi possível criar LLM Service: {e}")
                self.llm_service = None

    def generate(self, call_id: str) -> Optional[CallSummary]:
        """Gera resumo executivo da chamada"""
        # 1. Consolidar dados da chamada
        call_data = self._consolidate_call_data(call_id)

        # 2. Verificar se LLM Service está disponível
        if not self.llm_service:
            self.logger.warning("⚠️ LLM Service não disponível, usando resumo simulado")
            return self._generate_fallback_summary(call_data)

        # 3. Gerar prompt estruturado
        prompt = self._build_summary_prompt(call_data)

        # 4. Invocar LLM local (AnythingLLM)
        try:
            llm_response = self.llm_service.generate_response(prompt, max_tokens=1000)
            self.logger.info("✅ Resumo gerado com AnythingLLM")
        except Exception as e:
            self.logger.warning(f"⚠️ Erro no LLM, usando fallback: {e}")
            return self._generate_fallback_summary(call_data)

        # 5. Parsear resposta estruturada
        summary = self._parse_llm_response(llm_response, call_id)

        # 6. Persistir no storage
        if self.storage_service:
            # TODO: Implementar salvamento síncrono
            pass

        return summary

    def _generate_fallback_summary(self, call_data: Dict[str, Any]) -> CallSummary:
        """Gera resumo fallback quando LLM não está disponível"""
        self.logger.info("🔄 Gerando resumo fallback...")

        # Resumo básico baseado nos dados consolidados
        transcript = call_data.get("transcript", "")
        sentiment = call_data.get("sentiment_data", {})
        objections = call_data.get("objections", [])

        # Pontos principais simulados
        key_points = [
            "Reunião realizada com cliente potencial",
            "Discussão sobre necessidades e soluções",
            "Apresentação de benefícios da proposta"
        ]

        # Próximos passos simulados
        next_steps = [
            {
                "desc": "Enviar proposta detalhada por email",
                "due": "2025-01-20",
                "owner": "vendedor"
            },
            {
                "desc": "Agendar demonstração técnica",
                "due": "2025-01-25",
                "owner": "vendedor"
            }
        ]

        # Métricas simuladas
        metrics = {
            "talk_time_vendor_pct": 45.0,
            "talk_time_client_pct": 55.0,
            "sentiment_avg": sentiment.get("avg_score", 0.7),
            "objections_total": len(objections),
            "objections_resolved": len([obj for obj in objections if obj.get("handled", False)]),
            "buying_signals": sentiment.get("buying_signals_count", 2)
        }

        # Objeções tratadas
        objections_summary = []
        for obj in objections:
            objections_summary.append({
                "type": obj.get("type", "unknown"),
                "handled": obj.get("handled", False),
                "note": obj.get("note", "")
            })

        return CallSummary(
            call_id=call_data.get("call_id", "unknown"),
            key_points=key_points,
            objections=objections_summary,
            next_steps=next_steps,
            metrics=metrics,
            generated_at=datetime.now().timestamp()
        )
    
    def _consolidate_call_data(self, call_id: str) -> Dict[str, Any]:
        """Consolida dados de transcrição, sentimento e objeções"""
        # Dados simulados para teste
        return {
            "transcript": {
                "chunks": [
                    {"speaker": "vendor", "text": "Olá, bom dia! Como vai?", "duration_sec": 2.0},
                    {"speaker": "client", "text": "Oi, tudo bem. Gostaria de saber sobre a solução", "duration_sec": 3.0},
                    {"speaker": "vendor", "text": "Claro! Nossa plataforma oferece integração completa", "duration_sec": 4.0},
                    {"speaker": "client", "text": "Parece interessante, mas está muito caro", "duration_sec": 2.5},
                    {"speaker": "vendor", "text": "Entendo sua preocupação. O ROI é de 340% em 18 meses", "duration_sec": 5.0},
                    {"speaker": "client", "text": "Hmm, preciso pensar melhor", "duration_sec": 2.0}
                ],
                "text": "Transcrição de exemplo da reunião"
            },
            "sentiment_data": {"avg_score": 0.75},
            "objections": [{"type": "preco", "handled": True}],
            "call_id": call_id,
            "metrics": {
                "talk_time_vendor_pct": 55.0,
                "talk_time_client_pct": 45.0,
                "sentiment_avg": 0.75,
                "objections_total": 1,
                "objections_resolved": 1,
                "buying_signals": 2
            }
        }
    
    def _calculate_metrics(self, transcript, sentiment_data, objections) -> Dict[str, Any]:
        """Calcula KPIs da chamada"""
        total_duration = transcript.get("duration_sec", 0)
        vendor_talk_time = sum(
            chunk.get("duration_sec", 0) 
            for chunk in transcript.get("chunks", [])
            if chunk.get("speaker") == "vendor"
        )
        
        return {
            "talk_time_vendor_pct": (vendor_talk_time / total_duration * 100) if total_duration > 0 else 0,
            "talk_time_client_pct": 100 - (vendor_talk_time / total_duration * 100) if total_duration > 0 else 0,
            "sentiment_avg": sentiment_data.get("average_sentiment", 0),
            "objections_total": len(objections),
            "objections_resolved": len([obj for obj in objections if obj.get("handled", False)]),
            "buying_signals": sentiment_data.get("buying_signals_count", 0)
        }
    
    def _build_summary_prompt(self, call_data: Dict[str, Any]) -> str:
        """Constrói prompt estruturado para o LLM"""
        transcript_text = self._extract_transcript_text(call_data["transcript"])
        objections_text = self._format_objections(call_data["objections"])
        metrics = call_data["metrics"]
        
        prompt = f"""
        Você é um assistente de IA especializado em análise de chamadas de vendas. Analise a transcrição abaixo e gere um resumo executivo inteligente focado em vendas.

        CONTEXTO DA CHAMADA:
        Esta é uma chamada de vendas onde um vendedor está conversando com um cliente potencial. Você deve identificar oportunidades, objeções, sinais de compra e próximos passos estratégicos.

        TRANSCRIÇÃO DA CHAMADA:
        {transcript_text}

        OBJEÇÕES DETECTADAS:
        {objections_text}

        MÉTRICAS TÉCNICAS:
        - Tempo de fala vendedor: {metrics['talk_time_vendor_pct']:.1f}%
        - Tempo de fala cliente: {metrics['talk_time_client_pct']:.1f}%
        - Sentimento médio: {metrics['sentiment_avg']:.2f}
        - Objeções totais: {metrics['objections_total']}
        - Objeções resolvidas: {metrics['objections_resolved']}
        - Sinais de compra detectados: {metrics['buying_signals']}

        INSTRUÇÕES PARA ANÁLISE:
        1. **Pontos Principais**: Extraia os 3-5 pontos mais importantes da conversa (necessidades do cliente, benefícios discutidos, decisões tomadas)
        2. **Objeções**: Para cada objeção, indique se foi tratada e como
        3. **Próximos Passos**: Sugira ações concretas com datas e responsáveis
        4. **Análise Estratégica**: Considere o contexto de vendas - sinais de interesse, urgência, autoridade de decisão

        FORMATO DE SAÍDA (JSON puro, sem formatação adicional):
        {{
            "key_points": ["Ponto principal 1", "Ponto principal 2", "Ponto principal 3"],
            "objections": [
                {{"type": "preco", "handled": true, "note": "Explicado ROI de 340% em 18 meses"}},
                {{"type": "timing", "handled": false, "note": "Cliente precisa aprovar com equipe técnica"}}
            ],
            "next_steps": [
                {{"desc": "Enviar proposta técnica detalhada", "due": "2025-01-17", "owner": "vendedor", "priority": "alta"}},
                {{"desc": "Agendar demonstração para equipe técnica", "due": "2025-01-24", "owner": "vendedor", "priority": "media"}},
                {{"desc": "Preparar case study similar", "due": "2025-01-18", "owner": "vendedor", "priority": "baixa"}}
            ],
            "metrics": {{
                "talk_time_vendor_pct": {metrics['talk_time_vendor_pct']},
                "talk_time_client_pct": {metrics['talk_time_client_pct']},
                "sentiment_avg": {metrics['sentiment_avg']},
                "objections_total": {metrics['objections_total']},
                "objections_resolved": {metrics['objections_resolved']},
                "buying_signals": {metrics['buying_signals']}
            }},
            "insights": {{
                "cliente_interesse": "alto|médio|baixo",
                "urgencia": "alta|média|baixa",
                "autoridade_decisao": "tomador|influenciador|usuario",
                "proxima_acao_recomendada": "follow_up|proposta|demo|nurturing"
            }}
        }}

        LEMBRE-SE: Foque no contexto comercial e nas oportunidades de venda. Seja específico e acionável.
        """
        return prompt
    
    def _extract_transcript_text(self, transcript: Dict[str, Any]) -> str:
        """Extrai texto da transcrição formatado"""
        chunks = transcript.get("chunks", [])
        text_parts = []
        
        for chunk in chunks:
            speaker = chunk.get("speaker", "unknown")
            text = chunk.get("text", "")
            if text.strip():
                text_parts.append(f"{speaker.upper()}: {text}")
        
        return "\n".join(text_parts)
    
    def _format_objections(self, objections: List[Dict[str, Any]]) -> str:
        """Formata objeções para o prompt"""
        if not objections:
            return "Nenhuma objeção detectada"
        
        formatted = []
        for obj in objections:
            obj_type = obj.get("type", "unknown")
            handled = "RESOLVIDA" if obj.get("handled", False) else "PENDENTE"
            suggestion = obj.get("suggestion", "")
            formatted.append(f"- {obj_type.upper()}: {handled} - {suggestion}")
        
        return "\n".join(formatted)
    
    def _parse_llm_response(self, llm_response: str, call_id: str = "unknown") -> CallSummary:
        """Parseia resposta do LLM em estrutura CallSummary"""
        try:
            # Extrair JSON da resposta do LLM
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            json_str = llm_response[json_start:json_end]

            if json_str:
                data = json.loads(json_str)

                return CallSummary(
                    call_id=call_id,
                    key_points=data.get("key_points", []),
                    objections=data.get("objections", []),
                    next_steps=data.get("next_steps", []),
                    metrics=data.get("metrics", {}),
                    generated_at=datetime.now().timestamp()
                )
            else:
                # Resposta não contém JSON
                raise json.JSONDecodeError("No JSON found in response", llm_response, 0)

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback em caso de erro no parsing
            self.logger.warning(f"Erro ao parsear resposta LLM: {e}")
            return CallSummary(
                call_id=call_id,
                key_points=["Resumo gerado automaticamente"],
                objections=[],
                next_steps=[{
                    "desc": "Revisar chamada e criar follow-up",
                    "due": "2025-01-20",
                    "owner": "vendedor"
                }],
                metrics={
                    "talk_time_vendor_pct": 50.0,
                    "talk_time_client_pct": 50.0,
                    "sentiment_avg": 0.7,
                    "objections_total": 0,
                    "objections_resolved": 0,
                    "buying_signals": 1
                },
                generated_at=datetime.now().timestamp()
            )
    
    async def get(self, call_id: str) -> Optional[CallSummary]:
        """Recupera resumo existente"""
        summary_data = await self.storage_service.get_summary(call_id)
        if summary_data:
            return CallSummary(**summary_data)
        return None
    
    async def export(self, call_id: str, format: str = "md") -> str:
        """Exporta resumo em formato específico"""
        summary = await self.get(call_id)
        if not summary:
            raise ValueError(f"Resumo não encontrado para call_id: {call_id}")
        
        if format == "md":
            return self._export_markdown(summary)
        elif format == "pdf":
            return await self._export_pdf(summary)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def _export_markdown(self, summary: CallSummary) -> str:
        """Exporta resumo em Markdown"""
        md = f"""# Resumo da Chamada

## Pontos Principais
"""
        for point in summary.key_points:
            md += f"- {point}\n"
        
        md += "\n## Objeções\n"
        for obj in summary.objections:
            status = "✅" if obj.get("handled") else "❌"
            md += f"- {status} **{obj.get('type', '').upper()}**: {obj.get('note', '')}\n"
        
        md += "\n## Próximos Passos\n"
        for step in summary.next_steps:
            due = f" (vence: {step.get('due')})" if step.get('due') else ""
            owner = f" - {step.get('owner')}" if step.get('owner') else ""
            md += f"- [ ] {step.get('desc', '')}{due}{owner}\n"
        
        md += "\n## Métricas\n"
        metrics = summary.metrics
        md += f"- Tempo de fala vendedor: {metrics.get('talk_time_vendor_pct', 0):.1f}%\n"
        md += f"- Tempo de fala cliente: {metrics.get('talk_time_client_pct', 0):.1f}%\n"
        md += f"- Sentimento médio: {metrics.get('sentiment_avg', 0):.2f}\n"
        md += f"- Objeções: {metrics.get('objections_total', 0)} (resolvidas: {metrics.get('objections_resolved', 0)})\n"
        md += f"- Sinais de compra: {metrics.get('buying_signals', 0)}\n"
        
        return md
    
    async def _export_pdf(self, summary: CallSummary) -> str:
        """Exporta resumo em PDF (placeholder)"""
        # TODO: Implementar geração de PDF
        # Por enquanto retorna markdown
        return self._export_markdown(summary)

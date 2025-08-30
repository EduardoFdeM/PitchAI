import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class CallSummary:
    """Estrutura do resumo pós-chamada"""
    key_points: List[str]
    objections: List[Dict[str, Any]]
    next_steps: List[Dict[str, Any]]
    metrics: Dict[str, Any]

class PostCallSummaryService:
    """Serviço para geração de resumo pós-chamada"""
    
    def __init__(self, llm_service, storage_service):
        self.llm_service = llm_service
        self.storage_service = storage_service
        
    async def generate(self, call_id: str) -> CallSummary:
        """Gera resumo executivo da chamada"""
        # 1. Consolidar dados da chamada
        call_data = await self._consolidate_call_data(call_id)
        
        # 2. Gerar prompt estruturado
        prompt = self._build_summary_prompt(call_data)
        
        # 3. Invocar LLM local
        llm_response = await self.llm_service.generate(prompt)
        
        # 4. Parsear resposta estruturada
        summary = self._parse_llm_response(llm_response)
        
        # 5. Persistir no storage
        await self.storage_service.save_summary(call_id, summary)
        
        return summary
    
    async def _consolidate_call_data(self, call_id: str) -> Dict[str, Any]:
        """Consolida dados de transcrição, sentimento e objeções"""
        # Buscar dados das features anteriores
        transcript = await self.storage_service.get_transcript(call_id)
        sentiment_data = await self.storage_service.get_sentiment_data(call_id)
        objections = await self.storage_service.get_objections(call_id)
        
        # Calcular métricas
        metrics = self._calculate_metrics(transcript, sentiment_data, objections)
        
        return {
            "transcript": transcript,
            "sentiment": sentiment_data,
            "objections": objections,
            "metrics": metrics
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
        Analise a seguinte chamada de vendas e gere um resumo executivo estruturado em JSON:

        TRANSCRIÇÃO:
        {transcript_text}

        OBJEÇÕES DETECTADAS:
        {objections_text}

        MÉTRICAS:
        - Tempo de fala vendedor: {metrics['talk_time_vendor_pct']:.1f}%
        - Tempo de fala cliente: {metrics['talk_time_client_pct']:.1f}%
        - Sentimento médio: {metrics['sentiment_avg']:.2f}
        - Objeções: {metrics['objections_total']} (resolvidas: {metrics['objections_resolved']})
        - Sinais de compra: {metrics['buying_signals']}

        Gere um JSON com a seguinte estrutura:
        {{
            "key_points": ["ponto 1", "ponto 2", "ponto 3"],
            "objections": [
                {{"type": "preco", "handled": true, "note": "ROI explicado"}},
                {{"type": "timing", "handled": false, "note": "Precisa follow-up"}}
            ],
            "next_steps": [
                {{"desc": "Enviar proposta técnica", "due": "2025-01-17", "owner": "vendedor"}},
                {{"desc": "Agendar demo", "due": "2025-01-24"}}
            ],
            "metrics": {{
                "talk_time_vendor_pct": {metrics['talk_time_vendor_pct']},
                "talk_time_client_pct": {metrics['talk_time_client_pct']},
                "sentiment_avg": {metrics['sentiment_avg']},
                "objections_total": {metrics['objections_total']},
                "objections_resolved": {metrics['objections_resolved']},
                "buying_signals": {metrics['buying_signals']}
            }}
        }}
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
    
    def _parse_llm_response(self, llm_response: str) -> CallSummary:
        """Parseia resposta do LLM em estrutura CallSummary"""
        try:
            # Extrair JSON da resposta do LLM
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            json_str = llm_response[json_start:json_end]
            
            data = json.loads(json_str)
            
            return CallSummary(
                key_points=data.get("key_points", []),
                objections=data.get("objections", []),
                next_steps=data.get("next_steps", []),
                metrics=data.get("metrics", {})
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback em caso de erro no parsing
            return CallSummary(
                key_points=["Erro ao processar resumo"],
                objections=[],
                next_steps=[],
                metrics={}
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

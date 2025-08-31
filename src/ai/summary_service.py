"""
Summary Service - PitchAI
=========================

Serviço para gerar resumos pós-chamada inteligentes com PDF.

Implementa Feature 5: Resumo Pós-Chamada Inteligente
- Consolida dados da chamada (transcrição, sentimento, objeções)
- Gera resumo estruturado via LLM local (NPU)
- Persiste no banco de dados
- Exportação em PDF profissional integrada
"""

import io
import time
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from data.models import CallData, CallSummary, CallMetrics, ObjectionEvent, NextStep, TranscriptChunk
from data.database import DatabaseManager

# PDF Generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class SummaryService:
    """Serviço para gerar resumos pós-chamada inteligentes."""
    
    def __init__(self, npu_manager, database: DatabaseManager):
        self.npu_manager = npu_manager
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.model = None
        
        if REPORTLAB_AVAILABLE:
            self._setup_pdf_styles()
            self.logger.info("✅ PDF generator integrado")
        else:
            self.logger.warning("⚠️ ReportLab não disponível")

    def _setup_pdf_styles(self):
        """Configura estilos para PDF."""
        self.styles = getSampleStyleSheet()
        
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1e293b'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=HexColor('#2563eb')
        ))

    def generate_summary(self, call_id: str) -> CallSummary:
        """Gera resumo estruturado pós-chamada."""
        self.logger.info(f"📄 Gerando resumo da chamada {call_id}...")
        start_time = time.time()
        
        call_data = self._consolidate_call_data(call_id)
        summary_json = self._generate_with_llm(call_data)
        summary = self._build_final_summary(summary_json, call_data)
        self._save_summary(call_id, summary, call_data.metrics)
        
        latency = time.time() - start_time
        self.logger.info(f"✅ Resumo gerado em {latency:.2f}s")
        return summary

    def _consolidate_call_data(self, call_id: str) -> CallData:
        """Consolida dados da chamada do banco."""
        transcript_rows = self.database.get_call_transcript(call_id)
        transcript = [
            TranscriptChunk(
                speaker=row['speaker'],
                ts_start_ms=row['ts_start_ms'],
                ts_end_ms=row['ts_end_ms'],
                text=row['text'],
                confidence=row['confidence']
            )
            for row in transcript_rows
        ]
        
        objection_rows = self.database.get_call_objections(call_id)
        objections = [
            ObjectionEvent(
                type=row['category'],
                ts_start_ms=row['ts_start_ms'],
                ts_end_ms=row['ts_end_ms'],
                handled=bool(row['handled']),
                note=row['suggestion_used']
            )
            for row in objection_rows
        ]
        
        metrics_data = self.database.get_call_metrics(call_id)
        vendor_pct = metrics_data.get('talk_time_vendor_pct') or 0.0
        metrics = CallMetrics(
            talk_time_vendor_pct=vendor_pct,
            talk_time_client_pct=1.0 - vendor_pct,
            sentiment_avg=metrics_data.get('sentiment_avg') or 0.0,
            objections_total=metrics_data.get('objections_count') or 0,
            objections_resolved=sum(1 for obj in objections if obj.handled),
            buying_signals=metrics_data.get('purchase_signals_count') or 0
        )
        
        return CallData(
            call_id=call_id,
            transcript=transcript,
            objections=objections,
            metrics=metrics,
            started_at=datetime.now(),
            ended_at=datetime.now()
        )

    def _generate_with_llm(self, call_data: CallData) -> Dict[str, Any]:
        """Gera resumo usando LLM (simulado)."""
        key_points = self._extract_key_points(call_data)
        next_steps = self._generate_next_steps(call_data)
        
        return {
            "key_points": key_points,
            "next_steps": next_steps
        }

    def _extract_key_points(self, call_data: CallData) -> List[str]:
        """Extrai pontos principais da transcrição."""
        key_points = []
        full_text = " ".join([chunk.text.lower() for chunk in call_data.transcript])
        
        if "integração" in full_text or "sistema" in full_text:
            key_points.append("Cliente interessado em integração com sistemas existentes")
        if "preço" in full_text or "custo" in full_text or "budget" in full_text:
            key_points.append("Discussão sobre investimento e orçamento")
        if "equipe" in full_text or "pessoas" in full_text:
            key_points.append("Definição do tamanho da equipe e usuários")
        if "prazo" in full_text or "timeline" in full_text:
            key_points.append("Alinhamento de cronograma e prazos")
        
        if len(key_points) < 2:
            key_points.extend([
                "Cliente demonstrou interesse na solução",
                "Necessário follow-up para próximos passos"
            ])
        
        return key_points[:5]

    def _generate_next_steps(self, call_data: CallData) -> List[Dict[str, str]]:
        """Gera próximos passos baseados no contexto."""
        next_steps = []
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        if any(obj.type == "preco" for obj in call_data.objections):
            next_steps.append({
                "desc": "Enviar proposta comercial detalhada com ROI",
                "due": tomorrow,
                "owner": "vendedor"
            })
        
        if any(obj.type == "integracao" for obj in call_data.objections):
            next_steps.append({
                "desc": "Agendar demo técnica com equipe de TI",
                "due": next_week,
                "owner": "vendedor"
            })
        
        next_steps.extend([
            {
                "desc": "Follow-up da reunião",
                "due": tomorrow,
                "owner": "vendedor"
            },
            {
                "desc": "Agendar próxima reunião",
                "due": next_week
            }
        ])
        
        return next_steps[:4]

    def _build_final_summary(self, summary_json: Dict[str, Any], call_data: CallData) -> CallSummary:
        """Constrói resumo final estruturado."""
        next_steps = [
            NextStep(
                desc=step["desc"],
                due=step.get("due"),
                owner=step.get("owner", "vendedor")
            )
            for step in summary_json.get("next_steps", [])
        ]
        
        return CallSummary(
            key_points=summary_json.get("key_points", []),
            objections=call_data.objections,
            next_steps=next_steps,
            metrics=call_data.metrics
        )

    def _save_summary(self, call_id: str, summary: CallSummary, metrics: CallMetrics):
        """Salva resumo no banco de dados."""
        summary_dict = {
            "key_points": summary.key_points,
            "objections": [
                {"type": obj.type, "handled": obj.handled, "note": obj.note}
                for obj in summary.objections
            ],
            "next_steps": [
                {"desc": step.desc, "due": step.due, "owner": step.owner}
                for step in summary.next_steps
            ],
            "metrics": {
                "talk_time_vendor_pct": metrics.talk_time_vendor_pct,
                "talk_time_client_pct": metrics.talk_time_client_pct,
                "sentiment_avg": metrics.sentiment_avg,
                "objections_total": metrics.objections_total,
                "objections_resolved": metrics.objections_resolved,
                "buying_signals": metrics.buying_signals
            }
        }
        
        self.database.finalize_call(call_id, summary_dict["metrics"], summary_dict)
        self.logger.info(f"💾 Resumo salvo no banco: {call_id}")

    def get_summary(self, call_id: str) -> Optional[CallSummary]:
        """Recupera resumo existente do banco."""
        summary_data = self.database.get_call_summary(call_id)
        if not summary_data:
            return None
        
        objections = [
            ObjectionEvent(
                type=obj["type"],
                ts_start_ms=0,
                handled=obj["handled"],
                note=obj.get("note")
            )
            for obj in summary_data.get("objections", [])
        ]
        
        next_steps = [
            NextStep(
                desc=step["desc"],
                due=step.get("due"),
                owner=step.get("owner", "vendedor")
            )
            for step in summary_data.get("next_steps", [])
        ]
        
        metrics_data = summary_data.get("metrics", {})
        metrics = CallMetrics(
            talk_time_vendor_pct=metrics_data.get("talk_time_vendor_pct", 0.0),
            talk_time_client_pct=metrics_data.get("talk_time_client_pct", 0.0),
            sentiment_avg=metrics_data.get("sentiment_avg", 0.0),
            objections_total=metrics_data.get("objections_total", 0),
            objections_resolved=metrics_data.get("objections_resolved", 0),
            buying_signals=metrics_data.get("buying_signals", 0)
        )
        
        return CallSummary(
            key_points=summary_data.get("key_points", []),
            objections=objections,
            next_steps=next_steps,
            metrics=metrics
        )

    def export_summary(self, call_id: str, format: str = "json") -> str:
        """Exporta resumo em formato específico."""
        summary = self.get_summary(call_id)
        if not summary:
            raise ValueError(f"Resumo não encontrado para chamada {call_id}")
        
        if format == "json":
            return self._export_json(summary)
        elif format == "md":
            return self._export_markdown(summary, call_id)
        elif format == "pdf":
            return self._export_pdf(summary, call_id)
        else:
            raise ValueError(f"Formato não suportado: {format}")

    def _export_json(self, summary: CallSummary) -> str:
        """Exporta resumo em JSON."""
        return json.dumps({
            "key_points": summary.key_points,
            "objections": [{
                "type": obj.type,
                "handled": obj.handled,
                "note": obj.note
            } for obj in summary.objections],
            "next_steps": [{
                "desc": step.desc,
                "due": step.due,
                "owner": step.owner
            } for step in summary.next_steps],
            "metrics": {
                "talk_time_vendor_pct": summary.metrics.talk_time_vendor_pct,
                "sentiment_avg": summary.metrics.sentiment_avg,
                "objections_resolved": summary.metrics.objections_resolved,
                "buying_signals": summary.metrics.buying_signals
            }
        }, indent=2, ensure_ascii=False)

    def _export_markdown(self, summary: CallSummary, call_id: str) -> str:
        """Exporta resumo em Markdown."""
        return f"""# Resumo da Chamada - {call_id}

## 📋 Pontos Principais

{chr(10).join([f"- {point}" for point in summary.key_points])}

## 🚨 Objeções Tratadas

{chr(10).join([f"- **{obj.type.title()}**: {'✅ Resolvida' if obj.handled else '❌ Pendente'}" + (f" - {obj.note}" if obj.note else "") for obj in summary.objections]) if summary.objections else "Nenhuma objeção detectada"}

## ✅ Próximos Passos

{chr(10).join([f"- [ ] {step.desc}" + (f" (até {step.due})" if step.due else "") + (f" - {step.owner}" if step.owner != "vendedor" else "") for step in summary.next_steps])}

## 📊 Métricas

- **Tempo de fala do vendedor**: {summary.metrics.talk_time_vendor_pct:.1%}
- **Sentimento médio**: {summary.metrics.sentiment_avg:.2f}
- **Objeções resolvidas**: {summary.metrics.objections_resolved}/{summary.metrics.objections_total}
- **Sinais de compra**: {summary.metrics.buying_signals}

---
*Gerado automaticamente pelo PitchAI*
"""

    def _export_pdf(self, summary: CallSummary, call_id: str) -> str:
        """Exporta resumo em PDF."""
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("ReportLab não disponível, retornando Markdown")
            return self._export_markdown(summary, call_id)
        
        try:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
                title=f"Resumo da Chamada - {call_id}"
            )
            
            story = []
            
            # Título
            title = Paragraph("📋 Resumo da Chamada", self.styles['CustomTitle'])
            story.append(title)
            
            # Info da chamada
            call_info = f"""
            <b>ID da Chamada:</b> {call_id}<br/>
            <b>Data de Geração:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>
            <b>Sistema:</b> PitchAI - Copiloto de Vendas
            """
            story.append(Paragraph(call_info, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Métricas
            section_title = Paragraph("📊 Métricas da Chamada", self.styles['SectionHeader'])
            story.append(section_title)
            
            metrics_data = [
                ['Métrica', 'Valor'],
                ['Tempo de Fala do Vendedor', f"{summary.metrics.talk_time_vendor_pct:.1%}"],
                ['Sentimento Médio', f"{summary.metrics.sentiment_avg:.2f}"],
                ['Objeções Resolvidas', f"{summary.metrics.objections_resolved}/{summary.metrics.objections_total}"],
                ['Sinais de Compra', str(summary.metrics.buying_signals)]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[6*cm, 4*cm])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e2e8f0'))
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # Pontos principais
            section_title = Paragraph("🎯 Pontos Principais", self.styles['SectionHeader'])
            story.append(section_title)
            
            for i, point in enumerate(summary.key_points, 1):
                bullet_text = f"<b>{i}.</b> {point}"
                story.append(Paragraph(bullet_text, self.styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Próximos passos
            section_title = Paragraph("✅ Próximos Passos", self.styles['SectionHeader'])
            story.append(section_title)
            
            if summary.next_steps:
                steps_data = [['#', 'Ação', 'Prazo', 'Responsável']]
                
                for i, step in enumerate(summary.next_steps, 1):
                    due_date = step.due if step.due else 'Não definido'
                    owner = step.owner if step.owner else 'Vendedor'
                    
                    steps_data.append([
                        str(i),
                        step.desc,
                        due_date,
                        owner.title()
                    ])
                
                steps_table = Table(steps_data, colWidths=[1*cm, 6*cm, 2.5*cm, 2.5*cm])
                steps_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#059669')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecfdf5')),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#10b981'))
                ]))
                
                story.append(steps_table)
            
            story.append(Spacer(1, 30))
            
            # Rodapé
            footer_text = f"""
            Gerado automaticamente pelo <b>PitchAI</b> - Copiloto de Vendas NPU-Powered<br/>
            {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} | Processamento 100% local e privado
            """
            
            footer_para = Paragraph(footer_text, self.styles['Normal'])
            story.append(footer_para)
            
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Salvar arquivo no diretório do projeto
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            pdf_path = output_dir / f"resumo_{call_id}.pdf"
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            self.logger.info(f"📄 PDF gerado: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar PDF: {e}")
            return self._export_markdown(summary, call_id)
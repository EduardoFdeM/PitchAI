import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.core.summary_service import PostCallSummaryService, CallSummary

class TestPostCallSummaryService:
    """Testes para o serviço de resumo pós-chamada"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock do serviço LLM"""
        service = Mock()
        service.generate = AsyncMock(return_value="""
        {
            "key_points": ["Integração ERP", "Budget R$60-80k", "Timeline Q2"],
            "objections": [
                {"type": "preco", "handled": true, "note": "ROI explicado"},
                {"type": "timing", "handled": false, "note": "Precisa follow-up"}
            ],
            "next_steps": [
                {"desc": "Enviar proposta técnica", "due": "2025-01-17", "owner": "vendedor"},
                {"desc": "Agendar demo", "due": "2025-01-24"}
            ],
            "metrics": {
                "talk_time_vendor_pct": 45.0,
                "talk_time_client_pct": 55.0,
                "sentiment_avg": 0.75,
                "objections_total": 2,
                "objections_resolved": 1,
                "buying_signals": 3
            }
        }
        """)
        return service
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock do serviço de storage"""
        service = Mock()
        service.get_transcript = AsyncMock(return_value={
            "call_id": "test_call_123",
            "duration_sec": 1800,
            "chunks": [
                {"speaker": "vendor", "text": "Olá, como posso ajudar?", "duration_sec": 2},
                {"speaker": "client", "text": "Preciso de uma solução ERP", "duration_sec": 3},
                {"speaker": "vendor", "text": "Temos uma solução perfeita", "duration_sec": 4}
            ]
        })
        service.get_sentiment_data = AsyncMock(return_value={
            "average_sentiment": 0.75,
            "average_engagement": 0.8,
            "buying_signals_count": 3,
            "samples": []
        })
        service.get_objections = AsyncMock(return_value=[
            {"type": "preco", "handled": True, "suggestion": "ROI explicado"},
            {"type": "timing", "handled": False, "suggestion": "Precisa follow-up"}
        ])
        service.save_summary = AsyncMock()
        return service
    
    @pytest.fixture
    def summary_service(self, mock_llm_service, mock_storage_service):
        """Instância do serviço de resumo"""
        return PostCallSummaryService(
            llm_service=mock_llm_service,
            storage_service=mock_storage_service
        )
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, summary_service, mock_storage_service):
        """Testa geração de resumo completo"""
        call_id = "test_call_123"
        
        # Executar geração
        summary = await summary_service.generate(call_id)
        
        # Verificar que é uma instância de CallSummary
        assert isinstance(summary, CallSummary)
        
        # Verificar estrutura do resumo
        assert len(summary.key_points) > 0
        assert len(summary.objections) > 0
        assert len(summary.next_steps) > 0
        assert "talk_time_vendor_pct" in summary.metrics
        
        # Verificar que foi salvo no storage
        mock_storage_service.save_summary.assert_called_once_with(call_id, summary)
    
    @pytest.mark.asyncio
    async def test_calculate_metrics(self, summary_service):
        """Testa cálculo de métricas"""
        transcript = {
            "duration_sec": 100,
            "chunks": [
                {"speaker": "vendor", "duration_sec": 40},
                {"speaker": "client", "duration_sec": 60}
            ]
        }
        sentiment_data = {
            "average_sentiment": 0.75,
            "buying_signals_count": 2
        }
        objections = [
            {"handled": True},
            {"handled": False}
        ]
        
        metrics = summary_service._calculate_metrics(transcript, sentiment_data, objections)
        
        assert metrics["talk_time_vendor_pct"] == 40.0
        assert metrics["talk_time_client_pct"] == 60.0
        assert metrics["sentiment_avg"] == 0.75
        assert metrics["objections_total"] == 2
        assert metrics["objections_resolved"] == 1
        assert metrics["buying_signals"] == 2
    
    def test_export_markdown(self, summary_service):
        """Testa exportação em Markdown"""
        summary = CallSummary(
            key_points=["Ponto 1", "Ponto 2"],
            objections=[{"type": "preco", "handled": True, "note": "ROI explicado"}],
            next_steps=[{"desc": "Enviar proposta", "due": "2025-01-17"}],
            metrics={"talk_time_vendor_pct": 45.0, "sentiment_avg": 0.75}
        )
        
        md = summary_service._export_markdown(summary)
        
        assert "# Resumo da Chamada" in md
        assert "Ponto 1" in md
        assert "Ponto 2" in md
        assert "✅" in md  # Objeção resolvida
        assert "Enviar proposta" in md
    
    @pytest.mark.asyncio
    async def test_export_summary(self, summary_service, mock_storage_service):
        """Testa exportação de resumo"""
        call_id = "test_call_123"
        mock_summary = CallSummary(
            key_points=["Teste"],
            objections=[],
            next_steps=[],
            metrics={}
        )
        
        # Mock do método get
        summary_service.get = AsyncMock(return_value=mock_summary)
        
        # Testar export MD
        md_result = await summary_service.export(call_id, "md")
        assert "# Resumo da Chamada" in md_result
        
        # Testar export PDF (placeholder)
        pdf_result = await summary_service.export(call_id, "pdf")
        assert "# Resumo da Chamada" in pdf_result  # Por enquanto retorna MD
        
        # Testar formato inválido
        with pytest.raises(ValueError):
            await summary_service.export(call_id, "invalid")

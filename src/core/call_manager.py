"""
Call Manager - PitchAI
======================

Orquestra o ciclo completo de uma chamada:
- Início e fim da sessão
- Coordenação entre serviços (transcrição, sentimento, objeções, resumo)
- Geração automática de resumo pós-chamada
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from data.database import DatabaseManager
from ai.summary_service import SummaryService
from data.models import CallSummary


class CallManager:
    """
    Gerenciador do ciclo de vida das chamadas.
    
    Coordena a integração entre todos os serviços para:
    - Capturar dados durante a chamada
    - Gerar resumo automático ao final
    - Persistir informações no histórico
    """
    
    def __init__(self, database: DatabaseManager, npu_manager, summary_service: SummaryService):
        """
        Inicializa o gerenciador de chamadas.
        
        Args:
            database: Gerenciador do banco de dados
            npu_manager: Gerenciador da NPU
            summary_service: Serviço de geração de resumos
        """
        self.database = database
        self.npu_manager = npu_manager
        self.summary_service = summary_service
        self.logger = logging.getLogger(__name__)
        
        # Estado atual da chamada
        self.current_call_id: Optional[str] = None
        self.call_start_time: Optional[datetime] = None
        self.is_active = False
    
    def start_call(self, contact_id: str = None, channel: str = "unknown") -> str:
        """
        Inicia uma nova chamada.
        
        Args:
            contact_id: ID do contato (opcional)
            channel: Canal da chamada (teams, zoom, meet, etc.)
            
        Returns:
            ID da chamada criada
        """
        if self.is_active:
            self.logger.warning("⚠️ Chamada já ativa, finalizando anterior...")
            self.end_call()
        
        # Criar nova chamada no banco
        self.current_call_id = self.database.create_call(contact_id, channel)
        self.call_start_time = datetime.now()
        self.is_active = True
        
        self.logger.info(f"📞 Chamada iniciada: {self.current_call_id}")
        return self.current_call_id
    
    def add_transcript_chunk(self, speaker: str, text: str, ts_start_ms: int, 
                           ts_end_ms: int, confidence: float = None):
        """
        Adiciona chunk de transcrição à chamada atual.
        
        Args:
            speaker: Identificação do falante (vendor/client)
            text: Texto transcrito
            ts_start_ms: Timestamp de início em ms
            ts_end_ms: Timestamp de fim em ms
            confidence: Confiança da transcrição (0-1)
        """
        if not self.is_active or not self.current_call_id:
            self.logger.warning("⚠️ Tentativa de adicionar transcrição sem chamada ativa")
            return
        
        self.database.add_transcript_chunk(
            self.current_call_id, speaker, ts_start_ms, ts_end_ms, text, confidence
        )
    
    def add_objection_event(self, objection_type: str, ts_start_ms: int, 
                          ts_end_ms: int = None, confidence: float = None,
                          suggestion_used: str = None):
        """
        Registra evento de objeção detectada.
        
        Args:
            objection_type: Tipo da objeção (preco, timing, autoridade, necessidade)
            ts_start_ms: Timestamp de início
            ts_end_ms: Timestamp de fim (opcional)
            confidence: Confiança da detecção
            suggestion_used: Sugestão utilizada pelo vendedor
        """
        if not self.is_active or not self.current_call_id:
            return
        
        # TODO: Implementar registro de objeções no banco
        self.logger.info(f"🚨 Objeção detectada: {objection_type} em {ts_start_ms}ms")
    
    def add_sentiment_sample(self, ts_start_ms: int, ts_end_ms: int, 
                           valence: float, engagement: float = None):
        """
        Adiciona amostra de análise de sentimento.
        
        Args:
            ts_start_ms: Timestamp de início
            ts_end_ms: Timestamp de fim
            valence: Valência do sentimento (-1 a +1)
            engagement: Nível de engajamento (0 a 1)
        """
        if not self.is_active or not self.current_call_id:
            return
        
        # TODO: Implementar registro de sentimento no banco
        self.logger.debug(f"💭 Sentimento: {valence:.2f} ({ts_start_ms}-{ts_end_ms}ms)")
    
    def end_call(self) -> Optional[CallSummary]:
        """
        Finaliza a chamada atual e gera resumo automático.
        
        Implementa Feature 5: Geração automática de resumo pós-chamada
        
        Returns:
            Resumo estruturado da chamada ou None se não houver chamada ativa
        """
        if not self.is_active or not self.current_call_id:
            self.logger.warning("⚠️ Tentativa de finalizar chamada sem chamada ativa")
            return None
        
        try:
            self.logger.info(f"⏹️ Finalizando chamada: {self.current_call_id}")
            
            # Calcular métricas básicas da chamada
            call_duration = (datetime.now() - self.call_start_time).total_seconds()
            
            # Gerar resumo automático
            self.logger.info("📄 Gerando resumo pós-chamada...")
            summary = self.summary_service.generate_summary(self.current_call_id)
            
            # Resetar estado
            call_id = self.current_call_id
            self.current_call_id = None
            self.call_start_time = None
            self.is_active = False
            
            self.logger.info(f"✅ Chamada finalizada com resumo: {call_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao finalizar chamada: {e}")
            # Resetar estado mesmo com erro
            self.current_call_id = None
            self.call_start_time = None
            self.is_active = False
            raise
    
    def get_current_call_id(self) -> Optional[str]:
        """
        Retorna o ID da chamada atual.
        
        Returns:
            ID da chamada ativa ou None
        """
        return self.current_call_id if self.is_active else None
    
    def is_call_active(self) -> bool:
        """
        Verifica se há uma chamada ativa.
        
        Returns:
            True se há chamada ativa, False caso contrário
        """
        return self.is_active and self.current_call_id is not None
    
    def get_call_summary(self, call_id: str) -> Optional[CallSummary]:
        """
        Recupera resumo de uma chamada específica.
        
        Args:
            call_id: ID da chamada
            
        Returns:
            Resumo da chamada ou None se não encontrado
        """
        return self.summary_service.get_summary(call_id)
    
    def export_call_summary(self, call_id: str, format: str = "json") -> str:
        """
        Exporta resumo de uma chamada em formato específico.
        
        Args:
            call_id: ID da chamada
            format: Formato de exportação (json, md, pdf)
            
        Returns:
            Conteúdo exportado
        """
        return self.summary_service.export_summary(call_id, format)
    
    def simulate_call_data(self):
        """
        Simula dados de uma chamada para desenvolvimento/demo.
        
        Adiciona transcrição, objeções e métricas simuladas.
        """
        if not self.is_active or not self.current_call_id:
            self.logger.warning("⚠️ Nenhuma chamada ativa para simular dados")
            return
        
        # Simular transcrição
        sample_transcript = [
            ("vendor", "Olá! Como posso ajudá-lo hoje?", 0, 2000),
            ("client", "Estou interessado na sua solução de CRM", 2500, 5000),
            ("vendor", "Perfeito! Qual o tamanho da sua equipe?", 5500, 7500),
            ("client", "Somos cerca de 50 pessoas", 8000, 10000),
            ("vendor", "E qual o orçamento disponível?", 10500, 12000),
            ("client", "Estamos pensando entre 50 e 80 mil", 12500, 15000),
            ("vendor", "Ótimo! Posso mostrar como nossa solução se integra", 15500, 18000),
            ("client", "O preço está um pouco alto...", 18500, 20000),
            ("vendor", "Entendo. Vamos falar sobre o ROI em 18 meses", 20500, 23000),
            ("client", "Interessante. Preciso conversar com minha equipe", 23500, 26000),
        ]
        
        for speaker, text, start_ms, end_ms in sample_transcript:
            self.add_transcript_chunk(speaker, text, start_ms, end_ms, 0.95)
        
        # Simular objeções
        self.add_objection_event("preco", 18500, 20000, 0.9, "ROI em 18 meses")
        
        # Simular sentimento
        self.add_sentiment_sample(0, 26000, 0.7, 0.8)
        
        self.logger.info("🎭 Dados simulados adicionados à chamada")
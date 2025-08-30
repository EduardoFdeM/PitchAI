"""
UiBridge - Ponte entre EventBus e UI PyQt6
==========================================

Conecta eventos do backend com sinais da interface gráfica.
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

from ..core.event_bus import get_event_bus, subscribe_to_event, unsubscribe_from_event
from ..core.contracts import EventType


class UiBridge(QObject):
    """Ponte thread-safe entre EventBus e UI PyQt6."""
    
    # Sinais para eventos ASR
    asr_chunk = pyqtSignal(object)  # Dict com payload do evento
    
    # Sinais para eventos de sentimento
    sentiment_update = pyqtSignal(object)  # Dict com payload do evento
    
    # Sinais para eventos de objeções e RAG
    objection_detected = pyqtSignal(object)  # Dict com payload do evento
    rag_suggestions = pyqtSignal(object)  # Dict com payload do evento
    
    # Sinais para eventos de resumo
    summary_ready = pyqtSignal(object)  # Dict com payload do evento
    
    # Sinais para eventos de sistema
    system_status = pyqtSignal(object)  # Dict com payload do evento
    error = pyqtSignal(object)  # Dict com payload do evento
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        
        # Timer para debouncing de eventos ASR
        self.asr_debounce_timer = QTimer()
        self.asr_debounce_timer.setSingleShot(True)
        self.asr_debounce_timer.timeout.connect(self._emit_pending_asr)
        self.pending_asr_events = []
        
        # Timer para debouncing de eventos de sentimento
        self.sentiment_debounce_timer = QTimer()
        self.sentiment_debounce_timer.setSingleShot(True)
        self.sentiment_debounce_timer.timeout.connect(self._emit_pending_sentiment)
        self.pending_sentiment_events = []
        
        # Conectar ao EventBus
        self._wire_to_event_bus()
        
        self.logger.info("✅ UiBridge inicializado")
    
    def _wire_to_event_bus(self):
        """Conectar sinais ao EventBus."""
        # ASR - com debouncing
        subscribe_to_event(EventType.ASR_CHUNK.value, self._on_asr_chunk)
        
        # Sentimento - com debouncing
        subscribe_to_event(EventType.SENTIMENT_UPDATE.value, self._on_sentiment_update)
        
        # Objeções - sem debouncing (importantes)
        subscribe_to_event(EventType.OBJECTION_DETECTED.value, self._on_objection_detected)
        
        # RAG - sem debouncing (streaming)
        subscribe_to_event(EventType.RAG_SUGGESTIONS.value, self._on_rag_suggestions)
        
        # Resumo - sem debouncing
        subscribe_to_event(EventType.SUMMARY_READY.value, self._on_summary_ready)
        
        # Sistema - sem debouncing
        subscribe_to_event(EventType.SYSTEM_STATUS.value, self._on_system_status)
        subscribe_to_event(EventType.ERROR.value, self._on_error)
        
        self.logger.info("🔗 UiBridge conectado ao EventBus")
    
    def _on_asr_chunk(self, payload: Dict[str, Any]):
        """Handler para eventos ASR com debouncing."""
        self.pending_asr_events.append(payload)
        
        # Reiniciar timer de debouncing (150ms)
        if not self.asr_debounce_timer.isActive():
            self.asr_debounce_timer.start(150)
    
    def _emit_pending_asr(self):
        """Emitir apenas o último evento ASR pendente."""
        if self.pending_asr_events:
            # Pegar apenas o último evento
            latest_event = self.pending_asr_events[-1]
            self.asr_chunk.emit(latest_event)
            self.pending_asr_events.clear()
            
            self.logger.debug(f"📢 ASR chunk emitido (debounced)")
    
    def _on_sentiment_update(self, payload: Dict[str, Any]):
        """Handler para eventos de sentimento com debouncing."""
        self.pending_sentiment_events.append(payload)
        
        # Reiniciar timer de debouncing (100ms)
        if not self.sentiment_debounce_timer.isActive():
            self.sentiment_debounce_timer.start(100)
    
    def _emit_pending_sentiment(self):
        """Emitir apenas o último evento de sentimento pendente."""
        if self.pending_sentiment_events:
            # Pegar apenas o último evento
            latest_event = self.pending_sentiment_events[-1]
            self.sentiment_update.emit(latest_event)
            self.pending_sentiment_events.clear()
            
            self.logger.debug(f"📊 Sentiment update emitido (debounced)")
    
    def _on_objection_detected(self, payload: Dict[str, Any]):
        """Handler para eventos de objeção (sem debouncing)."""
        self.objection_detected.emit(payload)
        self.logger.info(f"🚨 Objeção detectada: {payload.get('category', 'unknown')}")
    
    def _on_rag_suggestions(self, payload: Dict[str, Any]):
        """Handler para eventos RAG (sem debouncing)."""
        self.rag_suggestions.emit(payload)
        self.logger.debug(f"💡 RAG suggestions emitidas")
    
    def _on_summary_ready(self, payload: Dict[str, Any]):
        """Handler para eventos de resumo (sem debouncing)."""
        self.summary_ready.emit(payload)
        self.logger.info(f"📋 Resumo pronto para call {payload.get('call_id', 'unknown')}")
    
    def _on_system_status(self, payload: Dict[str, Any]):
        """Handler para eventos de status do sistema (sem debouncing)."""
        self.system_status.emit(payload)
        self.logger.debug(f"🔧 System status: {payload.get('npu', 'unknown')}")
    
    def _on_error(self, payload: Dict[str, Any]):
        """Handler para eventos de erro (sem debouncing)."""
        self.error.emit(payload)
        self.logger.error(f"❌ Error: {payload.get('message', 'unknown error')}")
    
    def cleanup(self):
        """Limpar recursos e desconectar do EventBus."""
        # Parar timers
        self.asr_debounce_timer.stop()
        self.sentiment_debounce_timer.stop()
        
        # Limpar eventos pendentes
        self.pending_asr_events.clear()
        self.pending_sentiment_events.clear()
        
        # Desconectar do EventBus
        unsubscribe_from_event(EventType.ASR_CHUNK.value, self._on_asr_chunk)
        unsubscribe_from_event(EventType.SENTIMENT_UPDATE.value, self._on_sentiment_update)
        unsubscribe_from_event(EventType.OBJECTION_DETECTED.value, self._on_objection_detected)
        unsubscribe_from_event(EventType.RAG_SUGGESTIONS.value, self._on_rag_suggestions)
        unsubscribe_from_event(EventType.SUMMARY_READY.value, self._on_summary_ready)
        unsubscribe_from_event(EventType.SYSTEM_STATUS.value, self._on_system_status)
        unsubscribe_from_event(EventType.ERROR.value, self._on_error)
        
        self.logger.info("🧹 UiBridge limpo")


def create_ui_bridge() -> UiBridge:
    """Factory function para criar UiBridge."""
    return UiBridge()


def wire_bus_to_ui(event_bus, bridge: UiBridge):
    """Função de conveniência para conectar EventBus ao UiBridge."""
    # O UiBridge já se conecta automaticamente no __init__
    # Esta função é mantida para compatibilidade
    pass 
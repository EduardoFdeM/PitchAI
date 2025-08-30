"""
UI Store - Estado centralizado da interface
==========================================

Gerenciamento de estado thread-safe com janela deslizante para performance.
"""

import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass, field

from ..core.contracts import EventType


@dataclass
class TranscriptEntry:
    """Entrada de transcrição."""
    t0: int  # timestamp início
    t1: int  # timestamp fim
    text: str
    source: str  # 'mic' ou 'loopback'
    confidence: float


@dataclass
class SentimentEntry:
    """Entrada de sentimento."""
    window_start: int
    window_end: int
    valence: float
    engagement: float
    sources: Dict[str, float]
    details: Optional[Dict[str, float]] = None


@dataclass
class ObjectionEntry:
    """Entrada de objeção."""
    ts_ms: int
    category: str
    confidence: float
    context_snippet: str
    call_id: str


@dataclass
class SuggestionEntry:
    """Entrada de sugestão RAG."""
    text: str
    score: float
    sources: List[Dict[str, str]]
    objection_id: str


class UIStore:
    """Store thread-safe para estado da UI."""
    
    def __init__(self, max_history_minutes: int = 10):
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # Configurações
        self.max_history_minutes = max_history_minutes
        self.max_history_ms = max_history_minutes * 60 * 1000
        
        # Estado principal
        self.call_id: Optional[str] = None
        self.transcript: Dict[str, deque] = {
            "mic": deque(maxlen=1000),  # Limite por segurança
            "loopback": deque(maxlen=1000)
        }
        self.sentiment: Dict[str, Any] = {
            "series": deque(maxlen=200),  # ~10 min de dados a cada 3s
            "last": None
        }
        self.objections: deque = deque(maxlen=50)  # Últimas 50 objeções
        self.suggestions: List[SuggestionEntry] = []
        self.summary: Optional[Dict[str, Any]] = None
        self.status: Dict[str, Any] = {
            "npu": "CPU",
            "models": {}
        }
        
        # Callbacks para notificar mudanças
        self._change_callbacks: List[Callable[[str, Any], None]] = []
        
        # Métricas
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # segundos
        
        self.logger.info(f"✅ UI Store inicializado (histórico: {max_history_minutes}min)")
    
    def add_change_callback(self, callback: Callable[[str, Any], None]):
        """Adicionar callback para notificar mudanças."""
        with self._lock:
            self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, Any], None]):
        """Remover callback de mudanças."""
        with self._lock:
            try:
                self._change_callbacks.remove(callback)
            except ValueError:
                pass
    
    def _notify_change(self, section: str, data: Any):
        """Notificar mudanças para callbacks."""
        for callback in self._change_callbacks:
            try:
                callback(section, data)
            except Exception as e:
                self.logger.error(f"Erro no callback de mudança: {e}")
    
    def set_call_id(self, call_id: str):
        """Definir ID da chamada atual."""
        with self._lock:
            self.call_id = call_id
            self._notify_change("call_id", call_id)
    
    def add_transcript_chunk(self, source: str, t0: int, t1: int, text: str, confidence: float):
        """Adicionar chunk de transcrição."""
        with self._lock:
            entry = TranscriptEntry(
                t0=t0, t1=t1, text=text, source=source, confidence=confidence
            )
            
            if source in self.transcript:
                self.transcript[source].append(entry)
                self._notify_change("transcript", {"source": source, "entry": entry})
            
            # Cleanup periódico
            self._maybe_cleanup()
    
    def add_sentiment_update(self, window_start: int, window_end: int, valence: float,
                           engagement: float, sources: Dict[str, float],
                           details: Optional[Dict[str, float]] = None):
        """Adicionar atualização de sentimento."""
        with self._lock:
            entry = SentimentEntry(
                window_start=window_start,
                window_end=window_end,
                valence=valence,
                engagement=engagement,
                sources=sources,
                details=details
            )
            
            self.sentiment["series"].append(entry)
            self.sentiment["last"] = entry
            
            self._notify_change("sentiment", entry)
    
    def add_objection(self, ts_ms: int, category: str, confidence: float,
                     context_snippet: str, call_id: str):
        """Adicionar objeção detectada."""
        with self._lock:
            entry = ObjectionEntry(
                ts_ms=ts_ms,
                category=category,
                confidence=confidence,
                context_snippet=context_snippet,
                call_id=call_id
            )
            
            self.objections.append(entry)
            self._notify_change("objection", entry)
    
    def set_suggestions(self, suggestions: List[Dict[str, Any]], objection_id: str):
        """Definir sugestões RAG atuais."""
        with self._lock:
            self.suggestions = [
                SuggestionEntry(
                    text=s["text"],
                    score=s["score"],
                    sources=s["sources"],
                    objection_id=objection_id
                ) for s in suggestions
            ]
            
            self._notify_change("suggestions", self.suggestions)
    
    def set_summary(self, summary_json: Dict[str, Any]):
        """Definir resumo da chamada."""
        with self._lock:
            self.summary = summary_json
            self._notify_change("summary", summary_json)
    
    def set_status(self, npu: str, models: Dict[str, str]):
        """Definir status do sistema."""
        with self._lock:
            self.status["npu"] = npu
            self.status["models"] = models
            self._notify_change("status", self.status)
    
    def get_state(self) -> Dict[str, Any]:
        """Obter estado completo (thread-safe)."""
        with self._lock:
            return {
                "call_id": self.call_id,
                "transcript": {
                    "mic": list(self.transcript["mic"]),
                    "loopback": list(self.transcript["loopback"])
                },
                "sentiment": {
                    "series": list(self.sentiment["series"]),
                    "last": self.sentiment["last"]
                },
                "objections": list(self.objections),
                "suggestions": self.suggestions,
                "summary": self.summary,
                "status": self.status.copy()
            }
    
    def get_transcript_window(self, source: str, start_ms: int, end_ms: int) -> List[TranscriptEntry]:
        """Obter transcrição em janela de tempo."""
        with self._lock:
            if source not in self.transcript:
                return []
            
            entries = []
            for entry in self.transcript[source]:
                if start_ms <= entry.t0 <= end_ms:
                    entries.append(entry)
            
            return entries
    
    def get_sentiment_window(self, start_ms: int, end_ms: int) -> List[SentimentEntry]:
        """Obter sentimento em janela de tempo."""
        with self._lock:
            entries = []
            for entry in self.sentiment["series"]:
                if start_ms <= entry.window_start <= end_ms:
                    entries.append(entry)
            
            return entries
    
    def get_recent_objections(self, minutes: int = 5) -> List[ObjectionEntry]:
        """Obter objeções recentes."""
        with self._lock:
            cutoff_time = time.time() * 1000 - (minutes * 60 * 1000)
            return [
                obj for obj in self.objections
                if obj.ts_ms >= cutoff_time
            ]
    
    def _maybe_cleanup(self):
        """Cleanup periódico de dados antigos."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = current_time
        cutoff_time = current_time * 1000 - self.max_history_ms
        
        # Cleanup de transcrição
        for source in self.transcript:
            # Manter apenas entradas recentes
            while (self.transcript[source] and 
                   self.transcript[source][0].t0 < cutoff_time):
                self.transcript[source].popleft()
        
        # Cleanup de sentimento
        while (self.sentiment["series"] and 
               self.sentiment["series"][0].window_start < cutoff_time):
            self.sentiment["series"].popleft()
        
        # Cleanup de objeções
        while (self.objections and 
               self.objections[0].ts_ms < cutoff_time):
            self.objections.popleft()
        
        self.logger.debug("🧹 Cleanup de dados antigos realizado")
    
    def clear(self):
        """Limpar todo o estado."""
        with self._lock:
            self.call_id = None
            for source in self.transcript:
                self.transcript[source].clear()
            self.sentiment["series"].clear()
            self.sentiment["last"] = None
            self.objections.clear()
            self.suggestions.clear()
            self.summary = None
            self.status = {"npu": "CPU", "models": {}}
            
            self._notify_change("clear", None)
            self.logger.info("🧹 Estado da UI limpo")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do store."""
        with self._lock:
            return {
                "transcript_entries": {
                    "mic": len(self.transcript["mic"]),
                    "loopback": len(self.transcript["loopback"])
                },
                "sentiment_entries": len(self.sentiment["series"]),
                "objections": len(self.objections),
                "suggestions": len(self.suggestions),
                "call_id": self.call_id,
                "max_history_minutes": self.max_history_minutes
            }


# Instância global do store
ui_store = UIStore()


def get_ui_store() -> UIStore:
    """Obter instância global do UI Store."""
    return ui_store 
"""
Contratos de eventos - Fonte única de verdade para UI
====================================================

Definições de payloads imutáveis para todos os eventos do sistema.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Tipos de eventos do sistema."""
    ASR_CHUNK = "asr.chunk"
    SENTIMENT_UPDATE = "sentiment.update"
    OBJECTION_DETECTED = "objection.detected"
    RAG_SUGGESTIONS = "rag.suggestions"
    SUMMARY_READY = "summary.ready"
    SYSTEM_STATUS = "system.status"
    ERROR = "error"


class AudioSource(Enum):
    """Fontes de áudio."""
    MIC = "mic"
    LOOPBACK = "loopback"


class ObjectionCategory(Enum):
    """Categorias de objeções."""
    PRECO = "preco"
    TIMING = "timing"
    AUTORIDADE = "autoridade"
    NECESSIDADE = "necessidade"


class NPUProvider(Enum):
    """Provedores de NPU."""
    QNN = "QNN"
    CPU = "CPU"
    DML = "DML"


class ModelStatus(Enum):
    """Status dos modelos."""
    OK = "ok"
    FAIL = "fail"


class ErrorScope(Enum):
    """Escopos de erro."""
    ASR = "asr"
    SENTIMENT = "sentiment"
    RAG = "rag"
    SUMMARY = "summary"
    IO = "io"


@dataclass
class ASRChunkEvent:
    """Evento de chunk de transcrição."""
    call_id: str
    source: AudioSource
    ts_start_ms: int
    ts_end_ms: int
    text: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "source": self.source.value,
            "ts_start_ms": self.ts_start_ms,
            "ts_end_ms": self.ts_end_ms,
            "text": self.text,
            "confidence": self.confidence
        }


@dataclass
class SentimentUpdateEvent:
    """Evento de atualização de sentimento."""
    call_id: str
    window_start_ms: int
    window_end_ms: int
    valence: float  # -1.0 a +1.0
    engagement: float  # 0.0 a 1.0
    sources: Dict[str, float]  # text, voice, vision
    details: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "call_id": self.call_id,
            "window_start_ms": self.window_start_ms,
            "window_end_ms": self.window_end_ms,
            "valence": self.valence,
            "engagement": self.engagement,
            "sources": self.sources
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class ObjectionDetectedEvent:
    """Evento de objeção detectada."""
    call_id: str
    ts_ms: int
    category: ObjectionCategory
    confidence: float
    context_snippet: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "ts_ms": self.ts_ms,
            "category": self.category.value,
            "confidence": self.confidence,
            "context_snippet": self.context_snippet
        }


@dataclass
class RAGSuggestion:
    """Sugestão do RAG."""
    text: str
    score: float
    sources: List[Dict[str, str]]  # [{id, title}]


@dataclass
class RAGRetrieved:
    """Documento recuperado do RAG."""
    id: str
    title: str
    snippet: str


@dataclass
class RAGSuggestionsEvent:
    """Evento de sugestões RAG."""
    call_id: str
    objection_id: str
    suggestions: List[RAGSuggestion]
    retrieved: List[RAGRetrieved]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "objection_id": self.objection_id,
            "suggestions": [
                {
                    "text": s.text,
                    "score": s.score,
                    "sources": s.sources
                } for s in self.suggestions
            ],
            "retrieved": [
                {
                    "id": r.id,
                    "title": r.title,
                    "snippet": r.snippet
                } for r in self.retrieved
            ]
        }


@dataclass
class SummaryReadyEvent:
    """Evento de resumo pronto."""
    call_id: str
    summary_json: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "summary_json": self.summary_json
        }


@dataclass
class SystemStatusEvent:
    """Evento de status do sistema."""
    npu: NPUProvider
    models: Dict[str, ModelStatus]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "npu": self.npu.value,
            "models": {k: v.value for k, v in self.models.items()}
        }


@dataclass
class ErrorEvent:
    """Evento de erro."""
    scope: ErrorScope
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "scope": self.scope.value,
            "code": self.code,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


# Factory functions para criar eventos
def create_asr_chunk(call_id: str, source: str, ts_start: int, ts_end: int, 
                    text: str, confidence: float) -> ASRChunkEvent:
    """Criar evento ASR chunk."""
    return ASRChunkEvent(
        call_id=call_id,
        source=AudioSource(source),
        ts_start_ms=ts_start,
        ts_end_ms=ts_end,
        text=text,
        confidence=confidence
    )


def create_sentiment_update(call_id: str, window_start: int, window_end: int,
                          valence: float, engagement: float, sources: Dict[str, float],
                          details: Optional[Dict[str, float]] = None) -> SentimentUpdateEvent:
    """Criar evento de atualização de sentimento."""
    return SentimentUpdateEvent(
        call_id=call_id,
        window_start_ms=window_start,
        window_end_ms=window_end,
        valence=valence,
        engagement=engagement,
        sources=sources,
        details=details
    )


def create_objection_detected(call_id: str, ts_ms: int, category: str,
                            confidence: float, context: str) -> ObjectionDetectedEvent:
    """Criar evento de objeção detectada."""
    return ObjectionDetectedEvent(
        call_id=call_id,
        ts_ms=ts_ms,
        category=ObjectionCategory(category),
        confidence=confidence,
        context_snippet=context
    )


def create_system_status(npu: str, models: Dict[str, str]) -> SystemStatusEvent:
    """Criar evento de status do sistema."""
    return SystemStatusEvent(
        npu=NPUProvider(npu),
        models={k: ModelStatus(v) for k, v in models.items()}
    )


def create_error(scope: str, code: str, message: str, 
                details: Optional[Dict[str, Any]] = None) -> ErrorEvent:
    """Criar evento de erro."""
    return ErrorEvent(
        scope=ErrorScope(scope),
        code=code,
        message=message,
        details=details
    ) 
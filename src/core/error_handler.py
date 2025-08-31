"""
Sistema de Tratamento de Erros Centralizado
==========================================

Gerencia erros de forma consistente em todo o sistema, com logging estruturado,
fallbacks inteligentes e métricas de erro.
"""

import logging
import time
import traceback
import functools
from typing import Dict, Any, Callable, Optional, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading


class ErrorSeverity(Enum):
    """Níveis de severidade de erro."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categorias de erro."""
    NETWORK = "network"
    DATABASE = "database"
    AUDIO = "audio"
    AI_MODEL = "ai_model"
    UI = "ui"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Contexto de um erro."""
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    call_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Registro de um erro."""
    timestamp: float
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    traceback: str
    resolved: bool = False
    resolution_time: Optional[float] = None
    resolution_method: Optional[str] = None


class ErrorHandler:
    """Sistema centralizado de tratamento de erros."""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Histórico de erros
        self.error_history: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_severity_counts: Dict[ErrorSeverity, int] = defaultdict(int)
        
        # Fallbacks configurados
        self.fallbacks: Dict[str, Callable] = {}
        self.retry_strategies: Dict[str, Dict[str, Any]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Métricas
        self.metrics = {
            "total_errors": 0,
            "errors_resolved": 0,
            "avg_resolution_time": 0.0,
            "most_common_errors": [],
            "error_rate_per_hour": 0.0
        }
        
        # Configurar fallbacks padrão
        self._setup_default_fallbacks()
        
        self.logger.info("✅ ErrorHandler inicializado")
    
    def _setup_default_fallbacks(self):
        """Configurar fallbacks padrão para operações críticas."""
        
        # Fallback para operações de rede
        self.register_fallback("network", self._network_fallback)
        
        # Fallback para operações de banco de dados
        self.register_fallback("database", self._database_fallback)
        
        # Fallback para operações de áudio
        self.register_fallback("audio", self._audio_fallback)
        
        # Fallback para operações de IA
        self.register_fallback("ai_model", self._ai_model_fallback)
    
    def register_fallback(self, category: str, fallback_func: Callable):
        """Registrar função de fallback para uma categoria."""
        self.fallbacks[category] = fallback_func
        self.logger.debug(f"Fallback registrado para categoria: {category}")
    
    def register_retry_strategy(self, operation: str, max_retries: int = 3, 
                              backoff_factor: float = 2.0, timeout: float = 30.0):
        """Registrar estratégia de retry para uma operação."""
        self.retry_strategies[operation] = {
            "max_retries": max_retries,
            "backoff_factor": backoff_factor,
            "timeout": timeout
        }
        self.logger.debug(f"Estratégia de retry registrada para: {operation}")
    
    def handle_error(self, error: Exception, context: ErrorContext, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    fallback: bool = True) -> Optional[Any]:
        """
        Tratar erro de forma centralizada.
        
        Args:
            error: Exceção capturada
            context: Contexto do erro
            severity: Severidade do erro
            category: Categoria do erro
            fallback: Se deve tentar fallback
            
        Returns:
            Resultado do fallback se aplicável, None caso contrário
        """
        # Criar registro do erro
        error_record = ErrorRecord(
            timestamp=time.time(),
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            context=context,
            traceback=traceback.format_exc()
        )
        
        # Adicionar ao histórico
        with self._lock:
            self.error_history.append(error_record)
            self.error_counts[error_record.error_type] += 1
            self.error_severity_counts[severity] += 1
            self.metrics["total_errors"] += 1
        
        # Log estruturado
        self._log_error(error_record)
        
        # Tentar fallback se configurado
        if fallback and category.value in self.fallbacks:
            try:
                fallback_result = self.fallbacks[category.value](error, context)
                self.logger.info(f"Fallback executado com sucesso para {category.value}")
                return fallback_result
            except Exception as fallback_error:
                self.logger.error(f"Fallback falhou para {category.value}: {fallback_error}")
        
        # Marcar como não resolvido
        return None
    
    def _log_error(self, error_record: ErrorRecord):
        """Log estruturado do erro."""
        log_data = {
            "error_type": error_record.error_type,
            "message": error_record.error_message,
            "severity": error_record.severity.value,
            "category": error_record.category.value,
            "component": error_record.context.component,
            "operation": error_record.context.operation,
            "timestamp": error_record.timestamp
        }
        
        # Adicionar contexto se disponível
        if error_record.context.user_id:
            log_data["user_id"] = error_record.context.user_id
        if error_record.context.session_id:
            log_data["session_id"] = error_record.context.session_id
        if error_record.context.call_id:
            log_data["call_id"] = error_record.context.call_id
        
        # Log baseado na severidade
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"ERRO CRÍTICO: {log_data}")
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(f"ERRO ALTO: {log_data}")
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"ERRO MÉDIO: {log_data}")
        else:
            self.logger.info(f"ERRO BAIXO: {log_data}")
        
        # Log traceback para erros críticos e altos
        if error_record.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self.logger.error(f"Traceback: {error_record.traceback}")
    
    def retry_operation(self, operation: str, func: Callable, *args, 
                       context: ErrorContext, **kwargs) -> Any:
        """
        Executar operação com retry automático.
        
        Args:
            operation: Nome da operação
            func: Função a ser executada
            context: Contexto para tratamento de erro
            *args, **kwargs: Argumentos para a função
            
        Returns:
            Resultado da função ou fallback
        """
        strategy = self.retry_strategies.get(operation, {
            "max_retries": 2,
            "backoff_factor": 1.5,
            "timeout": 10.0
        })
        
        last_error = None
        
        for attempt in range(strategy["max_retries"] + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                
                if attempt < strategy["max_retries"]:
                    wait_time = strategy["backoff_factor"] ** attempt
                    self.logger.warning(f"Tentativa {attempt + 1} falhou para {operation}, "
                                      f"aguardando {wait_time:.1f}s: {e}")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou
                    self.logger.error(f"Operação {operation} falhou após "
                                    f"{strategy['max_retries'] + 1} tentativas")
        
        # Todas as tentativas falharam
        if last_error:
            self.handle_error(last_error, context, 
                            severity=ErrorSeverity.HIGH,
                            category=self._categorize_error(last_error))
        
        return None
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorizar erro automaticamente."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Categorização baseada no tipo e mensagem
        if any(network_word in error_message for network_word in 
               ["connection", "timeout", "network", "http", "socket"]):
            return ErrorCategory.NETWORK
        
        elif any(db_word in error_message for db_word in 
                ["database", "sql", "connection", "query", "table"]):
            return ErrorCategory.DATABASE
        
        elif any(audio_word in error_message for audio_word in 
                ["audio", "microphone", "recording", "playback", "stream"]):
            return ErrorCategory.AUDIO
        
        elif any(ai_word in error_message for ai_word in 
                ["model", "inference", "tensor", "onnx", "llm"]):
            return ErrorCategory.AI_MODEL
        
        elif any(ui_word in error_message for ui_word in 
                ["widget", "window", "qt", "gui", "interface"]):
            return ErrorCategory.UI
        
        elif any(config_word in error_message for config_word in 
                ["config", "setting", "parameter", "option"]):
            return ErrorCategory.CONFIGURATION
        
        elif any(validation_word in error_message for validation_word in 
                ["validation", "invalid", "format", "type"]):
            return ErrorCategory.VALIDATION
        
        elif "timeout" in error_message:
            return ErrorCategory.TIMEOUT
        
        elif any(resource_word in error_message for resource_word in 
                ["memory", "disk", "file", "resource"]):
            return ErrorCategory.RESOURCE
        
        return ErrorCategory.UNKNOWN
    
    # Fallbacks padrão
    def _network_fallback(self, error: Exception, context: ErrorContext) -> Any:
        """Fallback para erros de rede."""
        self.logger.info("Executando fallback de rede")
        return {"status": "offline", "message": "Serviço temporariamente indisponível"}
    
    def _database_fallback(self, error: Exception, context: ErrorContext) -> Any:
        """Fallback para erros de banco de dados."""
        self.logger.info("Executando fallback de banco de dados")
        return {"status": "cache_only", "message": "Usando dados em cache"}
    
    def _audio_fallback(self, error: Exception, context: ErrorContext) -> Any:
        """Fallback para erros de áudio."""
        self.logger.info("Executando fallback de áudio")
        return {"status": "simulation", "message": "Modo de simulação ativado"}
    
    def _ai_model_fallback(self, error: Exception, context: ErrorContext) -> Any:
        """Fallback para erros de modelo de IA."""
        self.logger.info("Executando fallback de IA")
        return {"status": "rule_based", "message": "Usando regras baseadas"}
    
    def mark_error_resolved(self, error_type: str, resolution_method: str):
        """Marcar erro como resolvido."""
        with self._lock:
            resolved_count = 0
            for error in self.error_history:
                if (error.error_type == error_type and 
                    not error.resolved):
                    error.resolved = True
                    error.resolution_time = time.time()
                    error.resolution_method = resolution_method
                    resolved_count += 1
            
            self.metrics["errors_resolved"] += resolved_count
            
            if resolved_count > 0:
                self.logger.info(f"Marcados {resolved_count} erros como resolvidos "
                               f"via {resolution_method}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Obter resumo de erros."""
        with self._lock:
            # Calcular métricas
            total_errors = len(self.error_history)
            resolved_errors = sum(1 for e in self.error_history if e.resolved)
            
            # Erros mais comuns
            most_common = sorted(self.error_counts.items(), 
                               key=lambda x: x[1], reverse=True)[:5]
            
            # Taxa de erro por hora (últimas 24h)
            now = time.time()
            recent_errors = sum(1 for e in self.error_history 
                              if now - e.timestamp < 3600)
            
            return {
                "total_errors": total_errors,
                "resolved_errors": resolved_errors,
                "resolution_rate": resolved_errors / total_errors if total_errors > 0 else 0.0,
                "most_common_errors": most_common,
                "errors_by_severity": dict(self.error_severity_counts),
                "errors_per_hour": recent_errors,
                "recent_errors": [
                    {
                        "type": e.error_type,
                        "message": e.error_message,
                        "severity": e.severity.value,
                        "timestamp": e.timestamp,
                        "resolved": e.resolved
                    }
                    for e in list(self.error_history)[-10:]  # Últimos 10
                ]
            }
    
    def clear_error_history(self):
        """Limpar histórico de erros."""
        with self._lock:
            self.error_history.clear()
            self.error_counts.clear()
            self.error_severity_counts.clear()
            self.metrics = {
                "total_errors": 0,
                "errors_resolved": 0,
                "avg_resolution_time": 0.0,
                "most_common_errors": [],
                "error_rate_per_hour": 0.0
            }
            self.logger.info("Histórico de erros limpo")


# Decorator para tratamento automático de erros
def handle_errors(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 fallback: bool = True,
                 retry: bool = False,
                 max_retries: int = 2):
    """
    Decorator para tratamento automático de erros.
    
    Args:
        severity: Severidade padrão do erro
        category: Categoria padrão do erro
        fallback: Se deve tentar fallback
        retry: Se deve tentar retry
        max_retries: Número máximo de tentativas
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extrair contexto dos argumentos
            context = ErrorContext(
                component=func.__module__,
                operation=func.__name__
            )
            
            # Tentar extrair IDs dos argumentos
            for arg in args:
                if isinstance(arg, dict):
                    if "user_id" in arg:
                        context.user_id = arg["user_id"]
                    if "session_id" in arg:
                        context.session_id = arg["session_id"]
                    if "call_id" in arg:
                        context.call_id = arg["call_id"]
            
            # Verificar se error_handler está disponível
            try:
                from .application import get_application
                app = get_application()
                error_handler = getattr(app, 'error_handler', None)
            except:
                error_handler = None
            
            if error_handler and retry:
                # Usar retry automático
                return error_handler.retry_operation(
                    func.__name__, func, *args, context=context, **kwargs
                )
            
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                if error_handler:
                    # Usar tratamento centralizado
                    return error_handler.handle_error(
                        e, context, severity, category, fallback
                    )
                else:
                    # Fallback básico
                    logging.error(f"Erro em {func.__name__}: {e}")
                    return None
        
        return wrapper
    return decorator


# Instância global do ErrorHandler
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Obter instância global do ErrorHandler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def set_error_handler(error_handler: ErrorHandler):
    """Definir instância global do ErrorHandler."""
    global _error_handler
    _error_handler = error_handler 
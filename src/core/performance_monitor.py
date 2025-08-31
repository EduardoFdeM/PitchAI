"""
Sistema de Monitoramento de Performance
======================================

Identifica gargalos de performance e otimizações necessárias:
- Profiling de funções críticas
- Monitoramento de uso de recursos
- Análise de latência
- Detecção de memory leaks
"""

import time
import psutil
import threading
import functools
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import gc
import tracemalloc


class PerformanceMetric(Enum):
    """Tipos de métricas de performance."""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    CACHE_HIT_RATE = "cache_hit_rate"
    THREAD_COUNT = "thread_count"
    GARBAGE_COLLECTION = "garbage_collection"


@dataclass
class PerformanceRecord:
    """Registro de performance de uma operação."""
    operation: str
    component: str
    start_time: float
    end_time: float
    memory_before: int
    memory_after: int
    cpu_percent: float
    thread_count: int
    success: bool
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Alerta de performance."""
    timestamp: float
    metric: PerformanceMetric
    value: float
    threshold: float
    severity: str
    message: str
    component: str


class PerformanceMonitor:
    """Sistema de monitoramento de performance."""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Histórico de performance
        self.performance_history: deque = deque(maxlen=10000)
        self.operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0,
            "memory_avg": 0.0
        })
        
        # Alertas de performance
        self.alerts: deque = deque(maxlen=1000)
        self.thresholds = {
            PerformanceMetric.EXECUTION_TIME: 5.0,  # 5 segundos
            PerformanceMetric.MEMORY_USAGE: 500,    # 500 MB
            PerformanceMetric.CPU_USAGE: 80.0,      # 80%
            PerformanceMetric.THREAD_COUNT: 100,    # 100 threads
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Monitoramento de recursos do sistema
        self._monitoring = False
        self._monitor_thread = None
        self._system_stats = deque(maxlen=3600)  # 1 hora de dados
        
        # Profiling ativo
        self._profiling = False
        self._profile_data = {}
        
        # Memory leak detection
        self._memory_snapshots = deque(maxlen=100)
        
        self.logger.info("✅ PerformanceMonitor inicializado")
    
    def start_monitoring(self):
        """Iniciar monitoramento contínuo de recursos."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
        
        # Iniciar profiling de memória
        tracemalloc.start()
        
        self.logger.info("🔍 Monitoramento de performance iniciado")
    
    def stop_monitoring(self):
        """Parar monitoramento."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        tracemalloc.stop()
        self.logger.info("🛑 Monitoramento de performance parado")
    
    def _monitor_system_resources(self):
        """Monitorar recursos do sistema em background."""
        process = psutil.Process()
        
        while self._monitoring:
            try:
                # Coletar métricas do sistema
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = process.memory_info()
                thread_count = process.num_threads()
                
                # Verificar thresholds
                if cpu_percent > self.thresholds[PerformanceMetric.CPU_USAGE]:
                    self._create_alert(
                        PerformanceMetric.CPU_USAGE,
                        cpu_percent,
                        self.thresholds[PerformanceMetric.CPU_USAGE],
                        "high",
                        f"CPU usage high: {cpu_percent:.1f}%",
                        "system"
                    )
                
                if memory_info.rss / 1024 / 1024 > self.thresholds[PerformanceMetric.MEMORY_USAGE]:
                    self._create_alert(
                        PerformanceMetric.MEMORY_USAGE,
                        memory_info.rss / 1024 / 1024,
                        self.thresholds[PerformanceMetric.MEMORY_USAGE],
                        "high",
                        f"Memory usage high: {memory_info.rss / 1024 / 1024:.1f} MB",
                        "system"
                    )
                
                if thread_count > self.thresholds[PerformanceMetric.THREAD_COUNT]:
                    self._create_alert(
                        PerformanceMetric.THREAD_COUNT,
                        thread_count,
                        self.thresholds[PerformanceMetric.THREAD_COUNT],
                        "medium",
                        f"Thread count high: {thread_count}",
                        "system"
                    )
                
                # Armazenar snapshot
                snapshot = {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "thread_count": thread_count
                }
                
                with self._lock:
                    self._system_stats.append(snapshot)
                
                time.sleep(5)  # Coletar a cada 5 segundos
                
            except Exception as e:
                self.logger.error(f"Erro no monitoramento: {e}")
                time.sleep(10)
    
    def _create_alert(self, metric: PerformanceMetric, value: float, 
                     threshold: float, severity: str, message: str, component: str):
        """Criar alerta de performance."""
        alert = PerformanceAlert(
            timestamp=time.time(),
            metric=metric,
            value=value,
            threshold=threshold,
            severity=severity,
            message=message,
            component=component
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # Log do alerta
        if severity == "high":
            self.logger.warning(f"🚨 ALERTA DE PERFORMANCE: {message}")
        else:
            self.logger.info(f"⚠️ Alerta de performance: {message}")
    
    def profile_operation(self, operation: str, component: str = "unknown"):
        """Decorator para profiling de operações."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._profile_function(func, operation, component, *args, **kwargs)
            return wrapper
        return decorator
    
    def _profile_function(self, func: Callable, operation: str, component: str, 
                         *args, **kwargs) -> Any:
        """Profilar execução de função."""
        start_time = time.time()
        
        # Coletar métricas antes
        process = psutil.Process()
        memory_before = process.memory_info().rss
        cpu_percent = process.cpu_percent()
        thread_count = process.num_threads()
        
        # Executar função
        try:
            result = func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            # Coletar métricas depois
            end_time = time.time()
            memory_after = process.memory_info().rss
            
            # Criar registro
            record = PerformanceRecord(
                operation=operation,
                component=component,
                start_time=start_time,
                end_time=end_time,
                memory_before=memory_before,
                memory_after=memory_after,
                cpu_percent=cpu_percent,
                thread_count=thread_count,
                success=success,
                error_message=error_message
            )
            
            # Armazenar registro
            self._store_performance_record(record)
            
            # Verificar thresholds
            execution_time = end_time - start_time
            if execution_time > self.thresholds[PerformanceMetric.EXECUTION_TIME]:
                self._create_alert(
                    PerformanceMetric.EXECUTION_TIME,
                    execution_time,
                    self.thresholds[PerformanceMetric.EXECUTION_TIME],
                    "high" if execution_time > 10.0 else "medium",
                    f"Operation {operation} slow: {execution_time:.2f}s",
                    component
                )
        
        return result
    
    def _store_performance_record(self, record: PerformanceRecord):
        """Armazenar registro de performance."""
        with self._lock:
            # Adicionar ao histórico
            self.performance_history.append(record)
            
            # Atualizar estatísticas
            stats = self.operation_stats[record.operation]
            stats["count"] += 1
            stats["total_time"] += (record.end_time - record.start_time)
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["min_time"] = min(stats["min_time"], record.end_time - record.start_time)
            stats["max_time"] = max(stats["max_time"], record.end_time - record.start_time)
            
            if not record.success:
                stats["errors"] += 1
            
            # Média de memória
            memory_used = record.memory_after - record.memory_before
            stats["memory_avg"] = (stats["memory_avg"] * (stats["count"] - 1) + memory_used) / stats["count"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obter resumo de performance."""
        with self._lock:
            # Operações mais lentas
            slow_operations = sorted(
                self.operation_stats.items(),
                key=lambda x: x[1]["avg_time"],
                reverse=True
            )[:10]
            
            # Operações com mais erros
            error_operations = sorted(
                self.operation_stats.items(),
                key=lambda x: x[1]["errors"],
                reverse=True
            )[:10]
            
            # Alertas recentes
            recent_alerts = list(self.alerts)[-20:]
            
            # Métricas do sistema
            system_metrics = {}
            if self._system_stats:
                latest = self._system_stats[-1]
                system_metrics = {
                    "cpu_percent": latest["cpu_percent"],
                    "memory_mb": latest["memory_mb"],
                    "thread_count": latest["thread_count"]
                }
            
            return {
                "slow_operations": slow_operations,
                "error_operations": error_operations,
                "recent_alerts": [
                    {
                        "timestamp": alert.timestamp,
                        "metric": alert.metric.value,
                        "value": alert.value,
                        "severity": alert.severity,
                        "message": alert.message,
                        "component": alert.component
                    }
                    for alert in recent_alerts
                ],
                "system_metrics": system_metrics,
                "total_operations": sum(stats["count"] for stats in self.operation_stats.values()),
                "total_alerts": len(self.alerts)
            }
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detectar possíveis memory leaks."""
        if not tracemalloc.is_tracing():
            return []
        
        # Obter snapshot atual
        current_snapshot = tracemalloc.take_snapshot()
        
        with self._lock:
            self._memory_snapshots.append(current_snapshot)
        
        # Comparar com snapshot anterior
        if len(self._memory_snapshots) < 2:
            return []
        
        previous_snapshot = self._memory_snapshots[-2]
        
        # Encontrar diferenças
        top_stats = current_snapshot.compare_to(previous_snapshot, 'lineno')
        
        leaks = []
        for stat in top_stats[:10]:  # Top 10 diferenças
            if stat.size_diff > 1024 * 1024:  # Mais de 1MB de diferença
                leaks.append({
                    "file": stat.traceback.format()[-1],
                    "size_diff_mb": stat.size_diff / 1024 / 1024,
                    "count_diff": stat.count_diff
                })
        
        return leaks
    
    def optimize_memory(self):
        """Otimizar uso de memória."""
        # Forçar garbage collection
        collected = gc.collect()
        
        # Limpar caches se necessário
        if hasattr(self, '_clear_caches'):
            self._clear_caches()
        
        self.logger.info(f"🧹 Otimização de memória: {collected} objetos coletados")
    
    def get_recommendations(self) -> List[str]:
        """Obter recomendações de otimização."""
        recommendations = []
        
        with self._lock:
            # Verificar operações lentas
            for operation, stats in self.operation_stats.items():
                if stats["avg_time"] > 1.0:  # Mais de 1 segundo
                    recommendations.append(
                        f"Otimizar operação '{operation}': {stats['avg_time']:.2f}s médios"
                    )
                
                if stats["errors"] > stats["count"] * 0.1:  # Mais de 10% de erro
                    recommendations.append(
                        f"Corrigir erros em '{operation}': {stats['errors']}/{stats['count']} falhas"
                    )
            
            # Verificar uso de memória
            if self._system_stats:
                latest = self._system_stats[-1]
                if latest["memory_mb"] > 300:  # Mais de 300MB
                    recommendations.append(
                        f"Reduzir uso de memória: {latest['memory_mb']:.1f}MB"
                    )
            
            # Verificar threads
            if self._system_stats:
                latest = self._system_stats[-1]
                if latest["thread_count"] > 50:  # Mais de 50 threads
                    recommendations.append(
                        f"Reduzir número de threads: {latest['thread_count']}"
                    )
        
        return recommendations


# Instância global do PerformanceMonitor
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Obter instância global do PerformanceMonitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def profile_operation(operation: str, component: str = "unknown"):
    """Decorator global para profiling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            return monitor._profile_function(func, operation, component, *args, **kwargs)
        return wrapper
    return decorator 
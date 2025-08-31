"""
EventBus - Sistema de eventos pub/sub thread-safe
================================================

Gerenciamento centralizado de eventos para comunicação entre módulos.
"""

import logging
import threading
import time
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from queue import Queue, Empty

from .contracts import EventType


class EventBus:
    """Sistema de eventos pub/sub thread-safe."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._subscribers = defaultdict(list)
        self._lock = threading.RLock()
        self._event_queue = Queue()
        self._running = False
        self._worker_thread = None
        
        # Métricas
        self._event_count = 0
        self._subscriber_count = 0
    
    def start(self):
        """Iniciar worker thread para processamento de eventos."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()
        self.logger.info("✅ EventBus iniciado")
    
    def stop(self):
        """Parar worker thread."""
        if not self._running:
            return
        
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        self.logger.info("🛑 EventBus parado")
    
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Inscrever callback para um tipo de evento."""
        with self._lock:
            self._subscribers[event_type].append(callback)
            self._subscriber_count += 1
            self.logger.debug(f"📝 Inscrito em {event_type} (total: {len(self._subscribers[event_type])})")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Cancelar inscrição de callback."""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    self._subscriber_count -= 1
                    self.logger.debug(f"❌ Cancelado inscrição em {event_type}")
                except ValueError:
                    pass
    
    def publish(self, event_type: str, payload: Dict[str, Any]):
        """Publicar evento (thread-safe)."""
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": time.time(),
            "id": self._event_count
        }
        
        self._event_queue.put(event)
        self._event_count += 1
        
        # Log para eventos importantes
        if event_type in ["error", "system.status"]:
            self.logger.info(f"📢 {event_type}: {payload.get('message', payload)}")
        else:
            self.logger.debug(f"📢 {event_type}")
    
    def _process_events(self):
        """Worker thread para processar eventos."""
        while self._running:
            try:
                # Timeout para permitir parada graciosa
                event = self._event_queue.get(timeout=0.1)
                self._dispatch_event(event)
                self._event_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro no processamento de evento: {e}")
    
    def _dispatch_event(self, event: Dict[str, Any]):
        """Despachar evento para todos os subscribers com tratamento de erro robusto."""
        event_type = event["type"]
        payload = event["payload"]
        
        with self._lock:
            subscribers = self._subscribers[event_type].copy()
        
        # Executar callbacks com tratamento de erro robusto
        for callback in subscribers:
            try:
                # Verificar se callback ainda é válido
                if not callable(callback):
                    self.logger.warning(f"Callback inválido removido: {callback}")
                    self.unsubscribe(event_type, callback)
                    continue
                
                # Executar callback com timeout e retry
                self._execute_callback_safely(callback, payload, event_type)
                
            except Exception as e:
                self.logger.error(f"Erro crítico no callback de {event_type}: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _execute_callback_safely(self, callback: Callable, payload: Dict[str, Any], 
                                event_type: str, max_retries: int = 2):
        """Executar callback com retry e timeout."""
        import threading
        import time
        
        for attempt in range(max_retries + 1):
            try:
                # Executar com timeout de 30 segundos
                result = None
                exception = None
                
                def target():
                    nonlocal result, exception
                    try:
                        result = callback(payload)
                    except Exception as e:
                        exception = e
                
                thread = threading.Thread(target=target, daemon=True)
                thread.start()
                thread.join(timeout=30.0)
                
                if thread.is_alive():
                    # Timeout - tentar interromper thread
                    self.logger.warning(f"Timeout no callback {getattr(callback, '__name__', 'unknown')} "
                                      f"para evento {event_type}")
                    raise TimeoutError("Callback timeout")
                
                if exception:
                    raise exception
                
                # Sucesso
                if attempt > 0:
                    self.logger.info(f"Callback {getattr(callback, '__name__', 'unknown')} "
                                   f"executado com sucesso na tentativa {attempt + 1}")
                break
                
            except (TimeoutError, Exception) as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Backoff exponencial
                    self.logger.warning(f"Tentativa {attempt + 1} falhou para {event_type}, "
                                      f"aguardando {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou
                    self.logger.error(f"Callback {getattr(callback, '__name__', 'unknown')} "
                                    f"falhou após {max_retries + 1} tentativas para {event_type}: {e}")
                    
                    # Remover callback problemático se for muito problemático
                    if hasattr(callback, '_error_count'):
                        callback._error_count += 1
                        if callback._error_count > 5:
                            self.logger.warning(f"Removendo callback problemático: {callback}")
                            self.unsubscribe(event_type, callback)
                    else:
                        callback._error_count = 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas do EventBus."""
        with self._lock:
            return {
                "events_published": self._event_count,
                "active_subscribers": self._subscriber_count,
                "event_types": list(self._subscribers.keys()),
                "queue_size": self._event_queue.qsize(),
                "running": self._running
            }
    
    def clear_subscribers(self, event_type: Optional[str] = None):
        """Limpar subscribers (útil para testes)."""
        with self._lock:
            if event_type:
                if event_type in self._subscribers:
                    self._subscriber_count -= len(self._subscribers[event_type])
                    self._subscribers[event_type].clear()
            else:
                self._subscribers.clear()
                self._subscriber_count = 0


# Instância global do EventBus
event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Obter instância global do EventBus."""
    return event_bus


def publish_event(event_type: str, payload: Dict[str, Any]):
    """Publicar evento na instância global."""
    event_bus.publish(event_type, payload)


def subscribe_to_event(event_type: str, callback: Callable[[Dict[str, Any]], None]):
    """Inscrever em evento na instância global."""
    event_bus.subscribe(event_type, callback)


def unsubscribe_from_event(event_type: str, callback: Callable[[Dict[str, Any]], None]):
    """Cancelar inscrição em evento na instância global."""
    event_bus.unsubscribe(event_type, callback) 
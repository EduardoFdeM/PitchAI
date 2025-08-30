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
        """Despachar evento para todos os subscribers."""
        event_type = event["type"]
        payload = event["payload"]
        
        with self._lock:
            subscribers = self._subscribers[event_type].copy()
        
        # Executar callbacks em threads separadas para evitar bloqueio
        for callback in subscribers:
            try:
                # Executar callback diretamente (assumindo que é thread-safe)
                callback(payload)
            except Exception as e:
                self.logger.error(f"Erro no callback de {event_type}: {e}")
    
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
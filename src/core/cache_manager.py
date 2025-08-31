"""
Sistema de Cache Inteligente
===========================

Cache multi-nível com estratégias de eviction inteligentes:
- Cache em memória (LRU)
- Cache em disco (persistente)
- Cache distribuído (opcional)
- Prefetching inteligente
"""

import time
import json
import pickle
import hashlib
import threading
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from pathlib import Path
import sqlite3
import zlib


@dataclass
class CacheEntry:
    """Entrada de cache."""
    key: str
    value: Any
    timestamp: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None
    priority: int = 1  # 1-10, maior = mais importante


class CacheLevel:
    """Nível de cache abstrato."""
    
    def __init__(self, name: str, max_size: int = 1000):
        self.name = name
        self.max_size = max_size
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            priority: int = 1) -> bool:
        """Armazenar valor no cache."""
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        """Remover valor do cache."""
        raise NotImplementedError
    
    def clear(self):
        """Limpar cache."""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache."""
        return self.stats.copy()


class MemoryCache(CacheLevel):
    """Cache em memória com LRU."""
    
    def __init__(self, name: str, max_size: int = 1000, max_memory_mb: int = 100):
        super().__init__(name, max_size)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Verificar TTL
                if entry.ttl and time.time() > entry.timestamp + entry.ttl:
                    del self.cache[key]
                    self.stats["misses"] += 1
                    return None
                
                # Atualizar acesso
                entry.access_count += 1
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                return entry.value
            
            self.stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            priority: int = 1) -> bool:
        """Armazenar valor no cache."""
        with self.lock:
            # Calcular tamanho aproximado
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 1024  # Tamanho padrão
            
            # Verificar se cabe na memória
            if size_bytes > self.max_memory_bytes:
                return False
            
            # Criar entrada
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                size_bytes=size_bytes,
                ttl=ttl,
                priority=priority
            )
            
            # Eviction se necessário
            while (len(self.cache) >= self.max_size or 
                   self._get_total_size() + size_bytes > self.max_memory_bytes):
                self._evict_least_valuable()
            
            # Armazenar
            self.cache[key] = entry
            self.cache.move_to_end(key)
            self.stats["size"] = len(self.cache)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Remover valor do cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats["size"] = len(self.cache)
                return True
            return False
    
    def clear(self):
        """Limpar cache."""
        with self.lock:
            self.cache.clear()
            self.stats["size"] = 0
    
    def _get_total_size(self) -> int:
        """Obter tamanho total do cache."""
        return sum(entry.size_bytes for entry in self.cache.values())
    
    def _evict_least_valuable(self):
        """Evict entrada menos valiosa baseada em score."""
        if not self.cache:
            return
        
        # Calcular score para cada entrada
        scores = {}
        current_time = time.time()
        
        for key, entry in self.cache.items():
            # Score baseado em: prioridade, acesso recente, frequência de acesso
            age = current_time - entry.timestamp
            recency_score = 1.0 / (1.0 + age / 3600)  # Normalizar por hora
            frequency_score = min(entry.access_count / 10.0, 1.0)  # Normalizar por 10 acessos
            priority_score = entry.priority / 10.0
            
            # Score final (menor = menos valioso)
            score = (priority_score * 0.4 + 
                    recency_score * 0.3 + 
                    frequency_score * 0.3)
            
            scores[key] = score
        
        # Remover entrada com menor score
        least_valuable_key = min(scores.keys(), key=lambda k: scores[k])
        del self.cache[least_valuable_key]
        self.stats["evictions"] += 1


class DiskCache(CacheLevel):
    """Cache em disco com SQLite."""
    
    def __init__(self, name: str, cache_dir: Path, max_size_mb: int = 500):
        super().__init__(name, max_size_mb)
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / f"{name}.db"
        self.lock = threading.RLock()
        
        self._init_database()
    
    def _init_database(self):
        """Inicializar banco de dados SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    timestamp REAL,
                    access_count INTEGER DEFAULT 0,
                    size_bytes INTEGER,
                    ttl REAL,
                    priority INTEGER DEFAULT 1,
                    compressed INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON cache(priority)")
            conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT value, timestamp, ttl, compressed FROM cache WHERE key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    
                    if not row:
                        self.stats["misses"] += 1
                        return None
                    
                    value_blob, timestamp, ttl, compressed = row
                    
                    # Verificar TTL
                    if ttl and time.time() > timestamp + ttl:
                        self.delete(key)
                        self.stats["misses"] += 1
                        return None
                    
                    # Descomprimir se necessário
                    if compressed:
                        value_blob = zlib.decompress(value_blob)
                    
                    # Deserializar
                    value = pickle.loads(value_blob)
                    
                    # Atualizar contador de acesso
                    conn.execute(
                        "UPDATE cache SET access_count = access_count + 1 WHERE key = ?",
                        (key,)
                    )
                    conn.commit()
                    
                    self.stats["hits"] += 1
                    return value
                    
            except Exception as e:
                logging.error(f"Erro ao ler cache: {e}")
                self.stats["misses"] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            priority: int = 1) -> bool:
        """Armazenar valor no cache."""
        with self.lock:
            try:
                # Serializar valor
                value_blob = pickle.dumps(value)
                size_bytes = len(value_blob)
                
                # Comprimir se grande
                compressed = False
                if size_bytes > 1024:  # Comprimir se > 1KB
                    value_blob = zlib.compress(value_blob)
                    compressed = True
                    size_bytes = len(value_blob)
                
                # Verificar tamanho máximo
                if size_bytes > self.max_size * 1024 * 1024:
                    return False
                
                # Eviction se necessário
                self._evict_if_needed(size_bytes)
                
                # Armazenar
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache 
                        (key, value, timestamp, size_bytes, ttl, priority, compressed)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (key, value_blob, time.time(), size_bytes, ttl, priority, compressed))
                    conn.commit()
                
                self.stats["size"] += 1
                return True
                
            except Exception as e:
                logging.error(f"Erro ao escrever cache: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Remover valor do cache."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
                    deleted = cursor.rowcount > 0
                    if deleted:
                        self.stats["size"] = max(0, self.stats["size"] - 1)
                    return deleted
            except Exception as e:
                logging.error(f"Erro ao deletar cache: {e}")
                return False
    
    def clear(self):
        """Limpar cache."""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache")
                    conn.commit()
                self.stats["size"] = 0
            except Exception as e:
                logging.error(f"Erro ao limpar cache: {e}")
    
    def _evict_if_needed(self, new_size_bytes: int):
        """Evict entradas se necessário."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Calcular tamanho total
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache")
                total_size = cursor.fetchone()[0] or 0
                
                if total_size + new_size_bytes <= self.max_size * 1024 * 1024:
                    return
                
                # Remover entradas menos valiosas
                cursor = conn.execute("""
                    SELECT key, priority, access_count, timestamp 
                    FROM cache 
                    ORDER BY priority ASC, access_count ASC, timestamp ASC
                """)
                
                for row in cursor:
                    key, priority, access_count, timestamp = row
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    self.stats["evictions"] += 1
                    
                    # Recalcular tamanho
                    cursor2 = conn.execute("SELECT SUM(size_bytes) FROM cache")
                    total_size = cursor2.fetchone()[0] or 0
                    
                    if total_size + new_size_bytes <= self.max_size * 1024 * 1024:
                        break
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Erro na eviction: {e}")


class CacheManager:
    """Gerenciador de cache multi-nível."""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Níveis de cache
        self.levels: List[CacheLevel] = []
        
        # Cache de prefetch
        self.prefetch_cache: Dict[str, float] = {}
        self.prefetch_patterns: Dict[str, Callable] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Estatísticas
        self.stats = {
            "total_hits": 0,
            "total_misses": 0,
            "prefetch_hits": 0,
            "prefetch_misses": 0
        }
        
        self._setup_cache_levels()
        self.logger.info("✅ CacheManager inicializado")
    
    def _setup_cache_levels(self):
        """Configurar níveis de cache."""
        if not self.config:
            return
        
        cache_dir = self.config.app_dir / "cache"
        
        # Nível 1: Cache em memória (rápido, pequeno)
        memory_cache = MemoryCache(
            name="memory",
            max_size=1000,
            max_memory_mb=50
        )
        self.levels.append(memory_cache)
        
        # Nível 2: Cache em disco (lento, grande)
        disk_cache = DiskCache(
            name="disk",
            cache_dir=cache_dir,
            max_size_mb=500
        )
        self.levels.append(disk_cache)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obter valor do cache multi-nível."""
        with self.lock:
            # Tentar cada nível
            for i, level in enumerate(self.levels):
                value = level.get(key)
                if value is not None:
                    # Cache hit - promover para níveis superiores
                    self._promote_to_higher_levels(key, value, i)
                    self.stats["total_hits"] += 1
                    return value
            
            # Cache miss
            self.stats["total_misses"] += 1
            
            # Verificar prefetch
            if key in self.prefetch_cache:
                self.stats["prefetch_hits"] += 1
            else:
                self.stats["prefetch_misses"] += 1
            
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            priority: int = 1, level: Optional[int] = None) -> bool:
        """Armazenar valor no cache."""
        with self.lock:
            if level is not None:
                # Armazenar em nível específico
                if 0 <= level < len(self.levels):
                    return self.levels[level].set(key, value, ttl, priority)
                return False
            
            # Armazenar em todos os níveis (write-through)
            success = True
            for level_cache in self.levels:
                if not level_cache.set(key, value, ttl, priority):
                    success = False
            
            return success
    
    def delete(self, key: str) -> bool:
        """Remover valor de todos os níveis."""
        with self.lock:
            success = False
            for level in self.levels:
                if level.delete(key):
                    success = True
            return success
    
    def clear(self, level: Optional[int] = None):
        """Limpar cache."""
        with self.lock:
            if level is not None:
                if 0 <= level < len(self.levels):
                    self.levels[level].clear()
            else:
                for level_cache in self.levels:
                    level_cache.clear()
    
    def _promote_to_higher_levels(self, key: str, value: Any, current_level: int):
        """Promover valor para níveis superiores."""
        for i in range(current_level):
            self.levels[i].set(key, value)
    
    def register_prefetch_pattern(self, pattern: str, prefetch_func: Callable):
        """Registrar padrão de prefetch."""
        self.prefetch_patterns[pattern] = prefetch_func
        self.logger.debug(f"Padrão de prefetch registrado: {pattern}")
    
    def prefetch(self, key: str):
        """Executar prefetch para uma chave."""
        for pattern, prefetch_func in self.prefetch_patterns.items():
            if pattern in key:
                try:
                    prefetched_data = prefetch_func(key)
                    if prefetched_data:
                        self.set(key, prefetched_data, priority=5)
                        self.prefetch_cache[key] = time.time()
                except Exception as e:
                    self.logger.error(f"Erro no prefetch para {key}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache."""
        with self.lock:
            level_stats = []
            for i, level in enumerate(self.levels):
                stats = level.get_stats()
                stats["level"] = i
                stats["name"] = level.name
                level_stats.append(stats)
            
            return {
                **self.stats,
                "levels": level_stats,
                "prefetch_patterns": len(self.prefetch_patterns),
                "prefetch_cache_size": len(self.prefetch_cache)
            }
    
    def optimize(self):
        """Otimizar cache."""
        with self.lock:
            # Limpar entradas expiradas
            for level in self.levels:
                if hasattr(level, '_cleanup_expired'):
                    level._cleanup_expired()
            
            # Limpar prefetch cache antigo
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.prefetch_cache.items()
                if current_time - timestamp > 3600  # 1 hora
            ]
            for key in expired_keys:
                del self.prefetch_cache[key]
            
            self.logger.info("🧹 Cache otimizado")


# Instância global do CacheManager
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Obter instância global do CacheManager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cache_result(ttl: Optional[float] = None, priority: int = 1, key_prefix: str = ""):
    """Decorator para cachear resultado de função."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Gerar chave única
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # Tentar obter do cache
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl, priority)
            
            return result
        
        return wrapper
    return decorator 
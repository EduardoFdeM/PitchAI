"""
Teste das Otimizações de Performance
===================================

Testa as melhorias implementadas:
- Monitoramento de performance
- Cache inteligente
- Profiling de operações
- Otimizações de memória
"""

import sys
import time
import threading
import numpy as np
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import create_config
from core.performance_monitor import PerformanceMonitor, profile_operation
from core.cache_manager import CacheManager, cache_result


def test_performance_monitoring():
    """Testar monitoramento de performance."""
    print("🔍 Testando monitoramento de performance...")
    
    config = create_config()
    monitor = PerformanceMonitor(config)
    monitor.start_monitoring()
    
    # Simular operações lentas
    @profile_operation("slow_operation", "test")
    def slow_function():
        time.sleep(0.1)  # 100ms
        return "result"
    
    @profile_operation("fast_operation", "test")
    def fast_function():
        time.sleep(0.01)  # 10ms
        return "result"
    
    # Executar operações
    for i in range(10):
        slow_function()
        fast_function()
    
    # Aguardar monitoramento
    time.sleep(2)
    
    # Verificar métricas
    summary = monitor.get_performance_summary()
    print(f"   Operações monitoradas: {summary['total_operations']}")
    print(f"   Alertas gerados: {summary['total_alerts']}")
    
    # Verificar operações lentas
    slow_ops = summary['slow_operations']
    if slow_ops:
        print(f"   Operação mais lenta: {slow_ops[0][0]} ({slow_ops[0][1]['avg_time']:.3f}s)")
    
    # Verificar métricas do sistema
    system_metrics = summary['system_metrics']
    if system_metrics:
        print(f"   CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
        print(f"   Memória: {system_metrics.get('memory_mb', 0):.1f}MB")
        print(f"   Threads: {system_metrics.get('thread_count', 0)}")
    
    # Detectar memory leaks
    leaks = monitor.detect_memory_leaks()
    print(f"   Possíveis memory leaks: {len(leaks)}")
    
    # Obter recomendações
    recommendations = monitor.get_recommendations()
    print(f"   Recomendações: {len(recommendations)}")
    for rec in recommendations[:3]:
        print(f"     - {rec}")
    
    monitor.stop_monitoring()
    
    return summary['total_operations'] > 0


def test_cache_performance():
    """Testar performance do cache."""
    print("\n💾 Testando performance do cache...")
    
    config = create_config()
    cache_manager = CacheManager(config)
    
    # Testar cache de funções
    @cache_result(ttl=60, priority=8, key_prefix="test_cache")
    def expensive_function(param: str):
        time.sleep(0.05)  # Simular operação cara
        return f"result_{param}"
    
    # Primeira execução (cache miss)
    start_time = time.time()
    result1 = expensive_function("test1")
    time1 = (time.time() - start_time) * 1000
    
    # Segunda execução (cache hit)
    start_time = time.time()
    result2 = expensive_function("test1")
    time2 = (time.time() - start_time) * 1000
    
    print(f"   Primeira execução: {time1:.1f}ms")
    print(f"   Segunda execução (cache): {time2:.1f}ms")
    print(f"   Melhoria: {time1/time2:.1f}x mais rápido")
    
    # Verificar estatísticas
    stats = cache_manager.get_stats()
    print(f"   Cache hits: {stats['total_hits']}")
    print(f"   Cache misses: {stats['total_misses']}")
    
    # Testar diferentes níveis
    cache_manager.set("test_key", "test_value", ttl=30, priority=5)
    retrieved = cache_manager.get("test_key")
    print(f"   Cache get/set: {'✅' if retrieved == 'test_value' else '❌'}")
    
    return time2 < time1 * 0.5  # Cache deve ser pelo menos 2x mais rápido


def test_concurrent_performance():
    """Testar performance concorrente."""
    print("\n⚡ Testando performance concorrente...")
    
    config = create_config()
    monitor = PerformanceMonitor(config)
    monitor.start_monitoring()
    
    results = []
    lock = threading.Lock()
    
    @profile_operation("concurrent_operation", "test")
    def concurrent_function(thread_id: int):
        time.sleep(0.02)  # 20ms
        with lock:
            results.append(f"thread_{thread_id}")
        return f"result_{thread_id}"
    
    # Executar operações concorrentes
    threads = []
    start_time = time.time()
    
    for i in range(10):
        thread = threading.Thread(
            target=concurrent_function, 
            args=(i,),
            name=f"worker_{i}"
        )
        threads.append(thread)
        thread.start()
    
    # Aguardar conclusão
    for thread in threads:
        thread.join()
    
    total_time = (time.time() - start_time) * 1000
    
    print(f"   Tempo total: {total_time:.1f}ms")
    print(f"   Operações concluídas: {len(results)}")
    print(f"   Throughput: {len(results)/total_time*1000:.1f} ops/s")
    
    # Verificar métricas
    summary = monitor.get_performance_summary()
    system_metrics = summary['system_metrics']
    if system_metrics:
        print(f"   Threads ativos: {system_metrics.get('thread_count', 0)}")
    
    monitor.stop_monitoring()
    
    return len(results) == 10


def test_memory_optimization():
    """Testar otimização de memória."""
    print("\n🧹 Testando otimização de memória...")
    
    config = create_config()
    monitor = PerformanceMonitor(config)
    monitor.start_monitoring()
    
    # Simular uso de memória
    large_data = []
    
    @profile_operation("memory_operation", "test")
    def memory_intensive_function():
        # Alocar memória
        data = np.random.rand(1000, 1000)  # ~8MB
        large_data.append(data)
        time.sleep(0.01)
        return data.shape
    
    # Executar operações que consomem memória
    for i in range(5):
        memory_intensive_function()
    
    # Verificar uso de memória antes da otimização
    summary_before = monitor.get_performance_summary()
    system_before = summary_before['system_metrics']
    memory_before = system_before.get('memory_mb', 0) if system_before else 0
    
    print(f"   Memória antes: {memory_before:.1f}MB")
    
    # Otimizar memória
    monitor.optimize_memory()
    
    # Verificar uso de memória depois da otimização
    time.sleep(1)  # Aguardar garbage collection
    summary_after = monitor.get_performance_summary()
    system_after = summary_after['system_metrics']
    memory_after = system_after.get('memory_mb', 0) if system_after else 0
    
    print(f"   Memória depois: {memory_after:.1f}MB")
    print(f"   Diferença: {memory_before - memory_after:.1f}MB")
    
    # Detectar memory leaks
    leaks = monitor.detect_memory_leaks()
    print(f"   Memory leaks detectados: {len(leaks)}")
    
    monitor.stop_monitoring()
    
    return memory_after <= memory_before


def test_cache_intelligence():
    """Testar inteligência do cache."""
    print("\n🧠 Testando inteligência do cache...")
    
    config = create_config()
    cache_manager = CacheManager(config)
    
    # Simular padrões de acesso
    access_patterns = [
        "user_profile_123",
        "user_profile_123",  # Repetido
        "product_info_456",
        "user_profile_123",  # Repetido novamente
        "order_history_789",
        "product_info_456",  # Repetido
    ]
    
    @cache_result(ttl=300, priority=6, key_prefix="smart_cache")
    def smart_function(key: str):
        time.sleep(0.03)  # Simular operação cara
        return f"data_for_{key}"
    
    # Simular acessos
    for key in access_patterns:
        smart_function(key)
    
    # Verificar estatísticas
    stats = cache_manager.get_stats()
    hit_rate = stats['total_hits'] / (stats['total_hits'] + stats['total_misses']) if (stats['total_hits'] + stats['total_misses']) > 0 else 0
    
    print(f"   Total de acessos: {stats['total_hits'] + stats['total_misses']}")
    print(f"   Cache hits: {stats['total_hits']}")
    print(f"   Hit rate: {hit_rate:.1%}")
    
    # Testar prefetch
    cache_manager.prefetch("user_profile_124")  # Padrão similar
    
    # Verificar prefetch
    prefetch_stats = cache_manager.get_stats()
    print(f"   Prefetch patterns: {prefetch_stats['prefetch_patterns']}")
    print(f"   Prefetch cache size: {prefetch_stats['prefetch_cache_size']}")
    
    return hit_rate > 0.3  # Pelo menos 30% de hit rate


def main():
    """Executar todos os testes de performance."""
    print("🚀 Teste das Otimizações de Performance")
    print("=" * 50)
    
    try:
        # Teste 1: Monitoramento de performance
        monitoring_ok = test_performance_monitoring()
        
        # Teste 2: Performance do cache
        cache_ok = test_cache_performance()
        
        # Teste 3: Performance concorrente
        concurrent_ok = test_concurrent_performance()
        
        # Teste 4: Otimização de memória
        memory_ok = test_memory_optimization()
        
        # Teste 5: Inteligência do cache
        intelligence_ok = test_cache_intelligence()
        
        # Resumo
        print("\n📊 Resumo dos Testes:")
        print(f"   Monitoramento: {'✅' if monitoring_ok else '❌'}")
        print(f"   Cache Performance: {'✅' if cache_ok else '❌'}")
        print(f"   Performance Concorrente: {'✅' if concurrent_ok else '❌'}")
        print(f"   Otimização de Memória: {'✅' if memory_ok else '❌'}")
        print(f"   Inteligência do Cache: {'✅' if intelligence_ok else '❌'}")
        
        all_passed = all([monitoring_ok, cache_ok, concurrent_ok, memory_ok, intelligence_ok])
        
        if all_passed:
            print("\n🎉 Todas as otimizações de performance estão funcionando!")
            print("✅ Sistema mais rápido e eficiente")
        else:
            print("\n⚠️ Algumas otimizações precisam de ajustes")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
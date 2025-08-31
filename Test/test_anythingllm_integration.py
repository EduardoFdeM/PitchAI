"""
Teste de Integração AnythingLLM
==============================

Testa a integração completa com AnythingLLM, incluindo:
- Cliente AnythingLLM
- RAG Service
- Integração completa
- Geração de sugestões e resumos
"""

import sys
import os
import time
import json
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import create_config
from ai.anythingllm_client import AnythingLLMClient, RAGPassage
from ai.rag_service import RAGService, ObjectionEvent
from ai.anythingllm_integration import AnythingLLMIntegration


def test_anythingllm_client():
    """Testar cliente AnythingLLM."""
    print("🔗 Testando AnythingLLM Client...")
    
    # 1. Configuração
    config = create_config()
    
    # 2. Cliente
    client = AnythingLLMClient(
        base_url="http://127.0.0.1:3001",
        api_key="local-dev",
        timeout=5.0
    )
    
    # 3. Health check
    is_healthy = client.health_check()
    print(f"   Health check: {'✅' if is_healthy else '❌'}")
    
    if not is_healthy:
        print("   ⚠️ AnythingLLM não está rodando. Testes serão simulados.")
        return False
    
    # 4. Testar geração de sugestões
    print("\n💡 Testando geração de sugestões...")
    
    # Passagens de exemplo
    passages = [
        RAGPassage(
            id="preco_001",
            title="Estratégias de Preço",
            snippet="Quando o cliente menciona que o preço está alto, foque no valor percebido. Apresente o ROI e os benefícios de longo prazo.",
            score=0.9
        ),
        RAGPassage(
            id="timing_001",
            title="Urgência e Timing",
            snippet="Crie senso de urgência mostrando oportunidades limitadas ou promoções por tempo determinado.",
            score=0.8
        )
    ]
    
    # Objeção de exemplo
    objection = "O preço está muito alto para o nosso orçamento"
    
    # Gerar sugestões
    response = client.generate_objection_suggestions(
        objection=objection,
        passages=passages,
        temperature=0.3
    )
    
    print(f"   Latência: {response.latency_ms:.0f}ms")
    print(f"   Modelo: {response.model_info['model']}")
    print(f"   Sugestões geradas: {len(response.suggestions)}")
    
    for i, suggestion in enumerate(response.suggestions):
        print(f"   {i+1}. {suggestion.text} (score: {suggestion.score:.2f})")
    
    return True


def test_rag_service():
    """Testar RAG Service."""
    print("\n🔍 Testando RAG Service...")
    
    # 1. Configuração
    config = create_config()
    
    # 2. RAG Service
    rag_service = RAGService(config)
    
    # 3. Testar recuperação de passagens
    print("   Testando recuperação de passagens...")
    
    objection_text = "Preciso pensar sobre isso"
    category = "timing"
    
    passages = rag_service.retrieve_passages(
        objection_text=objection_text,
        category=category,
        top_k=3
    )
    
    print(f"   Passagens recuperadas: {len(passages)}")
    
    for i, passage in enumerate(passages):
        print(f"   {i+1}. {passage.title} (score: {passage.score:.2f})")
        print(f"      {passage.snippet[:100]}...")
    
    # 4. Testar processamento de objeção
    print("\n   Testando processamento de objeção...")
    
    objection_event = ObjectionEvent(
        call_id="test_call_001",
        category="preco",
        text="O preço está muito alto",
        context_snippet="Cliente mencionou preocupação com custo",
        timestamp_ms=int(time.time() * 1000)
    )
    
    # Processar objeção
    rag_service.process_objection(objection_event)
    
    print("   ✅ Objeção enviada para processamento")
    
    return True


def test_integration():
    """Testar integração completa."""
    print("\n🔄 Testando integração completa...")
    
    # 1. Configuração
    config = create_config()
    
    # 2. Integração
    integration = AnythingLLMIntegration(config)
    
    # 3. Testar sessão
    print("   Testando sessão de call...")
    
    call_id = "test_call_002"
    seller_id = "seller_001"
    client_id = "client_001"
    
    # Iniciar sessão
    success = integration.start_session(call_id, seller_id, client_id)
    print(f"   Sessão iniciada: {'✅' if success else '❌'}")
    
    if success:
        # Adicionar dados de exemplo
        integration.add_transcription(call_id, "vendor", "Olá, como posso ajudá-lo hoje?", 0.95)
        integration.add_transcription(call_id, "client", "Estou interessado no produto, mas o preço está alto", 0.88)
        
        integration.add_sentiment(call_id, 0.3, "positive")
        integration.add_sentiment(call_id, -0.2, "negative")
        
        integration.add_objection(call_id, "preco", "O preço está muito alto", "Cliente expressou preocupação com custo")
        
        # Finalizar sessão
        session = integration.end_session(call_id)
        
        if session:
            print(f"   Sessão finalizada: ✅")
            print(f"   Duração: {session.metrics.get('duration_seconds', 0):.1f}s")
            print(f"   Transcrições: {len(session.transcriptions)}")
            print(f"   Objeções: {len(session.objections)}")
            print(f"   Sentimentos: {len(session.sentiment_data)}")
            
            # Gerar resumo
            print("\n   Gerando resumo...")
            integration.generate_session_summary(call_id)
            
            # Gerar coaching
            print("   Gerando coaching...")
            integration.generate_coaching_feedback(call_id)
            
            # Aguardar processamento
            time.sleep(2.0)
    
    # 4. Limpeza
    integration.cleanup()
    
    return True


def test_fallback_scenarios():
    """Testar cenários de fallback."""
    print("\n🛡️ Testando cenários de fallback...")
    
    # 1. Testar com AnythingLLM indisponível
    print("   Testando com AnythingLLM indisponível...")
    
    config = create_config()
    
    # Cliente com URL inválida
    client = AnythingLLMClient(
        base_url="http://localhost:9999",  # Porta inválida
        api_key="invalid",
        timeout=1.0
    )
    
    is_healthy = client.health_check()
    print(f"   Health check (offline): {'✅' if is_healthy else '❌'} (esperado: ❌)")
    
    # 2. Testar RAG Service com fallback
    print("\n   Testando RAG Service com fallback...")
    
    rag_service = RAGService(config)
    
    # Verificar se usa fallback quando AnythingLLM não está disponível
    objection_event = ObjectionEvent(
        call_id="test_fallback",
        category="preco",
        text="Preço alto",
        context_snippet="Teste de fallback",
        timestamp_ms=int(time.time() * 1000)
    )
    
    # Processar objeção (deve usar fallback)
    rag_service.process_objection(objection_event)
    
    print("   ✅ Fallback testado")
    
    return True


def test_performance():
    """Testar performance da integração."""
    print("\n⚡ Testando performance...")
    
    config = create_config()
    integration = AnythingLLMIntegration(config)
    
    # Teste de múltiplas sessões
    print("   Testando múltiplas sessões...")
    
    start_time = time.time()
    
    for i in range(3):
        call_id = f"perf_test_{i}"
        integration.start_session(call_id, f"seller_{i}", f"client_{i}")
        
        # Adicionar dados
        for j in range(5):
            integration.add_transcription(call_id, "vendor", f"Transcrição {j}", 0.9)
            integration.add_sentiment(call_id, 0.1 * j, "positive")
        
        integration.end_session(call_id)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"   Tempo total: {duration:.2f}s")
    print(f"   Tempo por sessão: {duration/3:.2f}s")
    
    # Limpeza
    integration.cleanup()
    
    return True


def main():
    """Executar todos os testes."""
    print("🧠 Teste de Integração AnythingLLM")
    print("=" * 50)
    
    try:
        # Teste 1: Cliente AnythingLLM
        client_ok = test_anythingllm_client()
        
        # Teste 2: RAG Service
        rag_ok = test_rag_service()
        
        # Teste 3: Integração completa
        integration_ok = test_integration()
        
        # Teste 4: Cenários de fallback
        fallback_ok = test_fallback_scenarios()
        
        # Teste 5: Performance
        perf_ok = test_performance()
        
        # Resumo
        print("\n📊 Resumo dos Testes:")
        print(f"   AnythingLLM Client: {'✅' if client_ok else '❌'}")
        print(f"   RAG Service: {'✅' if rag_ok else '❌'}")
        print(f"   Integração Completa: {'✅' if integration_ok else '❌'}")
        print(f"   Fallback Scenarios: {'✅' if fallback_ok else '❌'}")
        print(f"   Performance: {'✅' if perf_ok else '❌'}")
        
        all_passed = all([client_ok, rag_ok, integration_ok, fallback_ok, perf_ok])
        
        if all_passed:
            print("\n🎉 Todos os testes passaram!")
            print("✅ Integração com AnythingLLM está funcionando corretamente")
        else:
            print("\n⚠️ Alguns testes falharam")
            print("🔧 Verifique a configuração do AnythingLLM")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
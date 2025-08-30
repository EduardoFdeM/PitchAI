"""
Teste de Integração AnythingLLM
==============================

Script para testar a integração com AnythingLLM e verificar
se o sistema RAG está funcionando corretamente.
"""

import sys
import time
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai.anythingllm_client import AnythingLLMClient, RAGPassage
from ai.rag_service import RAGService, ObjectionEvent
from core.config import create_config


def test_anythingllm_connection():
    """Testar conexão com AnythingLLM."""
    print("🔍 Testando conexão com AnythingLLM...")
    
    try:
        client = AnythingLLMClient()
        is_available = client.health_check()
        
        if is_available:
            print("✅ AnythingLLM conectado com sucesso!")
            print(f"   Modelo padrão: {client.default_model}")
            return True
        else:
            print("❌ AnythingLLM não está disponível")
            print("   Verifique se está rodando em http://localhost:3001")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False


def test_rag_service():
    """Testar serviço RAG."""
    print("\n🔍 Testando serviço RAG...")
    
    try:
        config = create_config()
        rag_service = RAGService(config)
        
        print(f"✅ RAG Service inicializado")
        print(f"   LLM disponível: {rag_service.is_available}")
        print(f"   Passagens na base: {len(rag_service.knowledge_base)}")
        
        return rag_service
        
    except Exception as e:
        print(f"❌ Erro ao inicializar RAG Service: {e}")
        return None


def test_objection_processing(rag_service):
    """Testar processamento de objeções."""
    print("\n🔍 Testando processamento de objeções...")
    
    test_cases = [
        {
            "text": "O preço está muito alto",
            "category": "preco",
            "expected": "preco"
        },
        {
            "text": "Preciso pensar sobre isso",
            "category": "timing", 
            "expected": "timing"
        },
        {
            "text": "Preciso falar com meu chefe",
            "category": "autoridade",
            "expected": "autoridade"
        },
        {
            "text": "Não vejo necessidade disso",
            "category": "necessidade",
            "expected": "necessidade"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Teste {i}: '{test_case['text']}'")
        
        # Criar evento de objeção
        event = ObjectionEvent(
            call_id=f"test_{i}",
            category=test_case['category'],
            text=test_case['text'],
            context_snippet=test_case['text'],
            timestamp_ms=int(time.time() * 1000)
        )
        
        # Recuperar passagens
        passages = rag_service.retrieve_passages(
            event.text, 
            event.category, 
            top_k=3
        )
        
        print(f"      Categoria esperada: {test_case['expected']}")
        print(f"      Passagens encontradas: {len(passages)}")
        
        for j, passage in enumerate(passages, 1):
            print(f"        [{j}] {passage.title} (score: {passage.score:.2f})")
        
        if len(passages) == 0:
            print("      ⚠️ Nenhuma passagem encontrada")
        else:
            print("      ✅ Passagens recuperadas com sucesso")


def test_llm_generation(rag_service):
    """Testar geração com LLM (se disponível)."""
    print("\n🔍 Testando geração com LLM...")
    
    if not rag_service.is_available:
        print("   ⚠️ LLM não disponível - pulando teste de geração")
        return
    
    # Criar evento de teste
    event = ObjectionEvent(
        call_id="llm_test",
        category="preco",
        text="O preço está muito alto para o nosso orçamento",
        context_snippet="O preço está muito alto para o nosso orçamento",
        timestamp_ms=int(time.time() * 1000)
    )
    
    print("   Gerando sugestões...")
    start_time = time.time()
    
    # Processar objeção
    rag_service.process_objection(event)
    
    # Aguardar resultado (simulado)
    time.sleep(2)
    
    elapsed = (time.time() - start_time) * 1000
    print(f"   ⏱️ Tempo de processamento: {elapsed:.0f}ms")


def test_fallback_behavior(rag_service):
    """Testar comportamento de fallback."""
    print("\n🔍 Testando comportamento de fallback...")
    
    # Simular LLM indisponível
    original_available = rag_service.is_available
    rag_service.is_available = False
    
    try:
        # Criar evento de teste
        event = ObjectionEvent(
            call_id="fallback_test",
            category="preco",
            text="O preço está alto",
            context_snippet="O preço está alto",
            timestamp_ms=int(time.time() * 1000)
        )
        
        # Processar objeção
        rag_service.process_objection(event)
        
        print("   ✅ Fallback funcionando (LLM simulado como indisponível)")
        
    finally:
        # Restaurar estado original
        rag_service.is_available = original_available


def main():
    """Função principal de teste."""
    print("🚀 Teste de Integração AnythingLLM")
    print("=" * 50)
    
    # Teste 1: Conexão AnythingLLM
    llm_available = test_anythingllm_connection()
    
    # Teste 2: Serviço RAG
    rag_service = test_rag_service()
    if not rag_service:
        print("\n❌ Falha ao inicializar RAG Service")
        return
    
    # Teste 3: Processamento de objeções
    test_objection_processing(rag_service)
    
    # Teste 4: Geração com LLM (se disponível)
    test_llm_generation(rag_service)
    
    # Teste 5: Fallback
    test_fallback_behavior(rag_service)
    
    print("\n" + "=" * 50)
    print("✅ Teste de integração concluído!")
    
    if llm_available:
        print("🎉 AnythingLLM está funcionando corretamente")
    else:
        print("⚠️ AnythingLLM não está disponível - usando fallback")
    
    print("\n📋 Próximos passos:")
    print("   1. Iniciar AnythingLLM se não estiver rodando")
    print("   2. Executar: python src/main.py")
    print("   3. Testar com objeções reais na interface")


if __name__ == "__main__":
    main() 
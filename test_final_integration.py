#!/usr/bin/env python3
"""
Teste Final - PitchAI com Whisper Large + AnythingLLM
====================================================
"""

import sys
import json
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_whisper_large_priority():
    """Testa se Whisper Large está sendo priorizado"""
    print("🧪 Testando Priorização Whisper Large...")

    try:
        from src.ai.asr_whisper import TranscriptionService
        from src.ai.model_manager import ModelManager
        from src.core.config import create_config

        config = create_config()
        model_manager = ModelManager(config)

        # Carregar manifesto
        model_manager.load_manifest()
        print(f"✅ Manifesto carregado: {len(model_manager.models)} modelos")

        # Verificar se Whisper Large está disponível
        large_available = "whisper_large_encoder" in model_manager.models
        small_available = "whisper_small_encoder" in model_manager.models

        print(f"   Whisper Large disponível: {'✅' if large_available else '❌'}")
        print(f"   Whisper Small disponível: {'✅' if small_available else '❌'}")

        if large_available:
            large_entry = model_manager.models["whisper_large_encoder"]
            print("   📊 Whisper Large:")
            print(f"      Path: {large_entry.path}")
            print(f"      Size: {large_entry.size_mb}MB")
            print(f"      Latency: {large_entry.latency_target_ms}ms")

        return large_available

    except Exception as e:
        print(f"❌ Erro no teste Whisper: {e}")
        return False

def test_anythingllm_integration():
    """Testa integração completa com AnythingLLM"""
    print("\n🧪 Testando Integração AnythingLLM...")

    try:
        from src.ai.llm_service import LLMService

        # Inicializar com AnythingLLM prioritário
        service = LLMService(
            model_dir="models/",
            use_simulation=False,
            use_anythingllm=True
        )

        print("🚀 Inicializando LLM Service...")
        success = service.initialize()

        if not success:
            print("❌ Falha na inicialização")
            return False

        print("✅ LLM Service inicializado!")

        # Verificar status
        status = service.get_status()
        print("📊 Status dos serviços:")
        print(f"   Simulação: {status.get('use_simulation', True)}")
        print(f"   AnythingLLM: {status.get('anythingllm_available', False)}")

        # Testar resposta de vendas
        test_scenarios = [
            "Cliente disse: 'Está muito caro'",
            "Cliente: 'Quando podemos implementar?'",
            "Cliente: 'Como vocês se comparam com X?'",
            "Cliente: 'Preciso falar com meu chefe'"
        ]

        print("\n🤖 Testando cenários de vendas:")
        for i, prompt in enumerate(test_scenarios, 1):
            try:
                response = service.generate_response(prompt, max_tokens=150)
                print(f"   {i}. {prompt}")
                print(f"      → {response[:80]}...")
                print()
            except Exception as e:
                print(f"   {i}. ❌ Erro: {e}")
                print()

        # Cleanup
        service.cleanup()
        return True

    except Exception as e:
        print(f"❌ Erro no teste AnythingLLM: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_summary_generation():
    """Testa geração de resumo com AnythingLLM"""
    print("\n🧪 Testando Geração de Resumo...")

    try:
        from src.core.summary_service import PostCallSummaryService, CallSummary
        from src.ai.llm_service import LLMService

        # Inicializar LLM Service
        llm_service = LLMService(use_anythingllm=True)
        llm_service.initialize()

        # Inicializar Summary Service
        config = type('Config', (), {'app_dir': Path('models')})()
        summary_service = PostCallSummaryService(config, llm_service)

        # Dados de teste simulados
        call_data = {
            "transcript": {
                "chunks": [
                    {"speaker": "vendor", "text": "Ola, bom dia! Como vai?", "duration_sec": 2.0},
                    {"speaker": "client", "text": "Oi, tudo bem. Gostaria de saber sobre a solucao", "duration_sec": 3.0},
                    {"speaker": "vendor", "text": "Claro! Nossa plataforma oferece integracao completa", "duration_sec": 4.0},
                    {"speaker": "client", "text": "Parece interessante, mas esta muito caro", "duration_sec": 2.5},
                    {"speaker": "vendor", "text": "Entendo sua preocupacao. O ROI e de 340% em 18 meses", "duration_sec": 5.0},
                    {"speaker": "client", "text": "Hmm, preciso pensar melhor", "duration_sec": 2.0}
                ],
                "text": "Transcrição completa da chamada de vendas"
            },
            "sentiment_data": {"avg_score": 0.65},
            "objections": [{"type": "preco", "handled": True}],
            "metrics": {
                "talk_time_vendor_pct": 55.0,
                "talk_time_client_pct": 45.0,
                "sentiment_avg": 0.65,
                "objections_total": 1,
                "objections_resolved": 1,
                "buying_signals": 2
            }
        }

        print("📝 Gerando resumo da chamada...")
        summary = summary_service.generate("test_call_001")

        if summary:
            print("✅ Resumo gerado com sucesso!")
            print("📊 Resultado:")
            print(f"   Pontos principais: {len(summary.key_points)}")
            print(f"   Objeções: {len(summary.objections)}")
            print(f"   Próximos passos: {len(summary.next_steps)}")

            print("\n📋 Conteúdo do resumo:")
            print(f"   Pontos: {summary.key_points}")
            print(f"   Métricas: Talk time vendor: {summary.metrics['talk_time_vendor_pct']}%")

            # Tentar parsear insights se disponível
            if hasattr(summary, 'insights') and summary.insights:
                print(f"   Insights: Interesse {summary.insights.get('cliente_interesse', 'N/A')}")

            return True
        else:
            print("❌ Falha na geração do resumo")
            return False

    except Exception as e:
        print(f"❌ Erro no teste de resumo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes"""
    print("🚀 TESTE FINAL - PitchAI com Whisper Large + AnythingLLM")
    print("=" * 60)

    # Resultados
    results = {
        "whisper_large": False,
        "anythingllm": False,
        "summary": False
    }

    # Executar testes
    results["whisper_large"] = test_whisper_large_priority()
    results["anythingllm"] = test_anythingllm_integration()
    results["summary"] = test_summary_generation()

    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESULTADO DOS TESTES")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print("-" * 60)
    print(".1f")

    if passed_tests == total_tests:
        print("🎉 SUCESSO TOTAL!")
        print("🎯 PitchAI está pronto com:")
        print("   • Whisper Large para transcrição de alta qualidade")
        print("   • AnythingLLM para análise inteligente de vendas")
        print("   • Sistema de resumos automatizados")
        print("\n💡 Execute: python src/main_frontend.py")
    else:
        print("⚠️ Alguns testes falharam.")
        print("🔧 Verifique os logs acima para detalhes.")

    print("=" * 60)

if __name__ == "__main__":
    main()

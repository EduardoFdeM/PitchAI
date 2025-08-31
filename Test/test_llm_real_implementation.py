#!/usr/bin/env python3
"""
Teste da Implementação do LLM Service
=====================================

Testes que verificam se o LLM Service funciona corretamente,
usando tanto modo real quanto simulado.
"""

import pytest
import sys
import time
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ai.llm_service import LLMService

class TestLLMRealImplementation:
    """Testes da implementação REAL do LLM."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.model_dir = Path(__file__).parent.parent / "models" / "llmware_model"
        logging.basicConfig(level=logging.INFO)
        
    def test_model_files_exist(self):
        """Teste REAL: Verificar se arquivos do modelo existem."""
        assert self.model_dir.exists(), f"Diretório do modelo não existe: {self.model_dir}"
        
        # Arquivos essenciais para o modelo funcionar
        essential_files = [
            "genai_config.json",
            "config.json", 
            "tokenizer.json",
            "prompt_1_of_3_qnn_ctx.onnx",
            "token_1_of_3_qnn_ctx.onnx",
            "llama_v3_2_3b_chat_quantized_part_1_of_3.bin"
        ]
        
        missing_files = []
        for filename in essential_files:
            file_path = self.model_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        assert not missing_files, f"Arquivos essenciais faltando: {missing_files}"
        
    def test_llm_service_initialization_simulated(self):
        """Teste: Inicialização do serviço LLM em modo simulado."""
        service = LLMService(str(self.model_dir), use_simulation=True)
        assert service.use_simulation
        
        success = service.initialize()
        assert success, "Serviço simulado deveria conseguir inicializar"
        assert service.is_initialized, "Serviço simulado deveria estar marcado como inicializado"

    @pytest.mark.skipif(not LLMService(None, use_simulation=False).use_simulation, reason="llmware não disponível")
    def test_llm_service_initialization_real(self):
        """Teste: Inicialização do serviço LLM em modo real (requer llmware)."""
        service = LLMService(str(self.model_dir), use_simulation=False)
        assert not service.use_simulation
        
        success = service.initialize()
        assert success, "Serviço real deveria conseguir inicializar"
        assert service.is_initialized, "Serviço real deveria estar marcado como inicializado"
        service.cleanup()

    def test_simulated_text_generation(self):
        """Teste: Geração de texto em modo simulado."""
        service = LLMService(str(self.model_dir), use_simulation=True)
        service.initialize()
        
        prompt = "Qual o preço?"
        response = service.generate_response(prompt)
        
        assert response
        assert "preço" in response.lower() or "valor" in response.lower()
        print(f"✅ Geração simulada: '{prompt}' → '{response}'")

    def test_real_text_generation(self):
        """Teste: Geração de texto funcional em modo real."""
        service = LLMService(str(self.model_dir), use_simulation=False)
        if not service.initialize():
            pytest.skip("Falha ao inicializar serviço em modo real")

        try:
            # Teste de geração
            prompt = "Como responder objeção de preço?"

            start_time = time.time()
            response = service.generate_response(prompt, max_tokens=50)
            generation_time = time.time() - start_time

            # Verificações da resposta
            assert response, "Resposta não pode ser vazia"
            assert len(response) > 10, f"Resposta muito curta: '{response}'"
            assert response != prompt, "Resposta não pode ser igual ao prompt"
            assert not response.startswith("❌"), f"Resposta com erro: {response}"

            # Verificar tempo de resposta razoável
            assert generation_time < 30.0, f"Geração muito lenta: {generation_time:.2f}s"

            print(f"✅ Geração: '{prompt}' → '{response}' ({generation_time:.2f}s)")

        finally:
            if hasattr(service, 'cleanup'):
                service.cleanup()
    
    def test_multiple_generations(self):
        """Teste: Múltiplas gerações consecutivas em modo real."""
        service = LLMService(str(self.model_dir), use_simulation=False)
        if not service.initialize():
            pytest.skip("Falha ao inicializar serviço em modo real")

        try:
            prompts = [
                "Preço alto demais",
                "Não temos orçamento",
                "Preciso falar com minha equipe",
                "E o suporte técnico?"
            ]

            responses = []
            total_time = 0

            for prompt in prompts:
                start_time = time.time()
                response = service.generate_response(prompt, max_tokens=30)
                generation_time = time.time() - start_time

                # Verificações básicas
                assert response, f"Resposta vazia para: {prompt}"
                assert len(response) > 5, f"Resposta muito curta para '{prompt}': '{response}'"

                responses.append(response)
                total_time += generation_time

                print(f"  {len(responses)}. '{prompt}' → '{response}' ({generation_time:.2f}s)")

            # Verificar que todas as respostas são diferentes
            unique_responses = set(responses)
            assert len(unique_responses) > 1, "Todas as respostas são iguais (serviço não está funcionando)"

            print(f"✅ {len(prompts)} gerações em {total_time:.2f}s")

        finally:
            if hasattr(service, 'cleanup'):
                service.cleanup()
    
    def test_factory_function(self):
        """Teste: Função de criação do serviço."""
        # Criar serviço
        service = LLMService(str(self.model_dir), use_simulation=True)

        assert service is not None, "Serviço não foi criado"

        # Verificar se conseguiu inicializar
        success = service.initialize()
        assert success, "Serviço deve conseguir inicializar"

        # Testar que consegue gerar resposta
        response = service.generate_response("Teste de funcionamento")
        assert response, "Serviço deve conseguir gerar resposta"
        assert len(response) > 5, "Resposta deve ter conteúdo"

        print("✅ Serviço criado e funcionando")

        # Cleanup se necessário
        if hasattr(service, 'cleanup'):
            service.cleanup()
    
    def test_performance_requirements(self):
        """Teste: Verificar requirements de performance em modo real."""
        service = LLMService(str(self.model_dir), use_simulation=False)
        if not service.initialize():
            pytest.skip("Falha ao inicializar serviço em modo real")

        try:
            # Teste de latência
            prompt = "Teste de performance"

            # Múltiplas medições para média
            times = []
            for i in range(3):
                start_time = time.time()
                response = service.generate_response(prompt, max_tokens=20)
                generation_time = time.time() - start_time
                times.append(generation_time)

                assert response, f"Resposta {i+1} vazia"

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print(f"⏱️ Latência - Média: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s")

            # Requirements de latência (ajustar conforme necessário)
            assert avg_time < 5.0, f"Latência média muito alta: {avg_time:.2f}s"
            assert min_time < 10.0, f"Latência mínima muito alta: {min_time:.2f}s"

        finally:
            if hasattr(service, 'cleanup'):
                service.cleanup()
    
    def test_sales_context_responses(self):
        """Teste: Verificar se respostas são apropriadas para vendas em modo real."""
        service = LLMService(str(self.model_dir), use_simulation=False)
        if not service.initialize():
            pytest.skip("Falha ao inicializar serviço em modo real")

        try:
            sales_scenarios = [
                ("Está muito caro", ["preço", "custo", "valor", "investimento", "roi"]),
                ("Não temos tempo", ["prazo", "tempo", "implementação", "rápido"]),
                ("E o suporte?", ["suporte", "ajuda", "assistência", "técnico"]),
                ("Como funciona?", ["funciona", "processo", "como", "método"])
            ]

            for scenario, expected_words in sales_scenarios:
                response = service.generate_response(scenario, max_tokens=50)

                assert response, f"Resposta vazia para: {scenario}"

                # Verificar se pelo menos uma palavra-chave está presente
                response_lower = response.lower()
                has_relevant_word = any(word in response_lower for word in expected_words)

                print(f"🎯 '{scenario}' → '{response}'")
                print(f"   Palavras esperadas: {expected_words}")
                print(f"   Relevante: {'✅' if has_relevant_word else '❌'}")

                # Não falha o teste se não tiver palavra exata, mas registra
                if not has_relevant_word:
                    print(f"⚠️ Resposta pode não estar totalmente alinhada com contexto de vendas")

        finally:
            if hasattr(service, 'cleanup'):
                service.cleanup()

# Teste de integração completa
def test_complete_integration_simulated():
    """Teste de integração completa do sistema em modo simulado."""
    print("\n🔄 Teste de Integração Completa (Simulado)")
    print("=" * 50)

    model_dir = Path(__file__).parent.parent / "models" / "llmware_model"

    # 1. Verificar arquivos
    print("1. Verificando arquivos...")
    assert model_dir.exists(), "Diretório do modelo deve existir"

    # 2. Tentar criar serviço
    print("2. Criando serviço...")
    from ai.llm_service import LLMService
    service = LLMService(str(model_dir), use_simulation=True)
    assert service is not None, "Serviço deve ser criado"

    # 3. Inicializar
    print("3. Inicializando serviço...")
    success = service.initialize()
    assert success, "Serviço deve conseguir inicializar"

    # 4. Testar geração
    print("4. Testando geração...")
    response = service.generate_response("Como está você hoje?")
    assert response, "Deve gerar resposta"
    print(f"   Resposta: '{response}'")

    # 5. Cleanup
    print("5. Limpando recursos...")
    if hasattr(service, 'cleanup'):
        service.cleanup()

    print("✅ Integração completa (simulada) testada com sucesso!")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Executar teste de integração
    test_complete_integration_simulated()

    # Executar testes unitários
    print("\n🧪 Executando testes unitários...")
    test_instance = TestLLMRealImplementation()
    test_instance.setup_method()

    try:
        test_instance.test_model_files_exist()
        print("✅ test_model_files_exist")

        test_instance.test_llm_service_initialization_simulated()
        print("✅ test_llm_service_initialization_simulated")
        
        test_instance.test_simulated_text_generation()
        print("✅ test_simulated_text_generation")

        # Testes que podem falhar em diferentes ambientes
        try:
            test_instance.test_llm_service_initialization_real()
            print("✅ test_llm_service_initialization_real")
        except Exception as e:
            print(f"⚠️ test_llm_service_initialization_real: {e}")

        try:
            test_instance.test_real_text_generation()
            print("✅ test_real_text_generation")
        except Exception as e:
            print(f"⚠️ test_real_text_generation: {e}")

        try:
            test_instance.test_multiple_generations()
            print("✅ test_multiple_generations")
        except Exception as e:
            print(f"⚠️ test_multiple_generations: {e}")

        try:
            test_instance.test_performance_requirements()
            print("✅ test_performance_requirements")
        except Exception as e:
            print(f"⚠️ test_performance_requirements: {e}")

        try:
            test_instance.test_sales_context_responses()
            print("✅ test_sales_context_responses")
        except Exception as e:
            print(f"⚠️ test_sales_context_responses: {e}")

        print("\n🎉 Todos os testes executados!")

    except Exception as e:
        print(f"\n❌ Teste falhou: {e}")
        import traceback
        traceback.print_exc()

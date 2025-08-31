#!/usr/bin/env python3
"""
Testes de Integração para LLMService
===================================

Testes para o novo LLMService integrado com LLMWare.
"""

import pytest
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai.llm_service import LLMService

class TestLLMServiceIntegration:
    """Testes de integração para o LLMService."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.model_dir = Path(__file__).parent.parent / "models" / "llmware_model"
    
    def test_llm_service_initialization_simulated(self):
        """Teste: Inicialização do serviço LLM em modo simulado."""
        service = LLMService(use_simulation=True)
        
        success = service.initialize()
        assert success, "Serviço simulado deveria conseguir inicializar"
        assert service.is_initialized, "Serviço simulado deveria estar marcado como inicializado"
        assert service.use_simulation, "Deveria estar em modo simulado"
        
        service.cleanup()

    def test_llm_service_initialization_auto_fallback(self):
        """Teste: Inicialização com fallback automático para simulação."""
        service = LLMService(use_simulation=False)  # Tenta modo real
        
        success = service.initialize()
        assert success, "Serviço deveria conseguir inicializar (com fallback)"
        assert service.is_initialized, "Serviço deveria estar marcado como inicializado"
        
        service.cleanup()

    def test_llm_service_generation_simulated(self):
        """Teste: Geração de resposta em modo simulado."""
        service = LLMService(use_simulation=True)
        service.initialize()
        
        response = service.generate_response("Como lidar com objeção de preço?", max_tokens=50)
        assert response, "Resposta não pode estar vazia"
        assert isinstance(response, str), "Resposta deve ser string"
        assert "simulada" in response.lower(), "Resposta simulada deveria indicar que é simulação"
        
        service.cleanup()

    def test_llm_service_conversation_history(self):
        """Teste: Funcionalidade de histórico de conversa."""
        service = LLMService(use_simulation=True)
        service.initialize()
        
        # Primeira interação
        response1 = service.generate_response("Olá", include_history=True)
        assert len(service.conversation_history) == 1
        
        # Segunda interação (com histórico)
        response2 = service.generate_response("Como você está?", include_history=True)
        assert len(service.conversation_history) == 2
        
        # Terceira interação (sem histórico)
        response3 = service.generate_response("Tchau", include_history=False)
        assert len(service.conversation_history) == 2  # Não deve ter aumentado
        
        service.cleanup()

    def test_llm_service_clear_history(self):
        """Teste: Limpeza do histórico de conversa."""
        service = LLMService(use_simulation=True)
        service.initialize()
        
        # Adicionar algumas mensagens ao histórico
        service.generate_response("Primeira mensagem", include_history=True)
        service.generate_response("Segunda mensagem", include_history=True)
        assert len(service.conversation_history) == 2
        
        # Limpar histórico
        service.clear_history()
        assert len(service.conversation_history) == 0
        
        service.cleanup()

    def test_llm_service_cleanup(self):
        """Teste: Limpeza de recursos do serviço."""
        service = LLMService(use_simulation=True)
        service.initialize()
        
        # Adicionar histórico
        service.generate_response("Teste", include_history=True)
        assert service.is_initialized
        assert len(service.conversation_history) > 0
        
        # Fazer cleanup
        service.cleanup()
        
        # Verificar se foi limpo corretamente
        assert not service.is_initialized
        assert len(service.conversation_history) == 0

    def test_llm_service_status(self):
        """Teste: Status do serviço."""
        service = LLMService(use_simulation=True)
        
        # Status antes da inicialização
        status = service.get_status()
        assert not status["is_initialized"]
        assert status["use_simulation"]
        assert status["conversation_length"] == 0
        
        # Inicializar e testar novamente
        service.initialize()
        service.generate_response("Teste", include_history=True)
        
        status = service.get_status()
        assert status["is_initialized"]
        assert status["conversation_length"] == 1
        
        service.cleanup()

    def test_llm_service_multiple_generations(self):
        """Teste: Múltiplas gerações em sequência."""
        service = LLMService(use_simulation=True)
        service.initialize()
        
        prompts = [
            "Como responder à objeção de preço?",
            "O cliente disse que precisa pensar. O que fazer?",
            "Como identificar o decisor na empresa?"
        ]
        
        responses = []
        for prompt in prompts:
            response = service.generate_response(prompt, max_tokens=50, include_history=True)
            responses.append(response)
            assert response, f"Resposta para '{prompt}' não pode estar vazia"
        
        # Verificar histórico
        assert len(service.conversation_history) == 3
        
        # Verificar se todas as respostas são diferentes (alta probabilidade)
        assert len(set(responses)) > 1, "Respostas deveriam ter alguma variação"
        
        service.cleanup()

    def test_llm_service_error_handling(self):
        """Teste: Tratamento de erros."""
        service = LLMService(use_simulation=True)
        
        # Tentar gerar sem inicializar
        response = service.generate_response("Teste")
        assert "não inicializado" in response.lower()
        
        # Inicializar e testar novamente
        service.initialize()
        response = service.generate_response("Teste válido")
        assert "não inicializado" not in response.lower()
        
        service.cleanup()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

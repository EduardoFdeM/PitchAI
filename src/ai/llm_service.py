"""
LLM Service - Serviço Unificado para Llama 3.2 3B
=================================================

Serviço principal para interação com o modelo Llama 3.2 3B,
usando a integração LLMWare específica do PitchAI.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Importar integrações LLM
try:
    from .anythingllm_client import AnythingLLMClient, AnythingLLMConfig
    ANYTHINGLLM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AnythingLLM Client não disponível: {e}")
    ANYTHINGLLM_AVAILABLE = False
    AnythingLLMClient = None

# Importar a integração LLMWare específica (fallback)
try:
    sys.path.append(str(Path(__file__).parent.parent.parent / "models"))
    from llmware_model.pitchai_llmware_integration import LLMWareService
    LLMWARE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LLMWare não disponível: {e}")
    LLMWARE_AVAILABLE = False
    LLMWareService = None

class LLMService:
    """Serviço unificado para modelos LLM usando AnythingLLM como prioridade."""

    def __init__(self, model_dir: str = None, use_simulation: bool = False, use_anythingllm: bool = True):
        """
        Inicializa o serviço LLM.

        Args:
            model_dir: Diretório do modelo (usado para localizar modelos)
            use_simulation: Se True, usa simulação; se False, tenta usar modelos reais
            use_anythingllm: Se True, prioriza AnythingLLM sobre outros providers
        """
        self.model_dir = model_dir
        self.use_simulation = use_simulation
        self.use_anythingllm = use_anythingllm
        self.logger = logging.getLogger(__name__)

        # Serviços disponíveis
        self.anythingllm_client = None
        self.llmware_service = None

        self.is_initialized = False
        self.conversation_history = []

        # Configurações
        self.anythingllm_config = AnythingLLMConfig(
            offline_mode=True,  # Sempre offline para PitchAI
            model_name="llama-3.2-3b-instruct"
        )

    def initialize(self) -> bool:
        """Inicializa o serviço LLM."""
        try:
            if self.use_simulation:
                self.logger.info("🔄 Inicializando LLM em modo simulado")
                self.is_initialized = True
                return True

            # Estratégia de inicialização: AnythingLLM primeiro, depois fallbacks
            self.logger.info("🔄 Inicializando serviços LLM...")

            # 1. Tentar AnythingLLM (prioridade)
            if self.use_anythingllm and ANYTHINGLLM_AVAILABLE:
                try:
                    self.logger.info("🔄 Tentando inicializar AnythingLLM...")
                    self.anythingllm_client = AnythingLLMClient(self.anythingllm_config)

                    if self.anythingllm_client.initialize():
                        self.is_initialized = True
                        self.logger.info("✅ AnythingLLM inicializado com sucesso!")
                        return True
                    else:
                        self.logger.warning("⚠️ AnythingLLM falhou na inicialização")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro no AnythingLLM: {e}")

            # 2. Tentar LLMWare (fallback)
            if LLMWARE_AVAILABLE:
                try:
                    self.logger.info("🔄 Tentando inicializar LLMWare...")
                    self.llmware_service = LLMWareService()

                    if self.llmware_service.initialize():
                        self.is_initialized = True
                        self.logger.info("✅ LLMWare Service inicializado com sucesso!")
                        return True
                    else:
                        self.logger.warning("⚠️ LLMWare falhou na inicialização")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro no LLMWare: {e}")

            # 3. Último recurso: simulação
            self.logger.warning("⚠️ Nenhum serviço LLM conseguiu inicializar, usando simulação")
            self.use_simulation = True
            self.is_initialized = True
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro geral na inicialização: {e}")
            # Fallback para simulação em caso de erro
            self.use_simulation = True
            self.is_initialized = True
            return True

    def generate_response(self, prompt: str, max_tokens: int = 256, include_history: bool = True) -> str:
        """
        Gera resposta usando o modelo.

        Args:
            prompt: Texto de entrada
            max_tokens: Número máximo de tokens para gerar
            include_history: Se deve incluir histórico da conversa

        Returns:
            Resposta gerada pelo modelo
        """
        if not self.is_initialized:
            return "❌ Serviço não inicializado"

        try:
            # Construir prompt com histórico se solicitado
            full_prompt = self._build_prompt_with_history(prompt) if include_history else prompt

            # Estratégia de geração: AnythingLLM primeiro
            if self.anythingllm_client and not self.use_simulation:
                try:
                    self.logger.debug("🤖 Gerando resposta com AnythingLLM...")
                    response_obj = self.anythingllm_client.generate_response(
                        prompt=full_prompt,
                        max_tokens=max_tokens
                    )
                    response = response_obj.text

                    # Log de performance
                    self.logger.debug(f"📊 AnythingLLM: {response_obj.processing_time_ms:.1f}ms, "
                                    f"confiança: {response_obj.confidence:.2f}")

                except Exception as e:
                    self.logger.warning(f"⚠️ Erro no AnythingLLM, tentando fallback: {e}")
                    response = None

            # Fallback para LLMWare
            if response is None and self.llmware_service and not self.use_simulation:
                try:
                    self.logger.debug("🤖 Gerando resposta com LLMWare...")
                    response = self.llmware_service.generate_response(full_prompt, max_tokens)
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro no LLMWare: {e}")
                    response = None

            # Último fallback: simulação
            if response is None or self.use_simulation:
                self.logger.debug("🤖 Gerando resposta simulada...")
                response = self._generate_simulation_response(prompt)

            # Adicionar ao histórico
            if include_history and response:
                self.conversation_history.append({"user": prompt, "assistant": response})
                # Limitar histórico para não crescer indefinidamente
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]

            return response

        except Exception as e:
            self.logger.error(f"❌ Erro na geração: {e}")
            return f"❌ Erro: {str(e)}"

    def _build_prompt_with_history(self, prompt: str) -> str:
        """Constrói prompt incluindo histórico da conversa."""
        if not self.conversation_history:
            return prompt
        
        history_text = ""
        for entry in self.conversation_history[-5:]:  # Últimas 5 interações
            history_text += f"Usuário: {entry['user']}\nAssistente: {entry['assistant']}\n\n"
        
        return f"Histórico da conversa:\n{history_text}Nova pergunta: {prompt}"

    def _generate_simulation_response(self, prompt: str) -> str:
        """Gera resposta simulada para desenvolvimento/teste."""
        import random
        
        responses = [
            f"💡 Baseado em '{prompt[:30]}...', sugiro abordar o ROI direto.",
            f"🎯 Para a situação mencionada, recomendo focar nos benefícios de longo prazo.",
            f"📊 Analisando o contexto, a melhor estratégia seria evidenciar o valor agregado.",
            f"🔍 Considerando a objeção, sugiro apresentar cases de sucesso similares.",
            f"⚡ Para superar essa barreira, foque na urgência da solução."
        ]
        
        base_response = random.choice(responses)
        return f"{base_response}\n\n🤖 (Resposta simulada - modelo real não carregado)"

    def clear_history(self):
        """Limpa o histórico da conversa."""
        self.conversation_history = []
        self.logger.info("🧹 Histórico da conversa limpo")

    def cleanup(self):
        """Limpa recursos do serviço."""
        try:
            # Limpar AnythingLLM
            if self.anythingllm_client and hasattr(self.anythingllm_client, 'cleanup'):
                self.anythingllm_client.cleanup()

            # Limpar LLMWare
            if self.llmware_service and hasattr(self.llmware_service, 'cleanup'):
                self.llmware_service.cleanup()

            self.clear_history()
            self.is_initialized = False
            self.logger.info("🧹 LLMService limpo")

        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do serviço."""
        status = {
            "is_initialized": self.is_initialized,
            "use_simulation": self.use_simulation,
            "anythingllm_available": ANYTHINGLLM_AVAILABLE,
            "llmware_available": LLMWARE_AVAILABLE,
            "conversation_length": len(self.conversation_history)
        }

        # Informações específicas dos serviços
        if self.anythingllm_client:
            status["anythingllm_stats"] = self.anythingllm_client.get_stats()

        return status



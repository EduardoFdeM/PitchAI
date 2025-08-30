import asyncio
import json
from typing import Optional, Dict, Any
from .npu_manager import NPUManager

class LocalLLMService:
    """Serviço LLM local rodando na NPU"""
    
    def __init__(self, npu_manager: NPUManager):
        self.npu_manager = npu_manager
        self.model_loaded = False
        
    async def initialize(self):
        """Inicializa o modelo LLM na NPU"""
        if not self.model_loaded:
            await self.npu_manager.load_llm_model("llama-3.1-8b")
            self.model_loaded = True
    
    async def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Gera resposta do LLM local"""
        await self.initialize()
        
        # Preparar prompt para o modelo
        formatted_prompt = self._format_prompt(prompt)
        
        # Executar na NPU
        response = await self.npu_manager.generate_text(
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            temperature=0.3,  # Baixa temperatura para respostas consistentes
            top_p=0.9
        )
        
        return response
    
    def _format_prompt(self, prompt: str) -> str:
        """Formata prompt para o modelo específico"""
        # Adicionar instruções específicas para JSON
        system_prompt = """Você é um assistente especializado em análise de chamadas de vendas. 
        Sua tarefa é gerar resumos estruturados em formato JSON válido.
        Sempre responda apenas com o JSON solicitado, sem texto adicional."""
        
        return f"{system_prompt}\n\n{prompt}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço LLM"""
        try:
            await self.initialize()
            return {
                "status": "healthy",
                "model_loaded": self.model_loaded,
                "npu_available": self.npu_manager.is_available()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_loaded": self.model_loaded
            }

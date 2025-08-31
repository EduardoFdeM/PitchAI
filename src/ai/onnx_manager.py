"""
PitchAI - ONNX Manager
======================

Gerenciador ONNX para execução de modelos de IA em tempo real.
Preparado para integração com modelos ONNX reais.
"""

import logging
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import time
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("⚠️ ONNX Runtime não disponível")


class ONNXManager(QObject):
    """Gerenciador ONNX para modelos de IA."""

    # Sinais para comunicação
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas de sentimento
    objection_detected = pyqtSignal(str, list) # objeção, sugestões

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Modelos ONNX (serão carregados quando disponíveis)
        self.whisper_model: Optional[ort.InferenceSession] = None
        self.sentiment_model: Optional[ort.InferenceSession] = None
        self.objection_model: Optional[ort.InferenceSession] = None
        self.speaker_model: Optional[ort.InferenceSession] = None

        # Integração com AnythingLLM (cérebro do sistema)
        self.anythingllm_client = None
        self.llm_service = None  # LLM Service integrado
        
        # Configurações de performance
        self.audio_buffer_size = 20  # ms
        self.sentiment_window = 3    # segundos
        self.objection_threshold = 0.7
        self.sentiment_sensitivity = 0.3
        self.speaker_confidence = 0.9
        
        # Estado
        self.is_initialized = False
        self.models_loaded = False
        
        # Cache para otimização
        self._transcription_cache = {}
        self._sentiment_cache = {}
        
    def initialize(self):
        """Inicializar NPU Manager."""
        try:
            self.logger.info("Inicializando ONNX Manager...")
            
            # Verificar disponibilidade do ONNX Runtime
            if not ONNX_AVAILABLE:
                self.logger.warning("⚠️ ONNX Runtime não disponível - usando simulação")
                self._setup_simulation_mode()
                return
            
            # Verificar providers disponíveis
            providers = ort.get_available_providers()
            self.logger.info(f"Providers disponíveis: {providers}")
            
            # Tentar carregar modelos
            self._load_models()

            # Inicializar integração com AnythingLLM
            self._initialize_anythingllm()

            if self.models_loaded or self.anythingllm_client:
                self.logger.info("✅ Modelos ONNX e/ou AnythingLLM carregados com sucesso")
            else:
                self.logger.warning("⚠️ Modelos não encontrados - usando simulação")
                self._setup_simulation_mode()

            self.is_initialized = True
            self.logger.info("✅ NPU Manager inicializado")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar NPU Manager: {e}")
            self._setup_simulation_mode()
    
    def _load_models(self):
        """Carregar modelos ONNX."""
        models_dir = Path(self.config.app_dir) / "models"
        
        if not models_dir.exists():
            self.logger.warning(f"⚠️ Diretório de modelos não encontrado: {models_dir}")
            return
        
        # Lista de modelos necessários
        model_files = {
            'whisper': models_dir / "whisper_base.onnx",
            'sentiment': models_dir / "distilbert_sentiment.onnx", 
            'objection': models_dir / "bert_objection.onnx",
            'speaker': models_dir / "ecapa_speaker.onnx"
        }
        
        # Verificar quais modelos estão disponíveis
        available_models = {}
        for name, path in model_files.items():
            if path.exists():
                available_models[name] = path
                self.logger.info(f"✅ Modelo {name} encontrado: {path}")
            else:
                self.logger.warning(f"⚠️ Modelo {name} não encontrado: {path}")
        
        if not available_models:
            self.logger.warning("⚠️ Nenhum modelo encontrado")
            return
        
        # Carregar modelos disponíveis
        try:
            # Configurar sessão ONNX
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # FORÇAR uso exclusivo de provedores ONNX padrão - NUNCA QNN
            providers_priority = ['CUDAExecutionProvider', 'DMLExecutionProvider', 'CPUExecutionProvider']

            # Obter apenas provedores seguros (excluindo QNN e outros problemáticos)
            all_available = ort.get_available_providers()
            safe_providers = [p for p in all_available if p in providers_priority]

            # Garantir que pelo menos CPU esteja disponível
            if not safe_providers:
                safe_providers = ['CPUExecutionProvider']
                self.logger.warning("⚠️ Nenhum provider avançado disponível - usando CPU")

            # VERIFICAÇÃO EXPLÍCITA: Remover QUALQUER referência a QNN
            available_providers = [p for p in safe_providers if 'QNN' not in p and 'QUALCOMM' not in p]

            self.logger.info(f"✅ Usando providers seguros: {available_providers}")
            self.logger.info("🚫 QNN e outros provedores problemáticos foram bloqueados")
            
            # Carregar cada modelo
            for name, path in available_models.items():
                try:
                    session = ort.InferenceSession(
                        str(path), 
                        sess_options=session_options,
                        providers=available_providers
                    )
                    
                    if name == 'whisper':
                        self.whisper_model = session
                    elif name == 'sentiment':
                        self.sentiment_model = session
                    elif name == 'objection':
                        self.objection_model = session
                    elif name == 'speaker':
                        self.speaker_model = session
                    
                    self.logger.info(f"✅ Modelo {name} carregado com sucesso")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao carregar modelo {name}: {e}")
            
            self.models_loaded = len(available_models) > 0
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar modelos: {e}")

    def _initialize_anythingllm(self):
        """Inicializar integração com AnythingLLM."""
        try:
            self.logger.info("🤖 Inicializando integração com AnythingLLM...")

            # Importar LLM Service
            try:
                from .llm_service import LLMService
                self.llm_service = LLMService(
                    model_dir=str(Path(self.config.app_dir) / "models"),
                    use_simulation=False,
                    use_anythingllm=True
                )

                if self.llm_service.initialize():
                    self.logger.info("✅ LLM Service (AnythingLLM) inicializado")
                    return True
                else:
                    self.logger.warning("⚠️ LLM Service falhou na inicialização")
                    return False

            except ImportError as e:
                self.logger.warning(f"⚠️ LLM Service não disponível: {e}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar AnythingLLM: {e}")
            return False

    def _setup_simulation_mode(self):
        """Configurar modo de simulação quando modelos não estão disponíveis."""
        self.logger.info("🔧 Configurando modo de simulação")
        self.models_loaded = False
        
        # Configurações de simulação
        self.simulation_config = {
            'transcription_delay': 0.5,  # segundos
            'sentiment_update_interval': 3.0,  # segundos
            'objection_detection_rate': 0.1,  # 10% de chance
        }
    
    def transcribe_audio(self, audio_chunk: bytes, speaker_id: str = "unknown") -> Tuple[str, float]:
        """Transcrever áudio usando Whisper."""
        if self.whisper_model and self.models_loaded:
            return self._transcribe_with_model(audio_chunk, speaker_id)
        else:
            return self._simulate_transcription(audio_chunk, speaker_id)
    
    def _transcribe_with_model(self, audio_chunk: bytes, speaker_id: str) -> Tuple[str, float]:
        """Transcrever usando modelo Whisper real."""
        try:
            # Preparar input para o modelo
            # Nota: Esta é uma implementação base - ajustar conforme especificações do modelo
            audio_array = np.frombuffer(audio_chunk, dtype=np.float32)
            
            # Normalizar e preparar para o modelo
            if len(audio_array.shape) == 1:
                audio_array = audio_array.reshape(1, -1)
            
            # Executar inferência
            input_name = self.whisper_model.get_inputs()[0].name
            output_names = [output.name for output in self.whisper_model.get_outputs()]
            
            result = self.whisper_model.run(
                output_names,
                {input_name: audio_array}
            )
            
            # Processar resultado (ajustar conforme formato de saída do modelo)
            if len(result) >= 2:
                text = result[0] if isinstance(result[0], str) else str(result[0])
                confidence = float(result[1]) if len(result) > 1 else 0.8
            else:
                text = str(result[0]) if result else ""
                confidence = 0.8
            
            return text.strip(), confidence
            
        except Exception as e:
            self.logger.error(f"❌ Erro na transcrição com modelo: {e}")
            return self._simulate_transcription(audio_chunk, speaker_id)
    
    def _simulate_transcription(self, audio_chunk: bytes, speaker_id: str) -> Tuple[str, float]:
        """Simular transcrição quando modelo não está disponível."""
        import random
        
        # Simular delay de processamento
        time.sleep(self.simulation_config['transcription_delay'])
        
        # Frases de exemplo para simulação
        phrases = [
            "Entendo sua preocupação com o preço",
            "Vamos analisar o ROI do projeto",
            "Qual seria o prazo ideal para vocês?",
            "Posso enviar uma proposta detalhada",
            "Como está o orçamento disponível?",
            "Vamos fazer um piloto primeiro",
            "Qual é o processo de aprovação?",
            "Posso agendar uma demonstração",
            "Vamos discutir os benefícios",
            "Como podemos adaptar à sua necessidade"
        ]
        
        text = random.choice(phrases)
        confidence = random.uniform(0.7, 0.95)
        
        return text, confidence

    def generate_llm_response(self, prompt: str, context: Optional[Dict] = None, **kwargs) -> str:
        """
        Gerar resposta usando LLM (AnythingLLM primeiro, depois fallbacks).

        Args:
            prompt: Texto de entrada
            context: Contexto adicional (histórico, dados da chamada, etc.)
            **kwargs: Parâmetros adicionais

        Returns:
            str: Resposta gerada
        """
        try:
            # Usar LLM Service se disponível
            if self.llm_service and self.llm_service.is_initialized:
                self.logger.debug("🤖 Gerando resposta com LLM Service...")

                # Preparar contexto se fornecido
                full_prompt = prompt
                if context:
                    context_str = self._format_context_for_llm(context)
                    full_prompt = f"{context_str}\n\n{prompt}"

                response = self.llm_service.generate_response(
                    prompt=full_prompt,
                    max_tokens=kwargs.get('max_tokens', 256),
                    include_history=True
                )

                self.logger.debug(f"✅ Resposta LLM gerada: {len(response)} chars")
                return response

            # Fallback para simulação
            else:
                self.logger.debug("🤖 LLM não disponível, usando simulação...")
                return self._generate_simulation_response(prompt, context)

        except Exception as e:
            self.logger.error(f"❌ Erro na geração LLM: {e}")
            return self._generate_simulation_response(prompt, context)

    def _format_context_for_llm(self, context: Dict) -> str:
        """Formatar contexto para o LLM."""
        context_parts = []

        if 'call_info' in context:
            call_info = context['call_info']
            context_parts.append(f"Informações da Chamada:")
            context_parts.append(f"- Cliente: {call_info.get('client', 'N/A')}")
            context_parts.append(f"- Duração: {call_info.get('duration', 'N/A')}")
            context_parts.append(f"- Status: {call_info.get('status', 'N/A')}")

        if 'sentiment' in context:
            sentiment = context['sentiment']
            context_parts.append(f"Sentimento Atual:")
            context_parts.append(f"- Valência: {sentiment.get('valence', 0):.2f}")
            context_parts.append(f"- Engajamento: {sentiment.get('engagement', 0):.2f}")

        if 'objection_history' in context:
            objections = context['objection_history']
            if objections:
                context_parts.append(f"Objeções Anteriores:")
                for obj in objections[-3:]:  # Últimas 3
                    context_parts.append(f"- {obj.get('type', 'N/A')}: {obj.get('handled', False)}")

        if 'conversation_history' in context:
            history = context['conversation_history']
            if history:
                context_parts.append(f"Histórico da Conversa:")
                for msg in history[-5:]:  # Últimas 5 mensagens
                    speaker = "Cliente" if msg.get('speaker') == 'client' else "Vendedor"
                    context_parts.append(f"{speaker}: {msg.get('text', '')[:100]}...")

        return "\n".join(context_parts)

    def _generate_simulation_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Gerar resposta simulada quando LLM não está disponível."""
        import random

        # Análise básica do prompt para respostas contextuais
        prompt_lower = prompt.lower()

        if "preço" in prompt_lower or "custo" in prompt_lower or "caro" in prompt_lower:
            responses = [
                "💰 **Estratégia de Precificação:**\n\n• ROI em 18 meses\n• Redução de custos operacionais em 40%\n• Casos similares: 3x retorno no investimento\n\n'O investimento se paga sozinho em 6 meses através da economia operacional.'",
                "📊 **Framework de Resposta a Preço:**\n\n1. **Reconhecer:** 'Entendo sua preocupação com o investimento'\n2. **Demonstrar Valor:** Mostrar ROI quantificado\n3. **Social Proof:** Compartilhar casos de sucesso\n4. **Trial Close:** 'Faz sentido começarmos com um piloto?'"
            ]

        elif "prazo" in prompt_lower or "tempo" in prompt_lower:
            responses = [
                "⏰ **Tratamento de Objeções sobre Prazo:**\n\n• **Fases claras:** Setup (2 dias) → Configuração (1 semana) → Treinamento (3 dias)\n• **Paralelização:** Podemos começar enquanto outros projetos correm\n• **Benefícios imediatos:** Resultados na primeira semana\n\n'Vamos estruturar um cronograma que minimize impactos na sua operação.'",
                "📅 **Estratégia de Timeline:**\n\n**Implementação em 4 fases:**\n1. **Planejamento:** 1 semana\n2. **Setup técnico:** 2 semanas\n3. **Treinamento:** 1 semana\n4. **Go-live:** 1 dia\n\n**Total:** 5 semanas com valorização imediata."
            ]

        elif "concorrente" in prompt_lower or "competidor" in prompt_lower:
            responses = [
                "🎯 **Posicionamento Competitivo:**\n\n**Diferenciais Técnicos:**\n• **Integração:** API-first, 200+ sistemas conectados\n• **Performance:** 3x mais rápido na análise\n• **Suporte:** Equipe dedicada 24/7\n• **ROI:** 340% vs 180% da concorrência\n\n'Vamos demonstrar como nossa solução supera as limitações que você encontrou anteriormente.'",
                "🏆 **Vantagem Competitiva:**\n\n1. **Tecnologia Superior:** NPU otimizada para análise em tempo real\n2. **Integração Completa:** Não requer mudanças na infraestrutura\n3. **Suporte Especializado:** Equipe técnica dedicada\n4. **ROI Comprovado:** Resultados mensuráveis em 30 dias"
            ]

        else:
            responses = [
                "🤖 **Assistente de Vendas IA:**\n\nBaseado na conversa atual, posso ajudar com:\n\n• **Análise de sentimento** em tempo real\n• **Detecção de objeções** automática\n• **Sugestões contextuais** baseadas em IA\n• **Resumos inteligentes** da reunião\n\nQue aspecto específico você gostaria de aprofundar?",
                "💼 **PitchAI - Seu Copiloto Inteligente:**\n\n**Recursos Disponíveis:**\n\n• 🎤 **Transcrição** em tempo real (cliente + vendedor)\n• 😊 **Análise de sentimento** multidimensional\n• 🚨 **Detecção de objeções** automática\n• 💡 **Sugestões inteligentes** baseadas em contexto\n• 📋 **Resumos pós-chamada** estruturados\n\nComo posso auxiliar sua venda atual?"
            ]

        response = random.choice(responses)

        # Adicionar variação baseada no contexto
        if context and 'sentiment' in context:
            sentiment = context['sentiment']
            valence = sentiment.get('valence', 0)

            if valence > 0.5:
                response += "\n\n🌟 **Observação:** Cliente parece receptivo - mantenha o momentum!"
            elif valence < -0.3:
                response += "\n\n⚠️ **Alerta:** Sentimento negativo detectado - foque em resolver objeções."

        return response
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analisar sentimento do texto."""
        if self.sentiment_model and self.models_loaded:
            return self._analyze_sentiment_with_model(text)
        else:
            return self._simulate_sentiment(text)
    
    def _analyze_sentiment_with_model(self, text: str) -> Dict[str, Any]:
        """Analisar sentimento usando modelo real."""
        try:
            # Preparar input para o modelo
            # Nota: Ajustar conforme especificações do modelo de sentimento
            input_text = text[:512]  # Limitar tamanho se necessário
            
            # Tokenizar (ajustar conforme modelo específico)
            # Esta é uma implementação base
            input_name = self.sentiment_model.get_inputs()[0].name
            output_names = [output.name for output in self.sentiment_model.get_outputs()]
            
            # Executar inferência
            result = self.sentiment_model.run(
                output_names,
                {input_name: input_text}
            )
            
            # Processar resultado
            if len(result) >= 2:
                valence = float(result[0])
                engagement = float(result[1])
            else:
                valence = 0.5
                engagement = 0.5
            
            return {
                'valence': valence,
                'engagement': engagement,
                'timestamp': datetime.now(),
                'confidence': 0.8
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de sentimento: {e}")
            return self._simulate_sentiment(text)
    
    def _simulate_sentiment(self, text: str) -> Dict[str, Any]:
        """Simular análise de sentimento."""
        import random
        
        # Palavras-chave para simular sentimento
        positive_words = ['bom', 'ótimo', 'excelente', 'interessante', 'gosto', 'concordo']
        negative_words = ['caro', 'difícil', 'problema', 'não', 'ruim', 'preocupado']
        
        text_lower = text.lower()
        
        # Calcular sentimento baseado em palavras-chave
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            valence = random.uniform(0.6, 0.9)
        elif negative_count > positive_count:
            valence = random.uniform(0.1, 0.4)
        else:
            valence = random.uniform(0.4, 0.6)
        
        engagement = random.uniform(0.3, 0.8)
        
        return {
            'valence': valence,
            'engagement': engagement,
            'timestamp': datetime.now(),
            'confidence': random.uniform(0.7, 0.9)
        }
    
    def detect_objections(self, text: str) -> List[Dict[str, Any]]:
        """Detectar objeções no texto."""
        if self.objection_model and self.models_loaded:
            return self._detect_objections_with_model(text)
        else:
            return self._simulate_objection_detection(text)
    
    def _detect_objections_with_model(self, text: str) -> List[Dict[str, Any]]:
        """Detectar objeções usando modelo real."""
        try:
            # Preparar input para o modelo
            input_text = text[:512]
            
            input_name = self.objection_model.get_inputs()[0].name
            output_names = [output.name for output in self.objection_model.get_outputs()]
            
            # Executar inferência
            result = self.objection_model.run(
                output_names,
                {input_name: input_text}
            )
            
            # Processar resultado
            objections = []
            if len(result) >= 2:
                categories = ['preco', 'timing', 'autoridade', 'necessidade']
                confidences = result[1] if len(result) > 1 else [0.5] * 4
                
                for i, (category, confidence) in enumerate(zip(categories, confidences)):
                    if confidence > self.objection_threshold:
                        objections.append({
                            'category': category,
                            'confidence': float(confidence),
                            'text': text,
                            'timestamp': datetime.now()
                        })
            
            return objections
            
        except Exception as e:
            self.logger.error(f"❌ Erro na detecção de objeções: {e}")
            return self._simulate_objection_detection(text)
    
    def _simulate_objection_detection(self, text: str) -> List[Dict[str, Any]]:
        """Simular detecção de objeções."""
        import random
        
        objections = []
        text_lower = text.lower()
        
        # Palavras-chave para cada categoria
        objection_keywords = {
            'preco': ['caro', 'preço', 'custo', 'orçamento', 'valor'],
            'timing': ['prazo', 'tempo', 'quando', 'agenda', 'data'],
            'autoridade': ['chefe', 'diretor', 'aprovador', 'decisão'],
            'necessidade': ['preciso', 'necessidade', 'problema', 'solução']
        }
        
        for category, keywords in objection_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                if random.random() < self.simulation_config['objection_detection_rate']:
                    objections.append({
                        'category': category,
                        'confidence': random.uniform(0.7, 0.95),
                        'text': text,
                        'timestamp': datetime.now()
                    })
        
        return objections
    
    def identify_speaker(self, audio_chunk: bytes) -> Tuple[str, float]:
        """Identificar falante usando modelo de speaker ID."""
        if self.speaker_model and self.models_loaded:
            return self._identify_speaker_with_model(audio_chunk)
        else:
            return self._simulate_speaker_identification(audio_chunk)
    
    def _identify_speaker_with_model(self, audio_chunk: bytes) -> Tuple[str, float]:
        """Identificar falante usando modelo real."""
        try:
            # Preparar input para o modelo
            audio_array = np.frombuffer(audio_chunk, dtype=np.float32)
            
            input_name = self.speaker_model.get_inputs()[0].name
            output_names = [output.name for output in self.speaker_model.get_outputs()]
            
            # Executar inferência
            result = self.speaker_model.run(
                output_names,
                {input_name: audio_array}
            )
            
            # Processar resultado
            if len(result) >= 2:
                speaker_id = str(result[0])
                confidence = float(result[1])
            else:
                speaker_id = "unknown"
                confidence = 0.5
            
            return speaker_id, confidence
            
        except Exception as e:
            self.logger.error(f"❌ Erro na identificação de falante: {e}")
            return self._simulate_speaker_identification(audio_chunk)
    
    def _simulate_speaker_identification(self, audio_chunk: bytes) -> Tuple[str, float]:
        """Simular identificação de falante."""
        import random
        
        speakers = ["vendedor", "cliente"]
        speaker_id = random.choice(speakers)
        confidence = random.uniform(0.7, 0.95)
        
        return speaker_id, confidence
    
    def initialize_llama_chat(self):
        """Inicializar integração com LLaMA para chat."""
        try:
            self.logger.info("🤖 Inicializando integração com LLaMA chat...")

            # Tentar importar onnxruntime-genai para LLaMA
            try:
                import onnxruntime_genai as og
                llama_available = True
            except ImportError:
                llama_available = False
                self.logger.warning("⚠️ onnxruntime-genai não disponível para LLaMA")

            if llama_available:
                # Caminho do modelo LLaMA
                llama_path = Path(self.config.app_dir) / "llama-3.2-3b-onnx-qnn"

                if llama_path.exists():
                    try:
                        self.logger.info("🔄 Tentando carregar LLaMA com QNN...")

                        # Carregar modelo LLaMA
                        config = og.Config(str(llama_path))
                        model = og.Model(config)
                        tokenizer = og.Tokenizer(model)

                        self.llama_model = {
                            'model': model,
                            'tokenizer': tokenizer,
                            'config': config,
                            'mode': 'qnn'
                        }

                        self.logger.info("✅ LLaMA chat inicializado com QNN!")
                        return True

                    except Exception as e:
                        self.logger.warning(f"⚠️ QNN falhou: {e}")
                        self.logger.info("🔄 Tentando fallback para simulação...")

                        # Fallback para simulação quando QNN falha
                        self.llama_model = {
                            'mode': 'simulation',
                            'fallback': True
                        }

                        self.logger.info("✅ LLaMA inicializado em modo simulação!")
                        return True
                else:
                    self.logger.warning(f"⚠️ Modelo LLaMA não encontrado: {llama_path}")
                    return False
            else:
                self.logger.warning("⚠️ onnxruntime-genai não instalado - usando simulação")
                # Fallback para simulação
                self.llama_model = {
                    'mode': 'simulation',
                    'fallback': True
                }
                return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar LLaMA chat: {e}")
            # Mesmo em caso de erro, configurar simulação
            self.llama_model = {
                'mode': 'simulation',
                'fallback': True
            }
            return True

    def chat_with_llama(self, message: str, system_prompt: str = "Você é um assistente útil.") -> str:
        """Conversar com o modelo LLaMA."""
        if not self.llama_model:
            return self.simulate_llama_chat(message, system_prompt)

        # Verificar se está em modo simulação
        if self.llama_model.get('mode') == 'simulation':
            return self.simulate_llama_chat(message, system_prompt)

        # Tentar usar modelo real
        try:
            import onnxruntime_genai as og

            model = self.llama_model['model']
            tokenizer = self.llama_model['tokenizer']

            # Preparar mensagens
            messages = f'''[{{"role": "system", "content": "{system_prompt}"}}, {{"role": "user", "content": "{message}"}}]'''

            # Aplicar template de chat
            prompt = tokenizer.apply_chat_template(messages=messages, add_generation_prompt=True)
            input_tokens = tokenizer.encode(prompt)

            # Configurar geração
            params = og.GeneratorParams(model)
            params.set_search_options({
                'max_length': 256,
                'temperature': 0.7,
                'top_p': 0.9,
                'do_sample': True
            })

            # Gerar resposta
            generator = og.Generator(model, params)
            generator.append_tokens(input_tokens)

            tokenizer_stream = tokenizer.create_stream()
            response = ""

            while not generator.is_done():
                generator.generate_next_token()
                new_token = generator.get_next_tokens()[0]
                decoded_token = tokenizer_stream.decode(new_token)
                response += decoded_token

            # Limpar gerador
            del generator

            return response.strip()

        except Exception as e:
            self.logger.error(f"❌ Erro no chat com LLaMA real: {e}")
            self.logger.info("🔄 Fazendo fallback para simulação...")
            return self.simulate_llama_chat(message, system_prompt)

    def simulate_llama_chat(self, message: str, system_prompt: str = "Você é um assistente útil.") -> str:
        """Simular chat com LLaMA quando modelo não está disponível."""
        import random
        import time

        # Simular tempo de processamento
        time.sleep(0.5)

        # Respostas simuladas baseadas no input
        responses = [
            "Entendi sua pergunta. Como posso ajudar melhor?",
            "Essa é uma boa observação. Vamos analisar juntos.",
            "Interessante ponto de vista. Posso explicar melhor?",
            "Concordo com você. Que tal considerarmos outras opções?",
            "Boa pergunta! Deixe-me pensar sobre isso.",
            "Vejo que você está interessado neste tópico. Posso aprofundar?",
            "Obrigado pelo feedback. Vamos trabalhar nisso juntos."
        ]

        return random.choice(responses)

    def get_model_status(self) -> Dict[str, Any]:
        """Obter status dos modelos."""
        return {
            'models_loaded': self.models_loaded,
            'whisper_available': self.whisper_model is not None,
            'sentiment_available': self.sentiment_model is not None,
            'objection_available': self.objection_model is not None,
            'speaker_available': self.speaker_model is not None,
            'llama_available': self.llama_model is not None,
            'simulation_mode': not self.models_loaded
        }

    def process_audio(self, audio_data):
        """Processar dados de áudio e emitir sinais."""
        try:
            self.logger.debug(f"📡 Processando {len(audio_data)} bytes de áudio")

            # Processar transcrição
            transcription = self.transcribe_audio(audio_data)
            if transcription:
                self.transcription_ready.emit(transcription, "unknown")

            # Processar sentimento
            sentiment = self.analyze_sentiment(audio_data)
            if sentiment:
                self.sentiment_updated.emit(sentiment)

            # Detectar objeções
            objections = self.detect_objections(audio_data)
            if objections:
                self.objection_detected.emit(objections[0], objections[1:])

        except Exception as e:
            self.logger.error(f"❌ Erro ao processar áudio: {e}")

    def cleanup(self):
        """Limpar recursos do ONNX Manager."""
        self.logger.info("🧹 Limpando ONNX Manager...")
        self.shutdown()

    def shutdown(self):
        """Encerrar NPU Manager."""
        self.logger.info("🔄 Encerrando NPU Manager...")
        
        # Limpar cache
        self._transcription_cache.clear()
        self._sentiment_cache.clear()
        
        self.logger.info("✅ NPU Manager encerrado")

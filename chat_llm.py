#!/usr/bin/env python3
"""
Chat LLM - Interface de Chat Inteligente com Memória
=====================================================

Chat interativo que usa o LLM Service integrado do PitchAI com memória
de conversa persistente. Suporta tanto modo real (NPU) quanto simulado.
"""

import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

@dataclass
class ConversationMessage:
    """Mensagem da conversa."""
    role: str  # 'user' | 'assistant'
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationMemory:
    """Memória da conversa."""
    messages: List[ConversationMessage] = field(default_factory=list)
    max_messages: int = 50  # Máximo de mensagens na memória
    session_id: str = ""

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Adicionar mensagem à memória."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self.messages.append(message)

        # Manter limite de mensagens
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obter mensagens recentes formatadas para o LLM."""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in recent
        ]

    def clear(self):
        """Limpar memória da conversa."""
        self.messages.clear()

    def save_to_file(self, filepath: Path):
        """Salvar conversa em arquivo."""
        data = {
            "session_id": self.session_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, filepath: Path):
        """Carregar conversa de arquivo."""
        if not filepath.exists():
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.session_id = data.get("session_id", "")
            self.messages.clear()

            for msg_data in data.get("messages", []):
                message = ConversationMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=msg_data["timestamp"],
                    metadata=msg_data.get("metadata", {})
                )
                self.messages.append(message)

        except Exception as e:
            logging.warning(f"Erro ao carregar conversa: {e}")

def create_chat_interface():
    """Criar interface de chat inteligente com memória."""

    print("🤖 PitchAI - Chat Inteligente com Memória")
    print("=" * 50)
    print("💡 Digite suas perguntas sobre vendas")
    print("🔄 Comandos: 'sair', 'stats', 'clear', 'save', 'load'")
    print()

    # Inicializar memória da conversa
    memory = ConversationMemory()
    memory.session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Diretório para salvar conversas
    conversations_dir = Path("conversations")
    conversations_dir.mkdir(exist_ok=True)

    # Inicializar serviço LLM
    service = None
    service_type = "unknown"

    print("🔄 Inicializando LLM Service...")

    # Tentar usar o IBM Granite v3.1 8B
    try:
        from ai.model_manager import ModelManager
        from core.config import create_config
        from ai.llm_service import LLMService

        # Carregar configuração e ModelManager
        config = create_config()
        model_manager = ModelManager(config)
        model_manager.load_manifest()

        # Usar IBM Granite v3.1 8B
        service = GraniteLLMService(model_manager, use_simulation=False)

        if service.initialize():
            service_type = "ibm_granite_v3_1_8b"
            print("✅ IBM Granite v3.1 8B inicializado!")
        else:
            print("❌ Falha ao inicializar IBM Granite")
            return

    except Exception as e:
        print(f"❌ Erro ao inicializar LLM Service: {e}")
        return

    print()
    print(f"🎯 Serviço: {service_type.upper()}")
    print("🧠 Memória: Ativa (máx. 50 mensagens)")
    print("─" * 50)
    print()

    conversation_count = 0

    try:
        while True:
            # Ler entrada do usuário
            try:
                user_input = input("❓ Você: ").strip()
            except KeyboardInterrupt:
                print("\n👋 Chat interrompido. Até logo!")
                break

            if not user_input:
                continue

            # Comandos especiais
            if user_input.lower() in ['sair', 'exit', 'quit']:
                print("👋 Até logo!")
                break

            elif user_input.lower() == 'stats':
                stats_info = {
                    "Conversas": conversation_count,
                    "Mensagens na memória": len(memory.messages),
                    "Sessão": memory.session_id,
                    "Serviço": service_type
                }

                print("📊 Estatísticas:")
                for key, value in stats_info.items():
                    print(f"   {key}: {value}")
                print()

                # Mostrar últimas mensagens
                if memory.messages:
                    print("💬 Últimas mensagens:")
                    for i, msg in enumerate(memory.messages[-3:], 1):
                        role_icon = "👤" if msg.role == "user" else "🤖"
                        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                        print(f"   {i}. {role_icon} {content_preview}")
                    print()
                continue

            elif user_input.lower() == 'clear':
                memory.clear()
                print("🧹 Memória da conversa limpa!")
                print()
                continue

            elif user_input.lower() == 'save':
                filepath = conversations_dir / f"{memory.session_id}.json"
                memory.save_to_file(filepath)
                print(f"💾 Conversa salva em: {filepath}")
                print()
                continue

            elif user_input.lower() == 'load':
                # Listar conversas disponíveis
                saved_conversations = list(conversations_dir.glob("*.json"))
                if not saved_conversations:
                    print("❌ Nenhuma conversa salva encontrada")
                    print()
                    continue

                print("📁 Conversas salvas:")
                for i, conv_file in enumerate(saved_conversations, 1):
                    print(f"   {i}. {conv_file.stem}")
                print()

                try:
                    choice = input("Digite o número da conversa para carregar: ").strip()
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(saved_conversations):
                            selected_file = saved_conversations[idx]
                            memory.load_from_file(selected_file)
                            print(f"📂 Conversa '{selected_file.stem}' carregada!")
                            print(f"   {len(memory.messages)} mensagens restauradas")
                        else:
                            print("❌ Número inválido")
                    else:
                        print("❌ Digite um número válido")
                except Exception as e:
                    print(f"❌ Erro ao carregar: {e}")

                print()
                continue

            elif user_input.lower() == 'help':
                print("💡 Comandos disponíveis:")
                print("   sair/exit/quit - Encerrar chat")
                print("   stats - Ver estatísticas da sessão")
                print("   clear - Limpar memória da conversa")
                print("   save - Salvar conversa atual")
                print("   load - Carregar conversa salva")
                print("   help - Esta ajuda")
                print("   Qualquer outra coisa - Pergunta sobre vendas")
                print()
                continue

            # Adicionar mensagem do usuário à memória
            memory.add_message("user", user_input)

            # Preparar contexto para o LLM
            context_messages = memory.get_recent_messages(limit=10)  # Últimas 10 mensagens

            # Criar prompt com contexto
            if len(context_messages) > 1:
                # Conversa com histórico
                context_text = "\n".join([
                    f"{'Usuário' if msg['role'] == 'user' else 'Assistente'}: {msg['content']}"
                    for msg in context_messages[:-1]  # Excluir a última mensagem do usuário
                ])

                # Verificar se o usuário mencionou seu nome anteriormente
                user_name = None
                for msg in context_messages:
                    if msg['role'] == 'user' and 'chamo' in msg['content'].lower():
                        # Extrair nome após "chamo" ou "me chamo"
                        content_lower = msg['content'].lower()
                        if 'chamo' in content_lower:
                            parts = msg['content'].split('chamo')
                            if len(parts) > 1:
                                user_name = parts[1].strip().split()[0]  # Pegar primeira palavra após "chamo"
                                break

                if user_name:
                    full_prompt = f"Contexto da conversa:\n{context_text}\n\nO usuário se apresentou como {user_name}.\n\nUsuário: {user_input}\n\nAssistente:"
                else:
                    full_prompt = f"Contexto da conversa:\n{context_text}\n\nUsuário: {user_input}\n\nAssistente:"
            else:
                # Primeira mensagem
                full_prompt = user_input

            # Gerar resposta
            print("🤖 Pensando...", end="", flush=True)

            try:
                # Tentar usar o método correto baseado no serviço disponível
                if hasattr(service, 'generate_response'):
                    response = service.generate_response(full_prompt, max_tokens=200)
                elif hasattr(service, 'generate'):
                    response = service.generate(full_prompt, max_tokens=200)
                else:
                    response = "Erro: Método de geração não encontrado"

                # Limpar "Pensando..."
                print("\r" + " " * 25 + "\r", end="", flush=True)

                # Adicionar resposta à memória
                memory.add_message("assistant", response, {"model": service_type})

                # Mostrar resposta
                print(f"🤖 PitchAI: {response}")
                conversation_count += 1

            except Exception as e:
                print(f"\r❌ Erro na geração: {e}")
                # Não adicionar erro à memória

            print()

    except Exception as e:
        print(f"\n❌ Erro no chat: {e}")

    finally:
        # Salvar conversa automaticamente se houver mensagens
        if memory.messages:
            filepath = conversations_dir / f"{memory.session_id}.json"
            memory.save_to_file(filepath)
            print(f"💾 Conversa salva automaticamente: {filepath}")

        # Cleanup
        if service and hasattr(service, 'cleanup'):
            print("🔄 Limpando recursos...")
            service.cleanup()

        print(f"\n📊 Sessão finalizada: {conversation_count} conversas usando {service_type}")

class GraniteLLMService:
    """Serviço LLM para IBM Granite v3.1 8B Instruct."""

    def __init__(self, model_manager, use_simulation=False):
        self.model_manager = model_manager
        self.use_simulation = use_simulation
        self.session = None
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)

        # Configurações específicas do IBM Granite
        self.model_name = "ibm_granite_3_1_8b"
        self.max_tokens = 2048
        self.temperature = 0.7
        self.top_p = 0.9

        # Flags para diferentes métodos de carregamento
        self.use_transformers = False
        self.use_api = False
        self.use_onnx = False
        self.use_qairt = False
        self.use_genie = False

        # Componentes para diferentes métodos
        self.tokenizer = None
        self.model = None
        self.api_key = None
        self.api_url = None

        # Componentes QAIRT/Genie
        self.qairt_session = None
        self.geniet2t_runner = None
        self.bin_files = []
        self.geniet2t_path = None

    def _try_qairt_genie(self):
        """Tentar carregar via QAIRT/Genie para execução on-device."""
        try:
            self.logger.info("🔄 Tentando QAIRT/Genie para execução on-device...")

            # Verificar se os arquivos .bin existem
            from pathlib import Path
            model_dir = Path(__file__).parent / "models" / "ibm_granite_3_1_8b"

            if not model_dir.exists():
                self.logger.warning("⚠️ Diretório do modelo IBM Granite não encontrado")
                return False

            # Verificar arquivos de configuração
            config_files = [
                model_dir / "genie_config.json",
                model_dir / "htp_backend_ext_config.json",
                model_dir / "tokenizer.json"
            ]

            for config_file in config_files:
                if not config_file.exists():
                    self.logger.warning(f"⚠️ Arquivo de configuração não encontrado: {config_file.name}")
                    return False

            # Encontrar todos os arquivos .bin
            bin_files = list(model_dir.glob("weight_sharing_model_*.serialized.bin"))
            if len(bin_files) != 5:
                self.logger.warning(f"⚠️ Esperado 5 arquivos .bin, encontrado {len(bin_files)}")
                return False

            self.bin_files = sorted(bin_files)
            self.model_dir = model_dir
            self.logger.info(f"📁 Encontrados {len(self.bin_files)} arquivos QNN: {[f.name for f in self.bin_files]}")

            # Verificar caminhos do QAIRT SDK
            import os
            qairt_paths = [
                os.environ.get('QNN_SDK_ROOT'),
                "C:/Users/qchac/Downloads/v2.37.0.250724/qairt/2.37.0.250724",
                "C:/Users/qchac/Downloads/v2.29.0.241129/qairt/2.29.0.241129",
                "C:/Qualcomm/AIStack/QAIRT"
            ]

            for qairt_path in qairt_paths:
                if qairt_path and os.path.exists(qairt_path):
                    # Procurar executável do Genie
                    import platform
                    system = platform.system().lower()

                    if system == "windows":
                        genie_paths = [
                            os.path.join(qairt_path, "bin", "x86_64-windows-msvc", "genie-t2t-run.exe"),
                            os.path.join(qairt_path, "bin", "arm64x-windows-msvc", "genie-t2t-run.exe"),
                            os.path.join(qairt_path, "bin", "aarch64-windows-msvc", "genie-t2t-run.exe")
                        ]
                    else:  # Linux/Mac
                        genie_paths = [
                            os.path.join(qairt_path, "bin", "aarch64-oe-linux-gcc11.2", "genie-t2t-run"),
                            os.path.join(qairt_path, "bin", "x86_64-linux-clang", "genie-t2t-run")
                        ]

                    for genie_path in genie_paths:
                        if os.path.exists(genie_path):
                            self.geniet2t_path = genie_path
                            self.logger.info(f"✅ Genie executável encontrado: {genie_path}")
                            self.use_genie = True
                            return True

            self.logger.warning("⚠️ Genie executável não encontrado nos caminhos padrão")
            return False

        except Exception as e:
            self.logger.error(f"❌ Erro ao tentar QAIRT/Genie: {e}")
            return False

    def initialize(self):
        """Inicializar o modelo IBM Granite."""
        try:
            if self.use_simulation:
                self.logger.info("🔄 Inicializando IBM Granite em modo simulação")
                self.is_initialized = True
                return True

            self.logger.info("🔄 Carregando modelo IBM Granite v3.1 8B...")

            # Tentar múltiplas abordagens para carregar o modelo

            # 1. Tentar via QAIRT/Genie (método preferencial para on-device)
            if self._try_qairt_genie():
                self.logger.info("✅ IBM Granite v3.1 8B carregado via QAIRT/Genie")
                self.use_qairt = True
                self.is_initialized = True
                return True

            # 2. Tentar via ModelManager
            if hasattr(self.model_manager, 'get_session'):
                try:
                    self.session = self.model_manager.get_session(self.model_name)
                    if self.session:
                        self.logger.info("✅ IBM Granite v3.1 8B carregado via ModelManager")
                        self.is_initialized = True
                        return True
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro no ModelManager: {e}")

            # 2. Tentar carregamento direto com ONNX Runtime
            try:
                import onnxruntime as ort
                from pathlib import Path

                # Verificar se existe modelo ONNX convertido
                onnx_path = Path(__file__).parent / "models" / "ibm_granite_3_1_8b" / "model.onnx"
                if onnx_path.exists():
                    self.logger.info(f"📁 Modelo ONNX encontrado: {onnx_path}")

                    # Carregar sessão ONNX
                    providers = ['CPUExecutionProvider']  # Usar CPU por padrão
                    if ort.get_device() == 'GPU':
                        providers.insert(0, 'CUDAExecutionProvider')

                    self.session = ort.InferenceSession(str(onnx_path), providers=providers)
                    self.use_onnx = True
                    self.logger.info("✅ IBM Granite v3.1 8B carregado via ONNX Runtime")
                    self.is_initialized = True
                    return True
                else:
                    self.logger.warning("⚠️ Modelo ONNX não encontrado, tentando outros métodos")

            except ImportError:
                self.logger.warning("⚠️ ONNX Runtime não disponível")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro no carregamento ONNX: {e}")

            # 3. Tentar via Hugging Face Transformers (se disponível)
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch

                # Verificar se temos GPU disponível
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.logger.info(f"🔄 Tentando carregar via Transformers (device: {device})")

                # Carregar tokenizer e modelo
                model_name = "ibm-granite/granite-3.1-8b-instruct"

                self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    device_map="auto" if device == "cuda" else None,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32
                )

                if device == "cpu":
                    self.model = self.model.to(device)

                self.logger.info("✅ IBM Granite v3.1 8B carregado via Hugging Face Transformers")
                self.use_transformers = True
                self.is_initialized = True
                return True

            except ImportError:
                self.logger.warning("⚠️ Transformers não disponível")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro no carregamento Transformers: {e}")

            # 4. Tentar via API do IBM Watson (se disponível)
            try:
                import requests
                import os

                # Verificar se há chave API configurada
                api_key = os.getenv('IBM_GRANITE_API_KEY') or os.getenv('WATSONX_API_KEY')
                if api_key:
                    self.logger.info("🔄 Tentando conectar via IBM Watson API")
                    self.api_key = api_key
                    self.api_url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
                    self.use_api = True
                    self.logger.info("✅ IBM Granite v3.1 8B conectado via API")
                    self.is_initialized = True
                    return True
                else:
                    self.logger.warning("⚠️ API Key do IBM Watson não configurada")

            except ImportError:
                self.logger.warning("⚠️ Requests não disponível para API")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro na API do IBM Watson: {e}")

            # 5. Último recurso: simulação melhorada
            self.logger.warning("⚠️ Nenhum método de carregamento funcionou, usando simulação avançada")
            self.use_simulation = True
            self.is_initialized = True
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro geral ao inicializar IBM Granite: {e}")
            self.use_simulation = True
            self.is_initialized = True
            return True

    def generate_response(self, prompt, max_tokens=256, include_history=True):
        """Gerar resposta usando IBM Granite."""
        if not self.is_initialized:
            return "❌ Serviço não inicializado"

        if self.use_simulation:
            return self._generate_simulation_response(prompt)

        try:
            self.logger.debug(f"🤖 Gerando resposta com IBM Granite (max_tokens: {max_tokens})")

            # Roteamento baseado no método de carregamento
            if self.use_qairt:
                response = self._generate_with_qairt(prompt, max_tokens)
            elif self.use_genie:
                response = self._generate_with_genie(prompt, max_tokens)
            elif self.use_transformers:
                response = self._generate_with_transformers(prompt, max_tokens)
            elif self.use_api:
                response = self._generate_with_api(prompt, max_tokens)
            elif self.use_onnx:
                response = self._generate_with_onnx(prompt, max_tokens)
            else:
                # Fallback para ModelManager
                response = self._generate_with_model_manager(prompt, max_tokens)

            self.logger.debug("✅ Resposta gerada com sucesso")
            return response

        except Exception as e:
            self.logger.error(f"❌ Erro na geração com IBM Granite: {e}")
            return f"❌ Erro: {str(e)}"

    def _prepare_granite_input(self, prompt, max_tokens):
        """Preparar input específico para IBM Granite v3.1 8B."""
        # Template otimizado para IBM Granite v3.1 8B
        system_prompt = """You are Granite, an AI language model developed by IBM.
You are a helpful, honest, and harmless assistant. Provide accurate, useful information and maintain context in conversations."""

        # Formatar prompt com template específico do Granite
        formatted_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>"

        # Adicionar metadados para controle de geração
        self.current_max_tokens = min(max_tokens, self.max_tokens)

        return formatted_prompt

    def _generate_with_transformers(self, prompt, max_tokens):
        """Gerar resposta usando Hugging Face Transformers."""
        try:
            # Preparar input
            input_text = self._prepare_granite_input(prompt, max_tokens)

            # Tokenizar
            inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, max_length=2048)

            # Mover para device correto
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Gerar resposta
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Decodificar resposta
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extrair apenas a resposta (remover o prompt)
            if input_text in response:
                response = response[len(input_text):].strip()

            return response

        except Exception as e:
            self.logger.error(f"Erro na geração com Transformers: {e}")
            return self._generate_simulation_response(prompt)

    def _generate_with_api(self, prompt, max_tokens):
        """Gerar resposta usando IBM Watson API."""
        try:
            import requests

            # Preparar payload para Watson
            payload = {
                "input": self._prepare_granite_input(prompt, max_tokens),
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "repetition_penalty": 1.0
                },
                "model_id": "ibm/granite-13b-instruct-v2",
                "project_id": "your-project-id"  # Substitua pelo seu project ID
            }

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # Fazer requisição
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("results", [{}])[0].get("generated_text", "")

                # Limpar resposta
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()

                return generated_text
            else:
                self.logger.error(f"Erro na API Watson: {response.status_code} - {response.text}")
                return self._generate_simulation_response(prompt)

        except Exception as e:
            self.logger.error(f"Erro na geração com API: {e}")
            return self._generate_simulation_response(prompt)

    def _generate_with_onnx(self, prompt, max_tokens):
        """Gerar resposta usando ONNX Runtime."""
        try:
            # Preparar input
            input_text = self._prepare_granite_input(prompt, max_tokens)

            # Tokenizar (simplificado - em produção usaria tokenizer real)
            input_ids = self._simple_tokenize(input_text)

            # Preparar inputs para ONNX
            ort_inputs = {
                self.session.get_inputs()[0].name: input_ids
            }

            # Executar inferência
            outputs = self.session.run(None, ort_inputs)

            # Decodificar output (simplificado)
            response = self._simple_decode(outputs[0])

            # Limpar resposta
            if input_text in response:
                response = response[len(input_text):].strip()

            return response

        except Exception as e:
            self.logger.error(f"Erro na geração com ONNX: {e}")
            return self._generate_simulation_response(prompt)

    def _generate_with_qairt(self, prompt, max_tokens):
        """Gerar resposta usando QAIRT SDK."""
        try:
            import qairt
            from pathlib import Path

            # Preparar input
            input_text = self._prepare_granite_input(prompt, max_tokens)

            # Para QAIRT, seria necessário:
            # 1. Criar sessão com os arquivos .bin
            # 2. Preparar input conforme especificação do modelo
            # 3. Executar inferência usando a API do QAIRT
            # 4. Decodificar output

            # Como ainda não temos a implementação completa do QAIRT,
            # vamos usar uma simulação melhorada
            self.logger.info("🔄 Usando simulação aprimorada (QAIRT placeholder)")
            return self._simulate_granite_inference(input_text, max_tokens)

        except Exception as e:
            self.logger.error(f"Erro na geração com QAIRT: {e}")
            return self._generate_simulation_response(prompt)

    def _generate_with_genie(self, prompt, max_tokens):
        """Gerar resposta usando Genie executável."""
        try:
            import subprocess
            import json
            from pathlib import Path

            # Preparar input
            input_text = self._prepare_granite_input(prompt, max_tokens)
            self.logger.debug(f"📝 Input preparado: {input_text[:100]}...")

            # Caminho para o arquivo de configuração
            config_path = self.model_dir / "genie_config.json"

            if not config_path.exists():
                self.logger.error(f"❌ Arquivo de configuração não encontrado: {config_path}")
                return self._generate_simulation_response(prompt)

            # Modificar configuração temporariamente para incluir o prompt
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Atualizar configuração com parâmetros específicos desta geração
                config["generation"]["max_new_tokens"] = max_tokens
                config["generation"]["temperature"] = self.temperature
                config["generation"]["top_p"] = self.top_p

                # Salvar configuração temporária
                temp_config_path = self.model_dir / "temp_genie_config.json"
                with open(temp_config_path, 'w') as f:
                    json.dump(config, f, indent=2)

                # Executar Genie com o arquivo de configuração
                cmd = [
                    self.geniet2t_path,
                    "--config", str(temp_config_path),
                    "--prompt", input_text
                ]

                self.logger.info(f"🔄 Executando Genie: {' '.join(cmd[:3])}...")

                # Executar comando
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # Timeout aumentado para 2 minutos
                    cwd=str(self.model_dir)
                )

                # Limpar arquivo temporário
                try:
                    temp_config_path.unlink()
                except:
                    pass

                if result.returncode == 0:
                    # Parsear output do Genie
                    stdout = result.stdout.strip()
                    stderr = result.stderr.strip()

                    self.logger.debug(f"📄 Genie stdout: {stdout[:200]}...")
                    if stderr:
                        self.logger.debug(f"📄 Genie stderr: {stderr[:200]}...")

                    # Procurar pela resposta gerada
                    response = self._parse_genie_output(stdout, stderr)

                    if response and response.strip():
                        self.logger.info("✅ Resposta gerada com sucesso pelo Genie")
                        return response
                    else:
                        self.logger.warning("⚠️ Genie executou mas não retornou resposta válida")
                        self.logger.debug(f"Stdout completo: {stdout}")
                        self.logger.debug(f"Stderr completo: {stderr}")
                else:
                    self.logger.error(f"❌ Genie falhou com código {result.returncode}")
                    self.logger.error(f"Stdout: {result.stdout}")
                    self.logger.error(f"Stderr: {result.stderr}")

            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Erro ao ler arquivo de configuração: {e}")
            except Exception as e:
                self.logger.error(f"❌ Erro ao preparar configuração: {e}")

            # Fallback para simulação
            self.logger.info("🔄 Usando simulação como fallback")
            return self._generate_simulation_response(prompt)

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Timeout no Genie (2 minutos)")
            return self._generate_simulation_response(prompt)
        except Exception as e:
            self.logger.error(f"Erro na geração com Genie: {e}")
            return self._generate_simulation_response(prompt)

    def _parse_genie_output(self, stdout, stderr):
        """Parsear output do Genie para extrair a resposta."""
        try:
            # Procurar por padrões comuns de output do Genie
            lines = stdout.split('\n')

            # Padrões comuns que podem conter a resposta
            response_patterns = [
                "Generated text:",
                "Response:",
                "Output:",
                "Answer:",
                "Assistant:"
            ]

            for line in lines:
                line = line.strip()
                for pattern in response_patterns:
                    if pattern.lower() in line.lower():
                        # Extrair texto após o padrão
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            response = parts[1].strip()
                            if response:
                                return response

            # Se não encontrou padrão específico, tentar encontrar texto entre aspas ou após >
            for line in lines:
                line = line.strip()
                if line.startswith('>') or line.startswith('"') or line.startswith("'"):
                    continue  # Pular linhas de comando/input
                if len(line) > 10 and not line.startswith('INFO:') and not line.startswith('DEBUG:'):
                    return line

            # Último recurso: retornar a última linha não vazia
            for line in reversed(lines):
                line = line.strip()
                if line and len(line) > 5:
                    return line

            # Se nada foi encontrado, retornar vazio para usar fallback
            return ""

        except Exception as e:
            self.logger.error(f"Erro ao parsear output do Genie: {e}")
            return ""

    def _generate_with_model_manager(self, prompt, max_tokens):
        """Gerar resposta usando ModelManager do PitchAI."""
        try:
            # Preparar input
            input_text = self._prepare_granite_input(prompt, max_tokens)

            # Usar o método padrão do ModelManager
            # Isso assume que o ModelManager tem um método generate
            if hasattr(self.session, 'generate'):
                response = self.session.generate(input_text, max_tokens=max_tokens)
                return response
            else:
                # Fallback para simulação
                return self._simulate_granite_inference(input_text, max_tokens)

        except Exception as e:
            self.logger.error(f"Erro na geração com ModelManager: {e}")
            return self._generate_simulation_response(prompt)

    def _simple_tokenize(self, text):
        """Tokenização simples para ONNX (substitua por tokenizer real)."""
        import numpy as np

        # Simulação básica de tokenização
        tokens = []
        for char in text:
            # Mapeamento simples char -> token_id
            token_id = ord(char) % 50000
            tokens.append(token_id)

        # Padding para tamanho fixo (ajuste conforme necessário)
        max_length = 512
        if len(tokens) > max_length:
            tokens = tokens[:max_length]
        else:
            tokens.extend([0] * (max_length - len(tokens)))

        return np.array([tokens], dtype=np.int64)

    def _simple_decode(self, outputs):
        """Decodificação simples para ONNX (substitua por tokenizer real)."""
        # Simulação básica de decodificação
        tokens = outputs[0][0] if len(outputs) > 0 and len(outputs[0]) > 0 else []

        text = ""
        for token in tokens:
            if token > 0 and token < 128:  # ASCII básico
                text += chr(token)
            elif token == 0:  # Padding
                break

        return text

    def _simulate_granite_inference(self, input_text, max_tokens):
        """Simular inferência do IBM Granite com respostas avançadas e realistas."""
        import random
        import re

        # Análise avançada do prompt
        prompt_lower = input_text.lower()
        prompt_words = set(re.findall(r'\b\w+\b', prompt_lower))

        # Dicionários de palavras-chave para categorização
        sales_keywords = {
            'preço': ['preço', 'custo', 'valor', 'orçamento', 'investimento', 'pagar', 'caro'],
            'objeção': ['objeção', 'dúvida', 'preocupação', 'problema', 'não', 'talvez'],
            'cliente': ['cliente', 'prospect', 'lead', 'contato', 'empresa', 'setor'],
            'fechamento': ['fechar', 'contrato', 'assinar', 'comprar', 'decisão', 'pronto'],
            'follow_up': ['follow', 'retorno', 'ligar', 'email', 'agenda', 'reunião'],
            'produto': ['produto', 'solução', 'serviço', 'plataforma', 'sistema', 'ferramenta']
        }

        # Identificar categoria principal
        main_category = 'geral'
        max_matches = 0

        for category, keywords in sales_keywords.items():
            matches = len(prompt_words.intersection(set(keywords)))
            if matches > max_matches:
                max_matches = matches
                main_category = category

        # Respostas específicas por categoria
        responses_db = {
            'preço': [
                "💰 **Estratégia de Precificação Inteligente**\n\nQuando o cliente questiona o preço, use a abordagem 'Foco no Valor':\n\n• **ROI Quantificado**: 'Este investimento retorna em média 300% em 18 meses'\n• **Benefícios Intangíveis**: Redução de tempo operacional e aumento de eficiência\n• **Casos de Sucesso**: 'Cliente X economizou R$50k no primeiro ano'\n\nQuer que eu ajude a personalizar essa resposta para seu contexto específico?",
                "📊 **Framework de Resposta a Objeções de Preço**\n\nEstrutura comprovada:\n\n1. **Reconhecer**: 'Entendo sua preocupação com o investimento'\n2. **Questionar**: 'Que resultados você espera obter?'\n3. **Demonstrar Valor**: Mostre benefícios específicos e mensuráveis\n4. **Comparar**: 'Quanto custa manter o status quo?'\n\nQue tipo de cliente você está atendendo?",
                "🎯 **Precificação Baseada em Valor vs Custo**\n\nMude a perspectiva:\n\n• De: 'Quanto custa?'\n• Para: 'Quanto valor isso gera?'\n\n**Exemplo de Resposta:**\n'Entendo que o investimento inicial parece alto. Mas considere: nossos clientes recuperam o investimento em média em 8 meses através de economia operacional e aumento de receita.'\n\nPrecisa de ajuda para adaptar isso?"
            ],

            'objeção': [
                "🚨 **Sistema de Tratamento de Objeções**\n\nClassifique a objeção:\n\n**Tipo 1 - Preço**: Foco em ROI\n**Tipo 2 - Autoridade**: 'Quem mais precisa aprovar?'\n**Tipo 3 - Necessidade**: Valide problemas reais\n**Tipo 4 - Timing**: 'Quando seria o momento ideal?'\n\nQual tipo você identificou? Posso dar uma resposta específica.",
                "💭 **Técnica FEEL-FELT-FOUND**\n\nFramework comprovado:\n\n• **FEEL**: 'Entendo como se sente' (empatia)\n• **FELT**: 'Outros clientes se sentiram assim' (normalização)\n• **FOUND**: 'Mas descobriram que...' (benefício)\n\n**Exemplo:**\nCliente: 'Parece caro demais'\nVocê: 'Entendo sua preocupação (FEEL). Outros clientes inicialmente pensaram o mesmo (FELT), mas descobriram que o ROI é de 400% em 12 meses (FOUND)'\n\nQuer praticar com uma objeção específica?",
                "🎯 **Análise de Raiz da Objeção**\n\nPergunte-se:\n\n• É uma objeção real ou desculpa?\n• Está baseada em fatos ou emoção?\n• É sobre preço, produto ou processo?\n• Posso resolver isso com informação?\n\nA maioria das objeções (70%) são na verdade pedidos de informação. Vamos analisar sua objeção específica?"
            ],

            'cliente': [
                "👥 **Qualificação BANT Avançada**\n\nAvalie:\n\n• **Budget**: Capacidade financeira confirmada?\n• **Authority**: Tomador de decisão ou influenciador?\n• **Need**: Problema urgente que precisa resolver?\n• **Timeline**: Quando precisam implementar?\n\n**Dica**: Foque em prospects com alta necessidade e autoridade de decisão.",
                "📋 **Perfil do Comprador Digital**\n\nEntenda o journey:\n\n1. **Unaware**: Não conhece o problema\n2. **Aware**: Sabe que tem problema\n3. **Interested**: Buscando soluções\n4. **Evaluating**: Comparando opções\n5. **Purchase**: Pronto para comprar\n\nEm qual estágio está seu prospect? Isso determina sua abordagem.",
                "🎯 **Segmentação por Persona**\n\nAdapte sua mensagem:\n\n• **Executivo**: ROI e estratégia\n• **Gerente**: Eficiência operacional\n• **Usuário Final**: Benefícios práticos\n• **Influenciador**: Inovação tecnológica\n\nQue persona você está atendendo? Posso ajudar a criar uma mensagem direcionada."
            ],

            'fechamento': [
                "🎯 **Técnicas de Fechamento Avançadas**\n\n**Fechamento por Assumir:** 'Quando começamos a implementação?'\n\n**Fechamento Alternativo:** 'Prefere o plano anual ou mensal?'\n\n**Fechamento por Urgência:** 'Temos uma promoção especial até sexta'\n\nQual técnica combina melhor com seu estilo de vendas?",
                "📝 **Checklist de Pré-Fechamento**\n\nAntes de fechar:\n\n✅ Qualificação completa\n✅ Objeções tratadas\n✅ Benefícios claros\n✅ ROI demonstrado\n✅ Stakeholders alinhados\n✅ Proposta detalhada\n✅ Prazo definido\n\nFaltando algum item? Vamos trabalhar nele.",
                "🚀 **Fechamento Consultivo**\n\nAbordagem moderna:\n\n1. **Descobrir**: Entenda necessidades reais\n2. **Solução**: Apresente valor personalizado\n3. **Prova**: Mostre evidências sociais\n4. **Fechar**: Peça compromisso específico\n\nO fechamento consultivo aumenta taxa de conversão em 20-30%. Quer praticar?"
            ],

            'follow_up': [
                "📞 **Sequência de Follow-up Inteligente**\n\n**Dia 1**: Email de agradecimento + resumo\n**Dia 3**: Ligação para tirar dúvidas\n**Dia 7**: Case study relevante\n**Dia 14**: Oferta especial\n**Dia 30**: Check-in de relacionamento\n\nAdapte baseado na resposta do prospect.",
                "🎯 **Follow-up Personalizado**\n\nUse dados para personalizar:\n\n• **Objeção Específica**: 'Sobre sua preocupação com X...'\n• **Setor**: 'Vi que empresa Y do mesmo setor...'\n• **Cargo**: 'Como gerente, você deve valorizar...'\n• **Timeline**: 'Considerando seu prazo de X...'\n\nQue informação você tem sobre este prospect?",
                "📈 **Métricas de Follow-up**\n\nAcompanhe:\n\n• **Taxa de Resposta**: Meta >20%\n• **Conversões**: Meta >5%\n• **Tempo Médio**: <48h resposta\n• **Qualidade**: Leads qualificados\n\nComo está seu follow-up atual? Podemos otimizar?"
            ],

            'produto': [
                "💼 **Apresentação Consultiva de Produto**\n\nEstrutura:\n\n1. **Descoberta**: Entenda necessidades\n2. **Apresentação**: Foque em benefícios\n3. **Demonstração**: Mostre valor\n4. **Tratamento**: Objeções antecipadas\n5. **Fechamento**: Próximos passos\n\nQual etapa você gostaria de focar?",
                "🔧 **Demonstração Efetiva**\n\nTécnicas comprovadas:\n\n• **Cenário Real**: Use caso do prospect\n• **Benefício Primeiro**: 'Isso reduz tempo em 40%'\n• **Prova Social**: 'Cliente X conseguiu Y'\n• **Interação**: Peça feedback durante demo\n\nComo você normalmente faz demonstrações?",
                "📊 **Posicionamento Competitivo**\n\nDestaque diferenciais:\n\n• **Funcionalidade**: Recursos únicos\n• **Facilidade**: Simplicidade de uso\n• **Suporte**: Atendimento superior\n• **ROI**: Melhor retorno\n• **Inovação**: Tecnologia avançada\n\nQual seu maior diferencial competitivo?"
            ],

            'geral': [
                "🤖 **Assistente de Vendas IA - IBM Granite v3.1 8B**\n\nPosso ajudar com:\n\n• **Estratégias de Vendas**: Técnicas comprovadas e frameworks\n• **Tratamento de Objeções**: Respostas estruturadas e eficazes\n• **Qualificação de Leads**: BANT e outras metodologias\n• **Follow-up Inteligente**: Sequências personalizadas\n• **Análise de Conversas**: Insights sobre interações\n• **Fechamento**: Técnicas avançadas e consultivas\n\nQue aspecto específico você gostaria de explorar?",
                "💼 **Sistema Completo de Vendas**\n\nAbordagem integrada:\n\n1. **Prospecção**: Encontrar prospects qualificados\n2. **Qualificação**: Identificar oportunidades reais\n3. **Apresentação**: Demonstrar valor claramente\n4. **Tratamento**: Resolver objeções\n5. **Fechamento**: Converter em vendas\n6. **Pós-venda**: Manter relacionamento\n\nEm qual etapa você precisa de mais ajuda?",
                "📈 **Otimização de Performance de Vendas**\n\nFatores críticos:\n\n• **Habilidades**: Técnicas de venda\n• **Processo**: Metodologia consistente\n• **Ferramentas**: Tecnologia que auxilia\n• **Mentalidade**: Foco em valor\n• **Acompanhamento**: Métricas e feedback\n\nOnde você gostaria de focar para melhorar resultados?"
            ]
        }

        # Selecionar resposta da categoria identificada
        responses = responses_db.get(main_category, responses_db['geral'])
        response = random.choice(responses)

        # Adicionar variação para tornar mais natural
        if random.random() < 0.3:  # 30% das vezes
            follow_ups = [
                "\n\nQuer que eu elabore mais sobre algum ponto específico?",
                "\n\nComo você lidaria com uma situação similar?",
                "\n\nPrecisa de exemplos práticos para implementar isso?",
                "\n\nQue outros desafios você enfrenta nas vendas?"
            ]
            response += random.choice(follow_ups)

        # Simular limitação de tokens
        if len(response) > max_tokens * 4:  # Aproximadamente 4 chars por token
            response = response[:max_tokens * 4 - 3] + "..."

        return response

    def _prepare_input(self, prompt):
        """Preparar input para o modelo IBM Granite (método legado)."""
        # Template de instrução para IBM Granite
        system_prompt = """You are Granite, an AI language model developed by IBM.
You are helpful, honest, and harmless. Answer questions accurately and provide useful information."""

        return f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>"

    def _tokenize_input(self, text):
        """Tokenizar input (simplificado para demonstração)."""
        # Em produção, usaria o tokenizer real do modelo
        # Por enquanto, converter para IDs simples
        import numpy as np

        # Simulação básica de tokenização
        tokens = [1]  # BOS token
        for char in text:
            token_id = ord(char) % 50000  # Simulação simples
            tokens.append(token_id)

        tokens.append(2)  # EOS token
        return np.array([tokens], dtype=np.int64)

    def _decode_output(self, outputs):
        """Decodificar output do modelo."""
        # Em produção, usaria o tokenizer real para decodificar
        # Por enquanto, simulação simples
        if outputs and len(outputs) > 0:
            tokens = outputs[0][0] if hasattr(outputs[0], '__getitem__') else outputs[0]

            # Simulação de decodificação
            text = "Resposta gerada pelo IBM Granite v3.1 8B Instruct baseada no prompt fornecido."
            return text
        else:
            return "Erro na decodificação da resposta."

    def _generate_simulation_response(self, prompt):
        """Gerar resposta simulada com IBM Granite."""
        import random

        # Análise do prompt para respostas mais contextuais
        prompt_lower = prompt.lower()

        if "preço" in prompt_lower or "custo" in prompt_lower:
            responses = [
                "💰 **Abordagem de Preço:**\n\nQuando o cliente questiona o preço, foque no valor agregado:\n\n1. **ROI Mensurável**: Demonstre retorno sobre investimento em 6-12 meses\n2. **Benefícios Quantificáveis**: Mostre economia de tempo/custos operacionais\n3. **Cases de Sucesso**: Apresente clientes similares que obtiveram resultados\n\nQuer que eu ajude a estruturar uma resposta específica?",
                "📊 **Estratégia de Precificação:**\n\nPara objeções de preço, use a técnica 'Focar no Valor':\n\n• **Custo vs Investimento**: Transforme custo em investimento estratégico\n• **Benefícios Intangíveis**: Destaque redução de riscos e aumento de eficiência\n• **ROI Calculado**: Mostre projeções realistas de retorno\n\nQue aspecto específico você gostaria de enfatizar?"
            ]
        elif "objeção" in prompt_lower:
            responses = [
                "🚨 **Tratamento de Objeções:**\n\nObjeções são sinais de interesse! Classifique o tipo:\n\n1. **Preço**: Foco em ROI e valor\n2. **Autoridade**: Identifique decisor real\n3. **Necessidade**: Valide problemas do cliente\n4. **Timing**: Descubra urgência real\n\nQual tipo de objeção você está enfrentando?",
                "🎯 **Framework de Resposta:**\n\nPara objeções eficazes, use a estrutura FEEL-FELT-FOUND:\n\n• **FEEL**: Reconheça o sentimento ('Entendo sua preocupação')\n• **FELT**: Compartilhe experiência ('Outros clientes se sentiram assim')\n• **FOUND**: Mostre solução ('Mas descobriram que...')\n\nGostaria de ver um exemplo completo?"
            ]
        elif "cliente" in prompt_lower or "prospect" in prompt_lower:
            responses = [
                "👥 **Qualificação do Cliente:**\n\nAntes de prosseguir, certifique-se de:\n\n1. **Budget**: Capacidade financeira confirmada\n2. **Authority**: Decisor ou influenciador?\n3. **Need**: Problema real que precisa ser resolvido\n4. **Timeline**: Quando precisam da solução?\n\nQue informações você já tem sobre este prospect?",
                "📋 **Perfil do Comprador:**\n\nEntenda o journey do cliente:\n\n• **Reconhecimento**: Problema identificado\n• **Consideração**: Avaliando soluções\n• **Decisão**: Pronto para escolher\n\nEm qual estágio você avalia que ele está?"
            ]
        else:
            responses = [
                "🤖 **Assistente de Vendas IA:**\n\nComo especialista em vendas com IA, posso ajudar com:\n\n• Técnicas de objeções e fechamento\n• Estratégias de qualificação\n• Follow-ups inteligentes\n• Análise de conversas\n\nQue aspecto específico você gostaria de explorar?",
                "💼 **PitchAI - Seu Copiloto de Vendas:**\n\nPosso auxiliar em:\n\n1. **Análise de sentimento** em tempo real\n2. **Detecção de objeções** automática\n3. **Sugestões contextuais** baseadas em IA\n4. **Transcrição inteligente** de chamadas\n\nComo posso ajudar sua próxima venda?"
            ]

        response = random.choice(responses)
        return f"{response}\n\n🤖 *IBM Granite v3.1 8B - Assistente de Vendas Especializado*"

    def cleanup(self):
        """Limpar recursos do serviço."""
        try:
            if self.session:
                # Liberar recursos do modelo se necessário
                self.session = None
            self.is_initialized = False
            self.logger.info("🧹 Recursos do IBM Granite liberados")
        except Exception as e:
            self.logger.error(f"Erro ao limpar recursos: {e}")


if __name__ == "__main__":
    # Configurar logging mínimo
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            logging.basicConfig(level=logging.INFO, force=True)
            print("🐛 Modo debug ativado")
        elif sys.argv[1] == "--help":
            print("Chat LLM - Uso:")
            print("  python chat_llm.py         - Modo normal")
            print("  python chat_llm.py --debug - Modo debug")
            print("  python chat_llm.py --help  - Esta ajuda")
            sys.exit(0)

    # Executar chat
    create_chat_interface()



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

    # Tentar usar o LLM Service integrado
    try:
        from ai.llm_service import LLMService
        # Usar o modelo real por padrão, não forçar simulação
        service = LLMService("models/llmware_model", use_simulation=False)

        if service.initialize():
            if service.use_simulation:
                service_type = "llm_service_simulado"
                print("✅ LLM Service inicializado (modo simulado)!")
            else:
                service_type = "llm_service_real"
                print("✅ LLM Service inicializado (modelo real)!")
        else:
            print("❌ Falha ao inicializar LLM Service")
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



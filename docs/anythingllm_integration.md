# Integração com AnythingLLM

## Visão Geral

O PitchAI integra com o **AnythingLLM** como orquestrador de LLMs locais para geração de sugestões de objeções e resumos pós-chamada. Esta integração segue a **estratégia A** (RAG no app) para máxima privacidade e controle.

## Arquitetura

```
[Detecção de Objeção] → [RAG Service] → [AnythingLLM] → [Sugestões]
                              ↓
                    [Base de Conhecimento Local]
```

### Componentes

- **AnythingLLMClient**: Cliente para API OpenAI-compatível
- **RAGService**: Serviço de recuperação e geração
- **RAGSuggestionsWidget**: Interface para exibir sugestões
- **Base de Conhecimento**: Passagens locais para RAG

## Configuração do AnythingLLM

### 1. Instalação

```bash
# Opção 1: Desktop App (recomendado)
# Baixar de: https://anything-llm.com/

# Opção 2: Docker
docker run -d \
  --name anything-llm \
  -p 3001:3001 \
  -v anything-llm:/app/server/storage \
  anything-llm/anything-llm:latest
```

### 2. Configuração do Provedor Local

#### Ollama (Mais Simples)

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama3:instruct

# Verificar se está rodando
ollama list
```

#### LM Studio (OpenAI-compatível)

1. Baixar LM Studio
2. Baixar modelo GGUF (ex: llama-3-8b-instruct.gguf)
3. Iniciar servidor local na porta 1234
4. Configurar AnythingLLM para usar endpoint local

#### Llama.cpp Server

```bash
# Compilar llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Iniciar servidor
./server -m models/llama-3-8b-instruct.gguf -c 2048 -ngl 35
```

### 3. Configuração no AnythingLLM

1. Acessar `http://localhost:3001`
2. Criar workspace "PitchAI"
3. Configurar provedor local (Ollama/LM Studio/llama.cpp)
4. Selecionar modelo padrão
5. Desativar telemetria (opcional)

## Configuração do PitchAI

### Variáveis de Ambiente

```bash
# Configurações AnythingLLM
export ANYTHINGLLM_URL="http://127.0.0.1:3001"
export ANYTHINGLLM_API_KEY="local-dev"
export ANYTHINGLLM_TIMEOUT="2.0"
export ANYTHINGLLM_MODEL="llama3:instruct"
```

### Dependências

```bash
# Instalar dependências
pip install sseclient-py requests

# Ou via requirements.txt
pip install -r requirements.txt
```

## Uso

### 1. Iniciar AnythingLLM

```bash
# Desktop App
# Abrir AnythingLLM Desktop

# Docker
docker start anything-llm

# Ollama
ollama serve
```

### 2. Iniciar PitchAI

```bash
cd PitchAI
python src/main.py
```

### 3. Testar Integração

1. Iniciar gravação no PitchAI
2. Falar uma objeção (ex: "O preço está muito alto")
3. Verificar se as sugestões RAG aparecem na interface
4. Usar F8 para navegar para a tela de sugestões

## Base de Conhecimento

### Estrutura Atual

O sistema inclui passagens pré-definidas para:

- **Preço**: Estratégias de valor, flexibilidade de pagamento
- **Timing**: Urgência, oportunidades limitadas
- **Autoridade**: Tomada de decisão, stakeholders
- **Necessidade**: Descoberta de necessidades, casos de sucesso
- **Geral**: Técnicas de comunicação

### Adicionar Conteúdo

Para adicionar novas passagens, edite `src/ai/rag_service.py`:

```python
self.knowledge_base = [
    {
        "id": "novo_001",
        "title": "Título da Passagem",
        "content": "Conteúdo da passagem...",
        "category": "categoria"
    },
    # ... mais passagens
]
```

## Monitoramento

### Logs

```bash
# Verificar logs do PitchAI
tail -f logs/pitchai.log

# Verificar logs do AnythingLLM
# Desktop: Console da aplicação
# Docker: docker logs anything-llm
```

### Métricas

- **Latência**: Tempo de resposta do LLM
- **Disponibilidade**: Status do AnythingLLM
- **Fallback**: Uso de snippets quando LLM não disponível

## Troubleshooting

### Problema: AnythingLLM não conecta

```bash
# Verificar se está rodando
curl http://localhost:3001/v1/models

# Verificar logs
docker logs anything-llm  # se usando Docker
```

### Problema: Modelo não encontrado

```bash
# Verificar modelos disponíveis
curl http://localhost:3001/v1/models

# Verificar Ollama
ollama list
```

### Problema: Timeout

```bash
# Aumentar timeout
export ANYTHINGLLM_TIMEOUT="5.0"

# Verificar recursos do sistema
# CPU/GPU podem estar sobrecarregados
```

### Problema: Sugestões vazias

1. Verificar se há passagens na base de conhecimento
2. Verificar classificação da objeção
3. Verificar logs do RAG Service

## Desenvolvimento

### Estrutura de Arquivos

```
src/ai/
├── anythingllm_client.py    # Cliente AnythingLLM
├── rag_service.py          # Serviço RAG
└── ...

src/ui/
├── rag_suggestions_widget.py  # Interface RAG
└── ...

src/core/
├── application.py          # Integração principal
└── config.py              # Configurações
```

### Testes

```bash
# Testar cliente AnythingLLM
python -c "
from src.ai.anythingllm_client import AnythingLLMClient
client = AnythingLLMClient()
print('Status:', client.health_check())
"

# Testar RAG Service
python -c "
from src.ai.rag_service import RAGService, ObjectionEvent
from src.core.config import create_config

config = create_config()
rag = RAGService(config)

event = ObjectionEvent(
    call_id='test',
    category='preco',
    text='O preço está alto',
    context_snippet='O preço está alto',
    timestamp_ms=1234567890
)

rag.process_objection(event)
"
```

## Próximos Passos

1. **Base de Conhecimento Expandida**: Integrar com banco de dados
2. **Busca Semântica**: Implementar FAISS/sqlite-vss
3. **Fine-tuning**: Ajustar prompts para domínio específico
4. **Cache**: Implementar cache de sugestões
5. **Métricas**: Dashboard de performance do RAG 
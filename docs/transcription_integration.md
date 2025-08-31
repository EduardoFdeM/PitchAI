# Integração Frontend + Backend - Transcrição e Resumos

## 🎯 Visão Geral

Este documento descreve a integração completa entre frontend PyQt6 e backend para transcrição em tempo real e geração de resumos pós-reunião.

## 🏗️ Arquitetura da Integração

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MainWindow    │────│ IntegrationCtrl  │────│  DatabaseMgr    │
│   (PyQt6)       │    │  (Qt Signals)    │    │   (SQLite)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│TranscriptionWgt │────│TranscriptionSvc  │────│   LLM Service   │
│   (UI)          │    │  (Whisper)       │    │   (Llama 3.2)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Summary Service │
                                               │   (Post-call)   │
                                               └─────────────────┘
```

## 🔧 Componentes Principais

### 1. TranscriptionWidget (`src/ui/transcription_widget.py`)

**Funcionalidades:**
- ✅ Exibição de transcrição em tempo real
- ✅ Identificação de falantes (Vendedor/Cliente)
- ✅ Botões de salvar e gerar resumo
- ✅ Status em tempo real
- ✅ Integração com BD para armazenamento

**Sinais emitidos:**
- `transcription_saved(call_id)` - Quando transcrição é salva
- `summary_requested(call_id)` - Quando usuário solicita resumo

**Métodos principais:**
- `start_recording(call_id)` - Iniciar gravação
- `stop_recording()` - Parar gravação
- `set_summary_result(summary)` - Exibir resultado do resumo

### 2. IntegrationController (`src/ui/integration_controller.py`)

**Responsabilidades:**
- ✅ Coordenação entre todos os serviços
- ✅ Gerenciamento de estado da aplicação
- ✅ Conexão de sinais entre componentes
- ✅ Tratamento de erros centralizado

**Serviços gerenciados:**
- AudioCapture (captura de áudio)
- TranscriptionService (Whisper)
- LLMService (Llama 3.2)
- SentimentService (análise emocional)
- DatabaseManager (armazenamento)
- PostCallSummaryService (resumos)

### 3. DatabaseManager (`src/data/database.py`)

**Tabelas utilizadas:**
```sql
-- Transcrições
CREATE TABLE transcriptions (
    id INTEGER PRIMARY KEY,
    call_id TEXT NOT NULL,
    text TEXT NOT NULL,
    speaker TEXT,
    timestamp REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessões
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    status TEXT
);
```

**Métodos de armazenamento:**
- `save_transcription(call_id, text, speaker, timestamp)` - Salvar transcrição
- `get_transcription(call_id)` - Recuperar transcrição
- `get_session_summary(session_id)` - Obter resumo da sessão

## 🚀 Como Usar

### 1. Inicialização

```python
from src.ui.integration_controller import IntegrationController
from src.core.config import create_config

# Criar configuração
config = create_config()

# Inicializar controlador
controller = IntegrationController(config)
controller.initialize()

# Conectar widget de transcrição
transcription_widget = TranscriptionWidget(config)
controller.connect_transcription_widget(transcription_widget)
```

### 2. Fluxo de Uso

```python
# 1. Iniciar captura
call_id = "call_123"
controller.start_capture()

# 2. Iniciar transcrição
transcription_widget.start_recording(call_id)

# 3. Transcrição aparece automaticamente via sinais
# controller.transcription_updated.emit(chunk)

# 4. Salvar transcrição
transcription_widget._save_transcription()  # Via botão da UI

# 5. Gerar resumo pós-reunião
transcription_widget._generate_summary()  # Via botão da UI

# 6. Parar captura
controller.stop_capture()
transcription_widget.stop_recording()
```

### 3. Sinais e Conexões

```python
# No MainWindow ou widget pai
controller.transcription_updated.connect(on_transcription_update)
controller.summary_generated.connect(on_summary_generated)
controller.error_occurred.connect(on_error)

def on_transcription_update(chunk):
    print(f"Nova transcrição: {chunk.text}")

def on_summary_generated(summary):
    print(f"Resumo gerado: {summary['key_points']}")

def on_error(error_msg):
    print(f"Erro: {error_msg}")
```

## 📊 Funcionalidades de Resumo

### Estrutura do Resumo

```json
{
  "call_id": "call_123",
  "key_points": [
    "Cliente mencionou orçamento de R$ 50-80k",
    "Interesse em integração com sistema atual",
    "Prazo desejado: Q2"
  ],
  "objections": [
    {
      "type": "preco",
      "handled": true,
      "note": "ROI de 18 meses explicado"
    }
  ],
  "next_steps": [
    {
      "desc": "Enviar proposta técnica",
      "due": "2025-01-20",
      "owner": "vendedor"
    }
  ],
  "metrics": {
    "talk_time_vendor_pct": 45.2,
    "talk_time_client_pct": 54.8,
    "sentiment_avg": 0.78,
    "buying_signals": 3,
    "objections_total": 2,
    "objections_resolved": 2
  }
}
```

### Geração Automática

O resumo é gerado automaticamente quando:
1. ✅ Usuário clica no botão "📋 Resumo"
2. ✅ Sistema consolida dados da transcrição
3. ✅ LLM analisa conteúdo e gera estrutura JSON
4. ✅ Resultado é exibido na própria área de transcrição

## 🎨 Interface do Usuário

### TranscriptionWidget

```
┌─────────────────────────────────────────────────┐
│ 🎤 Transcrição em Tempo Real         💾 Salvar 📋 Resumo │
├─────────────────────────────────────────────────┤
│ [14:32:15] 👤 Vendedor: Olá! Como vai?         │
│ [14:32:18] 🎯 Cliente: Bem, obrigado!          │
│ [14:32:22] 👤 Vendedor: Ótimo! Sobre o projeto │
│                                                │
│ ⏹️ Gravação parada                              │
└─────────────────────────────────────────────────┘
```

### Após Gerar Resumo

```
┌─────────────────────────────────────────────────┐
│ 🎤 Transcrição em Tempo Real         💾 Salvar 📋 Resumo │
├─────────────────────────────────────────────────┤
│ [14:32:15] 👤 Vendedor: Olá! Como vai?         │
│ [14:32:18] 🎯 Cliente: Bem, obrigado!          │
│ ...                                            │
│                                                │
│ ✅ Resumo gerado com sucesso                   │
│                                                │
│ 📋 RESUMO DA REUNIÃO                           │
│ ==============================================  │
│ 🎯 PONTOS PRINCIPAIS:                          │
│ • Cliente interessado em solução               │
│ • Orçamento disponível: R$ 50-80k              │
│                                                │
│ 📝 PRÓXIMOS PASSOS:                            │
│ • Enviar proposta técnica (Prazo: 2025-01-20)  │
└─────────────────────────────────────────────────┘
```

## 🔍 Debugging e Monitoramento

### Logs Disponíveis

```python
# Habilitar logs detalhados
import logging
logging.basicConfig(level=logging.INFO)

# Logs do IntegrationController
controller.logger.info("Estado do sistema")

# Logs do TranscriptionWidget
transcription_widget.logger.info("Transcrição salva")

# Logs do DatabaseManager
database_manager.logger.info("BD inicializado")
```

### Métricas de Performance

- **Latência de transcrição**: <200ms (Whisper NPU)
- **Tempo de geração de resumo**: <3s (LLM local)
- **Armazenamento BD**: ~1KB por minuto de transcrição

## 🚨 Tratamento de Erros

### Cenários Comuns

1. **BD não disponível**: Sistema funciona em modo offline
2. **LLM não inicializado**: Resumos usam templates estáticos
3. **Captura de áudio falha**: Notificação visual + retry automático
4. **Rede indisponível**: Processamento 100% local

### Recuperação Automática

```python
try:
    controller.start_capture()
except Exception as e:
    # Fallback para modo simulação
    controller.start_simulation_mode()
```

## 📚 Próximos Passos

1. **Otimização NPU**: Migrar para QNN Execution Provider
2. **Cache Inteligente**: Implementar cache de embeddings
3. **Análise Avançada**: Adicionar análise de sentimento em tempo real
4. **Exportação**: PDF/Markdown dos resumos
5. **Sincronização**: Integração com CRM externo

---

## 🎯 Conclusão

A integração frontend/backend está **completa e funcional**, proporcionando:

- ✅ **Transcrição em tempo real** com Whisper Large
- ✅ **Armazenamento automático** no SQLite
- ✅ **Geração de resumos** pós-reunião via LLM local
- ✅ **Interface responsiva** com feedback visual
- ✅ **Tratamento robusto** de erros e fallbacks
- ✅ **Arquitetura modular** para futuras expansões

O sistema está pronto para uso em produção com dependências reais ou em modo simulação para desenvolvimento.

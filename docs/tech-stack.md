# PitchAI - Stack Tecnológica Detalhada

## 🎯 Visão Geral da Stack

A stack do PitchAI foi cuidadosamente escolhida para maximizar o aproveitamento da NPU Snapdragon X, garantindo performance excepcional e experiência fluida.

---

## 🧠 AI & Machine Learning

### **ONNX Runtime + QNN Execution Provider**
- **Versão**: 1.16.0+
- **Provedor**: QNN (Qualcomm Neural Network) + CPUExecutionProvider
- **Propósito**: Interface oficial para NPU Snapdragon X + fallback CPU
- **Vantagens**:
  - Acesso direto à NPU com latência ultra-baixa
  - Otimizações específicas para hardware Qualcomm
  - Suporte nativo para múltiplos modelos simultâneos
  - Estratégia robusta de fallback (NPU → CPU)
  - Eficiência energética superior (10x vs GPU)

### **AnythingLLM + Llama 3.2 3B**
- **Versão**: Client 0.1.0+
- **Propósito**: IA conversacional 100% offline
- **Características**:
  - Llama 3.2 3B quantizado para Snapdragon X+
  - Processamento local sem dependências externas
  - Integração com RAG para objeções e sugestões
  - Context awareness para vendas
  - Fallback robusto (AnythingLLM → LLMWare → Simulação)

### **Modelos ONNX Otimizados** (IMPLEMENTADOS)
| Modelo | Tamanho | Propósito | Latência NPU | Status |
|--------|---------|-----------|--------------|---------|
| Whisper-base | 39MB | Transcrição em tempo real | <50ms | ✅ |
| DistilBERT-sentiment | 65MB | Análise de sentimento | <30ms | ✅ |
| BERT-objection | 110MB | Detecção de objeções | <40ms | ✅ |
| Wav2Vec2-emotion | 95MB | Análise emocional | <35ms | ✅ |
| ECAPA-TDNN | 85MB | Separação de falantes | <25ms | ✅ |
| Llama 3.2 3B | ~2GB | Geração de respostas | <200ms | ✅ |
| BART-large | 500MB | Resumos inteligentes | <150ms | ✅ |

---

## 🖥️ Frontend Framework

### **PyQt6 + EventBus Integration**
- **Versão**: 6.6.0+
- **Propósito**: Interface nativa moderna com comunicação thread-safe
- **Justificativa**:
  - Performance nativa superior ao Electron
  - Acesso direto a APIs do Windows
  - Menor consumo de memória
  - Styling flexível (glassmorphism)
  - Thread safety para operações de IA
  - Integração nativa com EventBus

### **EventBus + Contracts System**
- **Propósito**: Comunicação thread-safe entre backend e UI
- **Componentes**:
  - EventBus: Sistema pub/sub thread-safe
  - Contracts: Payloads padronizados e imutáveis
  - UiBridge: Ponte PyQt6 ↔ EventBus
  - Debouncing: Performance otimizada
  - Error Handler: Recuperação automática

### **Arquitetura UI Completa**
```
MainWindow
├── EventBus Integration
│   ├── UiBridge (PyQt6 signals)
│   ├── Contracts System
│   └── Debouncing Manager
├── DashboardWidget (métricas NPU + Analytics)
├── TranscriptionWidget (texto em tempo real)
├── SuggestionsWidget (RAG + AnythingLLM)
├── HistoryWidget (SQLite + FTS5)
├── SummaryWidget (Resumos inteligentes)
└── ControlsWidget (controles principais)
```

---

## 💾 Data Management

### **SQLite + Advanced Features**
- **Versão**: 3.44.0+ (built-in Python)
- **Propósito**: Banco local completo para aplicação desktop
- **Esquema Completo**:
  - `transcriptions` - Histórico de transcrições com timestamps
  - `objections` - Base de objeções/respostas RAG
  - `analytics` - Métricas de performance e KPIs
  - `sentiment_samples` - Análise de sentimento em tempo real
  - `call_history` - Histórico completo de chamadas
  - `mentor_clients` - Perfis de clientes (Mentor Engine)
  - `disc_profiles` - Análise comportamental DISC
  - `xp_history` - Sistema de gamificação
  - `audit_log` - Logs de auditoria e segurança

### **FTS5 + Advanced Search**
- **Propósito**: Busca textual e semântica de alta performance
- **Características**:
  - Full-text search nativo do SQLite
  - Indexação automática de transcrições
  - Busca por relevância e contexto
  - Suporte a múltiplos idiomas

### **Cache Manager + Performance Monitor**
- **Propósito**: Aceleração e monitoramento de performance
- **Componentes**:
  - Cache multi-nível (memória → disco → compressão)
  - Redis-like interface local
  - TTL e políticas de eviction
  - Monitoramento de latência e throughput
  - Profiling de operações críticas

---

## 🎯 Advanced Systems

### **DISC System - Behavioral Analysis**
- **Propósito**: Análise comportamental do vendedor baseada em padrões linguísticos
- **Características**:
  - Extração de features de talk ratio, imperativos, perguntas
  - Cálculo de scores DISC (Dominância, Influência, Estabilidade, Consciência)
  - Identificação automática de pontos fortes e fraquezas
  - Recomendações de módulos de treino personalizados
  - Evolução contínua do perfil comportamental

### **Mentor Engine - Coaching Intelligence**
- **Propósito**: Sistema de coaching inteligente com gamificação
- **Características**:
  - Classificação automática de clientes (fácil/médio/difícil)
  - Sistema de XP e progressão de níveis (junior→mentor)
  - Feedback contextual em tempo real
  - Integração com DISC para coaching personalizado
  - Leaderboard e métricas de performance

### **Error Handler + Recovery System**
- **Propósito**: Tratamento robusto de erros e recuperação automática
- **Características**:
  - Estratégias de retry configuráveis
  - Recuperação automática de falhas
  - Logging estruturado e auditoria
  - Monitoramento de saúde do sistema
  - Fallbacks para componentes críticos

### **Contracts System - Type Safety**
- **Propósito**: Sistema de contratos imutáveis para comunicação
- **Características**:
  - Payloads padronizados para todos os eventos
  - Type safety em Python com dataclasses
  - Validação automática de dados
  - Documentação inline dos contratos
  - Facilita manutenção e debugging

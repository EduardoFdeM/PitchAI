# PitchAI - Stack Tecnológica Detalhada

## 🎯 Visão Geral da Stack

A stack do PitchAI foi cuidadosamente escolhida para maximizar o aproveitamento da NPU Snapdragon X, garantindo performance excepcional e experiência fluida.

---

## 🧠 AI & Machine Learning

### **ONNX Runtime + QNN Execution Provider**
- **Versão**: 1.16.0+
- **Provedor**: QNN (Qualcomm Neural Network)
- **Propósito**: Interface oficial para NPU Snapdragon X
- **Vantagens**:
  - Acesso direto à NPU com latência ultra-baixa
  - Otimizações específicas para hardware Qualcomm
  - Suporte nativo para múltiplos modelos simultâneos
  - Eficiência energética superior (10x vs GPU)

### **Modelos ONNX Otimizados** (SUGESTÕES)
| Modelo | Tamanho | Propósito | Latência NPU |
|--------|---------|-----------|--------------|
| Whisper-base | 39MB | Transcrição de fala | <50ms |
| DistilBERT-sentiment | 65MB | Análise de sentimento | <30ms |
| BERT-NER | 110MB | Detecção de entidades | <40ms |
| Wav2Vec2-emotion | 95MB | Análise emocional | <35ms |
| ECAPA-TDNN | 85MB | Separação de falantes | <25ms |

---

## 🖥️ Frontend Framework

### **PyQt6**
- **Versão**: 6.6.0+
- **Propósito**: Interface nativa moderna
- **Justificativa**:
  - Performance nativa superior ao Electron
  - Acesso direto a APIs do Windows
  - Menor consumo de memória
  - Styling flexível (glassmorphism)
  - Thread safety para operações de IA

### **Arquitetura UI**
```
MainWindow
├── DashboardWidget (métricas NPU)
├── TranscriptionWidget (texto em tempo real)
├── SuggestionsWidget (Sugestões com IA)
└── ControlsWidget (controles principais)
```

---

## 💾 Data Management

### **SQLite**
- **Versão**: 3.44.0+ (built-in Python)
- **Propósito**: Banco local para aplicação desktop
- **Esquema**:
  - `transcriptions` - Histórico de transcrições
  - `objections` - Base de objeções/respostas
  - `analytics` - Métricas de performance
  - `settings` - Configurações do usuário

# Feature 3 — Análise de Sentimento Multi-Dimensional
## Plano de Implementação Detalhado

### 📋 **Visão Geral**
Implementação da Feature 3 que combina análise de texto, prosódia e expressões faciais para inferir sentimento e engajamento do cliente em tempo real.

---

## 🎯 **Objetivos da Implementação**

### **Principais:**
- ✅ Inferir sentimento (-1 a +1) e engajamento (0 a 1) em tempo real
- ✅ Detectar palavras-gatilho e gerar alertas contextuais
- ✅ Dashboard visual com métricas e sparklines
- ✅ Integração com Features 1 e 2 (áudio + transcrição)
- ✅ Execução na NPU para baixa latência (≤ 500ms)

### **Secundários:**
- ✅ Suporte opcional a análise facial (opt-in)
- ✅ Fusão configurável de múltiplas fontes
- ✅ Persistência para Features 5 e 6
- ✅ Degradação graciosa sem vídeo

---

## 🏗️ **Arquitetura da Implementação**

### **Estrutura de Arquivos:**
```
src/ai/
├── sentiment/
│   ├── __init__.py
│   ├── sentiment_service.py      # Serviço principal
│   ├── text_analyzer.py          # RF-3.1: Motor textual
│   ├── prosody_analyzer.py       # RF-3.2: Motor de prosódia
│   ├── vision_analyzer.py        # RF-3.3: Motor de visão (opcional)
│   ├── fusion_engine.py          # RF-3.4: Fusão de dados
│   ├── keyword_detector.py       # Detecção de palavras-gatilho
│   └── models/
│       ├── distilbert_sentiment.onnx
│       ├── prosody_classifier.onnx
│       └── face_expression.onnx
```

### **Componentes Principais:**

#### **1. SentimentService (sentiment_service.py)**
```python
class SentimentService(QObject):
    """Serviço principal de análise de sentimento."""
    
    # Sinais
    sentiment_updated = pyqtSignal(SentimentSample)
    alert_triggered = pyqtSignal(SentimentEvent)
    dashboard_updated = pyqtSignal(DashboardData)
    
    def __init__(self, config, model_manager):
        self.text_analyzer = TextAnalyzer()
        self.prosody_analyzer = ProsodyAnalyzer()
        self.vision_analyzer = VisionAnalyzer()  # opcional
        self.fusion_engine = FusionEngine()
        self.keyword_detector = KeywordDetector()
```

#### **2. TextAnalyzer (text_analyzer.py)**
```python
class TextAnalyzer:
    """RF-3.1: Motor textual (NLP)"""
    
    def analyze_sentiment(self, text: str) -> float:
        """Inferir sentimento de texto (-1 a +1)."""
        
    def detect_keywords(self, text: str) -> List[KeywordMatch]:
        """Detectar palavras-gatilho."""
        
    def calculate_engagement(self, text: str) -> float:
        """Calcular engajamento textual."""
```

#### **3. ProsodyAnalyzer (prosody_analyzer.py)**
```python
class ProsodyAnalyzer:
    """RF-3.2: Motor de prosódia (áudio)"""
    
    def extract_features(self, audio: np.ndarray) -> ProsodyFeatures:
        """Extrair F0, energia, ritmo."""
        
    def classify_valence(self, features: ProsodyFeatures) -> float:
        """Classificar valência (-1 a +1)."""
        
    def detect_micro_expressions(self, features: ProsodyFeatures) -> List[str]:
        """Detectar micro-expressões vocais."""
```

#### **4. VisionAnalyzer (vision_analyzer.py)**
```python
class VisionAnalyzer:
    """RF-3.3: Motor de visão (opcional)"""
    
    def __init__(self, opt_in: bool = False):
        self.enabled = opt_in
        
    def detect_faces(self, frame: np.ndarray) -> List[Face]:
        """Detectar faces na imagem."""
        
    def classify_expressions(self, faces: List[Face]) -> List[Expression]:
        """Classificar expressões faciais."""
```

#### **5. FusionEngine (fusion_engine.py)**
```python
class FusionEngine:
    """RF-3.4: Fusão de dados"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {"text": 0.5, "voice": 0.3, "vision": 0.2}
        
    def fuse_sentiment(self, text_score: float, voice_score: float, 
                      vision_score: Optional[float] = None) -> float:
        """Fundir scores de sentimento."""
        
    def fuse_engagement(self, text_eng: float, voice_eng: float,
                       vision_eng: Optional[float] = None) -> float:
        """Fundir scores de engajamento."""
```

---

## 📊 **Modelo de Dados**

### **Estruturas Principais:**
```python
@dataclass
class SentimentSample:
    """Amostra de sentimento conforme SRS."""
    id: str
    call_id: str
    ts_start_ms: int
    ts_end_ms: int
    score_valence: float          # -1..+1
    score_engagement: float       # 0..1
    weights: Dict[str, float]     # pesos usados na fusão
    details: Dict[str, Any]       # confidences, features, labels

@dataclass
class SentimentEvent:
    """Evento de sentimento (alerta, sinal)."""
    id: str
    call_id: str
    ts_ms: int
    kind: str                     # 'buying_signal'|'risk'|'keyword'|'alert'
    label: str                    # "preco", "ROI", "piloto"
    strength: float               # 0..1

@dataclass
class DashboardData:
    """Dados para o dashboard em tempo real."""
    sentiment_percent: int        # 0-100
    engagement_percent: int       # 0-100
    buying_signals_count: int
    alerts: List[Dict[str, Any]]
    sparkline_data: List[float]   # últimos 90s
```

### **Schema SQL:**
```sql
-- Tabela de amostras de sentimento
CREATE TABLE sentiment_sample (
  id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  ts_start_ms INTEGER NOT NULL,
  ts_end_ms INTEGER NOT NULL,
  score_valence REAL NOT NULL,   -- -1..+1
  score_engagement REAL,         -- 0..1
  src_text REAL,                 -- peso usado na fusão
  src_voice REAL,
  src_vision REAL,
  details_json TEXT,             -- confidences, features, labels
  FOREIGN KEY (call_id) REFERENCES call(id) ON DELETE CASCADE
);

-- Tabela de eventos de sentimento
CREATE TABLE sentiment_event (
  id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  ts_ms INTEGER NOT NULL,
  kind TEXT,         -- buying_signal|risk|keyword|alert
  label TEXT,        -- "preco", "ROI", "piloto"
  strength REAL,     -- 0..1
  FOREIGN KEY (call_id) REFERENCES call(id) ON DELETE CASCADE
);
```

---

## 🔄 **Fluxo de Processamento**

### **Pipeline Principal:**
```
[Feature 2: TranscriptChunk] → [TextAnalyzer] → [SentimentScore]
[Feature 1: AudioChunk] → [ProsodyAnalyzer] → [ValenceScore]
[Video Frame] → [VisionAnalyzer] → [ExpressionScore] (opcional)
                                    ↓
[FusionEngine] → [SentimentSample] → [Dashboard] + [Storage]
                                    ↓
[KeywordDetector] → [SentimentEvent] → [Alert] + [Storage]
```

### **Sequência Detalhada:**
1. **Receber dados** das Features 1 e 2
2. **Processar em paralelo** na NPU:
   - Texto → sentimento + keywords
   - Áudio → prosódia + micro-expressões
   - Vídeo → expressões faciais (se habilitado)
3. **Fundir resultados** com pesos configuráveis
4. **Gerar amostra** de sentimento
5. **Detectar alertas** e sinais de compra
6. **Atualizar dashboard** em tempo real
7. **Persistir dados** para histórico

---

## 🎨 **Interface do Dashboard**

### **Componente UI (sentiment_widget.py):**
```python
class SentimentWidget(QWidget):
    """Widget do dashboard de sentimento."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface."""
        # Layout principal
        layout = QVBoxLayout()
        
        # Métricas principais
        self.sentiment_label = QLabel("😊 Sentimento: 72%")
        self.engagement_label = QLabel("🎯 Engajamento: 85%")
        self.signals_label = QLabel("⚡ Sinais de compra: 3")
        
        # Sparklines (últimos 90s)
        self.sentiment_sparkline = SparklineWidget()
        self.engagement_sparkline = SparklineWidget()
        
        # Alertas
        self.alerts_list = QListWidget()
        
        # Configurações
        self.vision_checkbox = QCheckBox("Análise facial (opt-in)")
```

### **Design Visual:**
```
┌─────────────────────────────────────┐
│ 😊 Sentimento: 72% positivo        │
│ 🎯 Engajamento: 85% alto           │
│ ⚡ Sinais de compra: 3 detectados  │
├─────────────────────────────────────┤
│ 📈 Histórico (90s):                │
│ Sentimento: ▁▂▃▅▂▁▂▃▅▂▁           │
│ Engajamento: ▁▂▃▅▂▁▂▃▅▂▁          │
├─────────────────────────────────────┤
│ 🚨 Alertas:                        │
│ • "preço" mencionado 2x            │
│ • "contrato" mencionado 1x         │
└─────────────────────────────────────┘
```

---

## ⚙️ **Configuração e Modelos**

### **Modelos ONNX Necessários:**
```json
{
  "distilbert_sentiment": {
    "path": "models/distilbert_sentiment.onnx",
    "ep": ["QNN", "CPU"],
    "input": "text_tokens",
    "quant": "int8_fp16",
    "description": "DistilBERT para análise de sentimento",
    "size_mb": 65,
    "latency_target_ms": 30
  },
  "prosody_classifier": {
    "path": "models/prosody_classifier.onnx",
    "ep": ["QNN", "CPU"],
    "input": "audio_features",
    "quant": "int8_fp16",
    "description": "Classificador de prosódia",
    "size_mb": 25,
    "latency_target_ms": 20
  },
  "face_expression": {
    "path": "models/face_expression.onnx",
    "ep": ["QNN", "CPU"],
    "input": "face_image",
    "quant": "int8_fp16",
    "description": "Classificador de expressões faciais",
    "size_mb": 45,
    "latency_target_ms": 40
  }
}
```

### **Configurações:**
```python
@dataclass
class SentimentConfig:
    """Configurações de sentimento."""
    # Pesos de fusão
    text_weight: float = 0.5
    voice_weight: float = 0.3
    vision_weight: float = 0.2
    
    # Janelas de análise
    text_window_s: float = 5.0
    prosody_window_s: float = 3.0
    vision_window_s: float = 1.0
    
    # Thresholds
    sentiment_threshold: float = 0.1
    engagement_threshold: float = 0.3
    alert_threshold: float = 0.7
    
    # Palavras-gatilho
    keywords: List[str] = field(default_factory=lambda: [
        "preço", "custo", "caro", "barato",
        "contrato", "acordo", "termos",
        "prazo", "tempo", "urgente",
        "piloto", "teste", "demonstração",
        "ROI", "retorno", "investimento"
    ])
```

---

## 🧪 **Testes e Validação**

### **Testes Unitários:**
```python
# test_sentiment_service.py
def test_text_analyzer():
    """Testar análise de texto."""
    analyzer = TextAnalyzer()
    score = analyzer.analyze_sentiment("Estou muito satisfeito")
    assert -1 <= score <= 1

def test_prosody_analyzer():
    """Testar análise de prosódia."""
    analyzer = ProsodyAnalyzer()
    features = analyzer.extract_features(audio_sample)
    assert features.f0 > 0

def test_fusion_engine():
    """Testar fusão de dados."""
    engine = FusionEngine()
    fused = engine.fuse_sentiment(0.8, 0.6, 0.7)
    assert -1 <= fused <= 1
```

### **Testes de Integração:**
```python
# test_sentiment_integration.py
def test_end_to_end_latency():
    """Testar latência end-to-end ≤ 500ms."""
    service = SentimentService(config)
    start_time = time.time()
    
    # Simular entrada
    service.process_text_chunk(text_chunk)
    service.process_audio_chunk(audio_chunk)
    
    # Aguardar resultado
    result = service.get_latest_sentiment()
    latency = (time.time() - start_time) * 1000
    
    assert latency <= 500  # ms
```

### **Testes de Performance:**
```python
def test_npu_utilization():
    """Testar uso da NPU."""
    # Monitorar uso de CPU/GPU durante inferência
    # Deve ser ≤ 10% CPU, ≈ 0% GPU
```

---

## 📅 **Cronograma de Implementação**

### **Fase 1: Fundação (Semana 1)**
- [ ] Criar estrutura de arquivos
- [ ] Implementar TextAnalyzer básico
- [ ] Implementar ProsodyAnalyzer básico
- [ ] Criar modelos de dados
- [ ] Testes unitários básicos

### **Fase 2: Core (Semana 2)**
- [ ] Implementar FusionEngine
- [ ] Implementar KeywordDetector
- [ ] Integrar com ModelManager
- [ ] Implementar SentimentService principal
- [ ] Testes de integração

### **Fase 3: UI e Polimento (Semana 3)**
- [ ] Implementar SentimentWidget
- [ ] Criar dashboard visual
- [ ] Implementar sparklines
- [ ] Adicionar configurações de opt-in
- [ ] Testes de UI

### **Fase 4: Otimização (Semana 4)**
- [ ] Otimizar para NPU
- [ ] Ajustar latência
- [ ] Implementar VisionAnalyzer (opcional)
- [ ] Testes de performance
- [ ] Documentação final

---

## 🎯 **Critérios de Sucesso**

### **Funcionais:**
- [ ] RF-3.1 a RF-3.6 implementados
- [ ] Dashboard em tempo real funcionando
- [ ] Detecção de palavras-gatilho ≥ 90% precisão
- [ ] Fusão de múltiplas fontes configurável

### **Não-Funcionais:**
- [ ] Latência ≤ 500ms (P95)
- [ ] Uso CPU ≤ 10% durante inferência
- [ ] Degradação graciosa sem vídeo
- [ ] Opt-in/opt-out para análise facial

### **Integração:**
- [ ] Compatível com Features 1 e 2
- [ ] Dados persistidos para Features 5 e 6
- [ ] EventBus funcionando
- [ ] ModelManager integrado

---

## 🚀 **Próximos Passos**

1. **Iniciar Fase 1** - Criar estrutura básica
2. **Configurar modelos ONNX** - DistilBERT, prosódia, face
3. **Implementar TextAnalyzer** - Primeiro componente
4. **Testar integração** - Com Features 1 e 2
5. **Iterar e otimizar** - Baseado em feedback

---

## 📚 **Referências Técnicas**

- **DistilBERT**: https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english
- **Prosódia**: https://github.com/facebookresearch/fairseq/tree/main/examples/wav2vec
- **Expressões Faciais**: https://github.com/opencv/opencv_contrib/tree/master/modules/face
- **ONNX Runtime**: https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html
- **PyQt6**: https://doc.qt.io/qtforpython-6/

---

*Este plano está alinhado com o SRS v1.0 da Feature 3 e integra-se perfeitamente com as Features 1 e 2 já implementadas.* 
# Guia de Quantização do Whisper Large para NPU
## Introdução à Quantização de Modelos Whisper ONNX

Este guia explica como baixar, organizar e quantizar o modelo Whisper Large ONNX para otimização em NPUs da Qualcomm (como Snapdragon X Elite).

## 1. Download e Organização dos Arquivos

### 1.1 Baixando o Whisper Large ONNX

O modelo Whisper Large ONNX está disponível no site da Qualcomm:
- **URL**: https://www.qualcomm.com/developer/software/qualcomm-ai-engine-direct
- **Procure por**: `whisper-large-v3-onnx` ou similar
- **Formato**: Arquivo ZIP contendo:
  - `whisper_encoder.onnx` (~1.5GB)
  - `whisper_decoder.onnx` (~1.5GB)
  - Arquivos auxiliares (.bin, configs, etc.)

### 1.2 Estrutura de Diretórios Recomendada

Após baixar e descompactar, organize os arquivos assim:

```
models/
├── whisper_large_onnx/
│   ├── encoder/
│   │   ├── whisper_encoder.onnx
│   │   └── whisper_encoder.bin (se presente)
│   ├── decoder/
│   │   ├── whisper_decoder.onnx
│   │   └── whisper_decoder.bin (se presente)
│   ├── tokenizer.json
│   ├── config.json
│   └── README.md
└── whisper_large_quantized/
    └── (arquivos quantizados serão colocados aqui)
```

### 1.3 Atualizando o Manifest

Adicione a entrada no `models/manifest.json`:

```json
{
  "whisper_large_encoder": {
    "path": "models/whisper_large_onnx/encoder/whisper_encoder.onnx",
    "ep": ["QNN", "CPU"],
    "input": "audio_16k_mono",
    "quant": "fp32",
    "description": "Encoder Whisper Large original (não quantizado)",
    "version": "3.0",
    "size_mb": 1500,
    "latency_target_ms": 500
  },
  "whisper_large_decoder": {
    "path": "models/whisper_large_onnx/decoder/whisper_decoder.onnx",
    "ep": ["QNN", "CPU"],
    "input": "tokens",
    "quant": "fp32",
    "description": "Decoder Whisper Large original (não quantizado)",
    "version": "3.0",
    "size_mb": 1500,
    "latency_target_ms": 200
  }
}
```

## 2. Processo de Quantização

### 2.1 Ferramentas Necessárias

Instale as dependências:

```bash
pip install onnx onnxruntime
pip install onnxruntime-qnn  # Para QNN EP (NPU)
```

### 2.2 Script de Quantização Personalizado

Use o script `scripts/quantize_whisper.py` (já criado anteriormente):

```bash
# Quantizar o encoder
python scripts/quantize_whisper.py \
    --input_model "models/whisper_large_onnx/encoder/whisper_encoder.onnx" \
    --output_model "models/whisper_large_quantized/whisper_encoder_int8.onnx" \
    --quantization_type "int8"

# Quantizar o decoder
python scripts/quantize_whisper.py \
    --input_model "models/whisper_large_onnx/decoder/whisper_decoder.onnx" \
    --output_model "models/whisper_large_quantized/whisper_decoder_int8.onnx" \
    --quantization_type "int8"
```

### 2.3 Tempo Estimado e Recursos

| Modelo | Tamanho Original | Tempo de Quantização | Tamanho Final | Redução |
|--------|------------------|---------------------|---------------|---------|
| Encoder | ~1.5GB | 10-20 min | ~400MB | ~73% |
| Decoder | ~1.5GB | 10-20 min | ~400MB | ~73% |

**Hardware recomendado para quantização:**
- RAM: Mínimo 8GB, recomendado 16GB
- CPU: Qualquer processador moderno
- Espaço em disco: 5GB livres

## 3. Validação Pós-Quantização

### 3.1 Script de Teste Simples

Crie um arquivo `test_whisper_quantized.py`:

```python
#!/usr/bin/env python3
import onnxruntime as ort
import numpy as np
import time

def test_quantized_model(model_path, input_shape):
    """Testa um modelo quantizado com entrada simulada."""
    try:
        # Carregar modelo
        session = ort.InferenceSession(
            model_path,
            providers=["QNNExecutionProvider", "CPUExecutionProvider"]
        )
        
        # Criar entrada simulada
        input_name = session.get_inputs()[0].name
        fake_input = np.random.randn(*input_shape).astype(np.float32)
        
        # Executar inferência
        start_time = time.time()
        outputs = session.run(None, {input_name: fake_input})
        inference_time = time.time() - start_time
        
        print(f"✅ Modelo '{model_path}' OK")
        print(f"   Tempo de inferência: {inference_time:.3f}s")
        print(f"   Forma de saída: {outputs[0].shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no modelo '{model_path}': {e}")
        return False

if __name__ == "__main__":
    # Testar encoder quantizado
    encoder_path = "models/whisper_large_quantized/whisper_encoder_int8.onnx"
    encoder_input_shape = (1, 80, 3000)  # (batch, mel_features, time_steps)
    
    # Testar decoder quantizado
    decoder_path = "models/whisper_large_quantized/whisper_decoder_int8.onnx"
    decoder_input_shape = (1, 1, 512)  # (batch, sequence, hidden_size)
    
    success = True
    success &= test_quantized_model(encoder_path, encoder_input_shape)
    success &= test_quantized_model(decoder_path, decoder_input_shape)
    
    if success:
        print("\n🎉 Todos os modelos quantizados estão funcionais!")
    else:
        print("\n💥 Alguns modelos falharam na validação.")
```

### 3.2 Integração no PitchAI

Após a quantização bem-sucedida, atualize o `models/manifest.json`:

```json
{
  "whisper_large_encoder_quantized": {
    "path": "models/whisper_large_quantized/whisper_encoder_int8.onnx",
    "ep": ["QNN", "CPU"],
    "input": "audio_16k_mono",
    "quant": "int8",
    "description": "Encoder Whisper Large quantizado para NPU",
    "version": "3.0-int8",
    "size_mb": 400,
    "latency_target_ms": 200
  },
  "whisper_large_decoder_quantized": {
    "path": "models/whisper_large_quantized/whisper_decoder_int8.onnx",
    "ep": ["QNN", "CPU"],
    "input": "tokens",
    "quant": "int8",
    "description": "Decoder Whisper Large quantizado para NPU",
    "version": "3.0-int8",
    "size_mb": 400,
    "latency_target_ms": 100
  }
}
```

## 4. Troubleshooting

### 4.1 Problemas Comuns

**Erro: "ONNX model too large"**
- Solução: Certifique-se de ter RAM suficiente (16GB+)
- Alternativa: Quantize em uma máquina com mais RAM

**Erro: "QNNExecutionProvider not found"**
- Solução: Instale `onnxruntime-qnn`
- Verifique se o driver da NPU está instalado

**Erro: "Invalid input shape"**
- Solução: Verifique a documentação do modelo original
- Use ferramentas como `netron` para inspecionar a arquitetura

### 4.2 Comandos de Diagnóstico

```bash
# Verificar providers disponíveis
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"

# Inspecionar modelo ONNX
pip install netron
netron models/whisper_large_onnx/encoder/whisper_encoder.onnx

# Verificar tamanho dos arquivos
ls -lh models/whisper_large_*/*
```

## 5. Performance Esperada

### 5.1 Benchmarks Estimados (Snapdragon X Elite)

| Modelo | Versão | Latência | Throughput | Qualidade |
|--------|--------|----------|------------|-----------|
| Whisper Large FP32 | Original | ~800ms | 2x real-time | 100% |
| Whisper Large INT8 | Quantizado | ~200ms | 8x real-time | ~98% |

### 5.2 Configuração Recomendada para Produção

```python
# Em src/ai/whisper_decoder.py
WHISPER_CONFIG = {
    "model_name": "whisper_large_quantized",
    "encoder_path": "models/whisper_large_quantized/whisper_encoder_int8.onnx",
    "decoder_path": "models/whisper_large_quantized/whisper_decoder_int8.onnx",
    "providers": ["QNNExecutionProvider", "CPUExecutionProvider"],
    "session_options": {
        "enable_cpu_mem_arena": False,
        "enable_mem_pattern": True,
        "execution_mode": "ORT_SEQUENTIAL"
    }
}
```

## 6. Próximos Passos

Após a quantização bem-sucedida:

1. **Integre no `whisper_decoder.py`**: Atualize o código para usar os modelos quantizados
2. **Teste com áudio real**: Valide a qualidade de transcrição
3. **Benchmark de performance**: Meça latência e throughput reais
4. **Otimize configurações**: Ajuste parâmetros da NPU para máxima performance

---

**Nota**: Este processo pode demorar 20-40 minutos no total, dependendo do hardware. A quantização é um processo único - depois de concluída, os modelos quantizados podem ser usados indefinidamente.

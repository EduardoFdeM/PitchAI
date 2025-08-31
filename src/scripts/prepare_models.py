"""
Script para preparar estrutura de modelos ONNX
============================================

Este script cria a estrutura necessária para os modelos ONNX
e documenta como integrar quando os modelos estiverem disponíveis.
"""

import os
import shutil
from pathlib import Path
import json


def create_models_structure():
    """Criar estrutura de diretórios para modelos."""
    
    print("📁 Criando estrutura de modelos...")
    
    # Diretório base
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Subdiretórios
    (models_dir / "whisper").mkdir(exist_ok=True)
    (models_dir / "sentiment").mkdir(exist_ok=True)
    (models_dir / "objection").mkdir(exist_ok=True)
    (models_dir / "speaker").mkdir(exist_ok=True)
    (models_dir / "llm").mkdir(exist_ok=True)
    
    print("✅ Estrutura de diretórios criada")
    
    # Criar arquivo de configuração
    config = {
        "models": {
            "whisper": {
                "file": "whisper_base.onnx",
                "description": "Modelo Whisper para transcrição de áudio",
                "input_format": "audio PCM 16-bit, 16kHz, mono",
                "output_format": "texto transcrito",
                "expected_size_mb": 150,
                "providers": ["QNNExecutionProvider", "CPUExecutionProvider"]
            },
            "sentiment": {
                "file": "distilbert_sentiment.onnx",
                "description": "Modelo DistilBERT para análise de sentimento",
                "input_format": "texto tokenizado",
                "output_format": "score de sentimento (-1 a 1)",
                "expected_size_mb": 260,
                "providers": ["QNNExecutionProvider", "CPUExecutionProvider"]
            },
            "objection": {
                "file": "bert_objection.onnx",
                "description": "Modelo BERT para detecção de objeções",
                "input_format": "texto tokenizado",
                "output_format": "categoria de objeção + confiança",
                "expected_size_mb": 420,
                "providers": ["QNNExecutionProvider", "CPUExecutionProvider"]
            },
            "speaker": {
                "file": "ecapa_speaker.onnx",
                "description": "Modelo ECAPA para identificação de falantes",
                "input_format": "audio PCM 16-bit, 16kHz, mono",
                "output_format": "embedding de speaker + confiança",
                "expected_size_mb": 90,
                "providers": ["QNNExecutionProvider", "CPUExecutionProvider"]
            },
            "llm": {
                "file": "anythingllm_local.onnx",
                "description": "Modelo LLM local para geração de texto",
                "input_format": "prompt tokenizado",
                "output_format": "texto gerado",
                "expected_size_mb": 2000,
                "providers": ["QNNExecutionProvider", "CPUExecutionProvider"]
            }
        },
        "integration_notes": {
            "setup": [
                "1. Colocar modelos ONNX na pasta models/",
                "2. Verificar se os nomes dos arquivos correspondem ao config",
                "3. Executar src/main_frontend.py",
                "4. Verificar logs para confirmação de carregamento"
            ],
            "testing": [
                "1. Iniciar gravação na aplicação",
                "2. Falar algumas frases",
                "3. Verificar se transcrição aparece",
                "4. Verificar se sentimento é detectado",
                "5. Verificar se objeções são identificadas"
            ],
            "troubleshooting": [
                "Se modelos não carregarem:",
                "- Verificar se arquivos existem na pasta models/",
                "- Verificar se ONNX Runtime está instalado",
                "- Verificar logs para erros específicos",
                "- Verificar se providers estão disponíveis"
            ]
        }
    }
    
    # Salvar configuração
    with open(models_dir / "models_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Arquivo de configuração criado")
    
    # Criar README
    readme_content = """# Modelos ONNX - PitchAI

## 📁 Estrutura de Diretórios

```
models/
├── whisper_base.onnx          # Transcrição de áudio
├── distilbert_sentiment.onnx  # Análise de sentimento
├── bert_objection.onnx        # Detecção de objeções
├── ecapa_speaker.onnx         # Identificação de falantes
├── anythingllm_local.onnx     # LLM local
└── models_config.json         # Configuração dos modelos
```

## 🚀 Como Integrar

### 1. Preparação
- Coloque os modelos ONNX na pasta `models/`
- Verifique se os nomes dos arquivos correspondem ao config
- Certifique-se de que o ONNX Runtime está instalado

### 2. Execução
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar aplicação
python src/main_frontend.py
```

### 3. Verificação
- Verifique os logs para confirmação de carregamento
- Teste a funcionalidade de gravação
- Confirme se os modelos estão funcionando

## 🔧 Configuração

Os modelos são configurados automaticamente no `NPUManager`. 
Para ajustar parâmetros, edite `src/ai/npu_manager.py`.

### Parâmetros Ajustáveis:
- `audio_buffer_size`: Tamanho do buffer de áudio (ms)
- `sentiment_window`: Janela de análise de sentimento (s)
- `objection_threshold`: Threshold para detecção de objeções
- `sentiment_sensitivity`: Sensibilidade do sentimento

## 📊 Status dos Modelos

A aplicação mostrará o status de cada modelo:
- ✅ Carregado: Modelo funcionando
- ⚠️ Simulação: Modelo não encontrado, usando simulação
- ❌ Erro: Problema no carregamento

## 🐛 Troubleshooting

### Modelos não carregam:
1. Verificar se arquivos existem na pasta `models/`
2. Verificar se ONNX Runtime está instalado
3. Verificar logs para erros específicos
4. Verificar se providers estão disponíveis

### Performance lenta:
1. Verificar se NPU está sendo usada
2. Ajustar tamanhos de buffer
3. Verificar uso de CPU/GPU

### Erros de inferência:
1. Verificar formato de entrada dos modelos
2. Verificar compatibilidade de versões
3. Verificar logs de erro específicos

## 📝 Notas Técnicas

- **Formato de Áudio**: PCM 16-bit, 16kHz, mono
- **Formato de Texto**: UTF-8
- **Providers**: QNN (NPU) > CoreML > CPU
- **Cache**: Resultados são cacheados por 5 segundos
- **Threading**: Processamento assíncrono para não bloquear UI

## 🔄 Atualizações

Para atualizar modelos:
1. Substituir arquivos ONNX na pasta `models/`
2. Reiniciar aplicação
3. Verificar logs de carregamento
4. Testar funcionalidade

## 📞 Suporte

Em caso de problemas:
1. Verificar logs da aplicação
2. Consultar documentação ONNX Runtime
3. Verificar compatibilidade de hardware
"""
    
    with open(models_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README criado")
    
    # Criar arquivos placeholder
    placeholders = [
        "whisper_base.onnx",
        "distilbert_sentiment.onnx", 
        "bert_objection.onnx",
        "ecapa_speaker.onnx",
        "anythingllm_local.onnx"
    ]
    
    for placeholder in placeholders:
        placeholder_path = models_dir / placeholder
        if not placeholder_path.exists():
            with open(placeholder_path, "w") as f:
                f.write(f"# Placeholder para {placeholder}\n")
                f.write("# Substitua este arquivo pelo modelo ONNX real\n")
            print(f"📄 Placeholder criado: {placeholder}")
    
    print("\n🎯 Estrutura de modelos preparada!")
    print("📋 Próximos passos:")
    print("1. Substituir placeholders pelos modelos ONNX reais")
    print("2. Executar src/main_frontend.py")
    print("3. Verificar logs de carregamento")
    print("4. Testar funcionalidade")


if __name__ == "__main__":
    create_models_structure()

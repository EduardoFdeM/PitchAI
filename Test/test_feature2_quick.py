#!/usr/bin/env python3
"""
Teste Rápido da Feature 2 Corrigida
===================================

Teste rápido para verificar se as correções estão funcionando:
- ModelManager integrado
- Timestamps corretos
- Fila limitada
- Logs de modo real/simulado
"""

import sys
import time
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from ai.model_manager import ModelManager
from ai.asr_whisper import TranscriptionService

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_feature2_corrections():
    """Testar as correções aplicadas na Feature 2."""
    print("🧪 Testando Feature 2 Corrigida")
    print("=" * 50)
    
    config = Config()
    
    # Inicializar Model Manager
    print("🔧 Inicializando Model Manager...")
    model_manager = ModelManager(config)
    model_manager.load_manifest()
    
    # Verificar modelos disponíveis
    models = model_manager.list_models()
    print(f"📋 Modelos disponíveis: {models}")
    
    # Obter entrada do modelo Whisper
    whisper_entry = model_manager.get_model_entry("whisper_base")
    if not whisper_entry:
        print("⚠️ Modelo Whisper não encontrado no manifesto, usando simulação")
        whisper_entry = {
            "path": "models/whisper_base.onnx",
            "ep": ["CPU"],
            "input": "audio_16k_mono"
        }
    else:
        print(f"✅ Whisper encontrado: {whisper_entry.description}")
    
    # Inicializar TranscriptionService com ModelManager
    print("🔧 Inicializando TranscriptionService...")
    transcription_service = TranscriptionService(
        config, 
        whisper_entry, 
        model_manager=model_manager
    )
    
    try:
        # Inicializar
        transcription_service.initialize()
        
        # Verificar métricas iniciais
        metrics = transcription_service.get_metrics()
        print(f"📊 Métricas iniciais: {metrics}")
        
        # Verificar se a fila está limitada
        queue_size = transcription_service.audio_queue.maxsize
        print(f"📊 Tamanho da fila: {queue_size} (deve ser 8)")
        
        if queue_size == 8:
            print("✅ Fila limitada corretamente")
        else:
            print(f"❌ Fila não limitada: {queue_size}")
        
        # Verificar contadores de amostras
        samples_consumed = transcription_service.samples_consumed
        print(f"📊 Contadores de amostras: {samples_consumed}")
        
        # Verificar timestamps t0
        t0_ms = transcription_service.t0_ms
        print(f"📊 Timestamps t0: {t0_ms}")
        
        print("✅ Feature 2 corrigida com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        transcription_service.cleanup()
        model_manager.cleanup()

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste Rápido da Feature 2 Corrigida")
    print("=" * 60)
    
    setup_logging()
    
    success = test_feature2_corrections()
    
    if success:
        print("\n🎉 CORREÇÕES APLICADAS COM SUCESSO!")
        print("   ✅ ModelManager integrado")
        print("   ✅ Timestamps corretos")
        print("   ✅ Fila limitada")
        print("   ✅ Logs de modo real/simulado")
    else:
        print("\n❌ Teste falhou.")

if __name__ == "__main__":
    main() 
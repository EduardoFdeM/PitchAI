#!/usr/bin/env python3
"""
Teste Simples de Captura de Áudio - PitchAI
===========================================

Teste básico para verificar se a captura de áudio está funcionando.
"""

import sys
import time
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from audio.capture import AudioCapture

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_simple_capture():
    """Teste simples de captura."""
    print("🎤 Teste simples de captura de áudio...")
    
    try:
        config = Config()
        audio_capture = AudioCapture(config)
        
        # Inicializar
        audio_capture.initialize()
        
        # Contador de chunks
        chunk_count = 0
        
        def on_audio_chunk(chunk):
            nonlocal chunk_count
            chunk_count += 1
            print(f"📊 Chunk {chunk_count}: {chunk.source} - {len(chunk.buffer)} samples")
        
        # Adicionar callback
        audio_capture.add_callback(on_audio_chunk)
        
        # Iniciar captura
        print("🎤 Iniciando captura...")
        audio_capture.start()
        
        # Aguardar
        print("⏳ Capturando por 5 segundos...")
        time.sleep(5)
        
        # Parar
        print("⏹️ Parando captura...")
        audio_capture.stop()
        
        # Métricas
        metrics = audio_capture.get_metrics()
        print(f"📊 Métricas: {metrics}")
        
        print("✅ Teste concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            audio_capture.cleanup()
        except:
            pass

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste Simples de Áudio")
    print("=" * 40)
    
    setup_logging()
    
    success = test_simple_capture()
    
    if success:
        print("\n🎉 Teste bem-sucedido!")
    else:
        print("\n❌ Teste falhou.")

if __name__ == "__main__":
    main() 
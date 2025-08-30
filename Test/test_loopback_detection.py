#!/usr/bin/env python3
"""
Teste de Detecção de Loopback WASAPI - PitchAI
==============================================

Teste para verificar se conseguimos detectar e configurar
dispositivos de loopback WASAPI no Windows.
"""

import sys
import time
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_loopback_detection():
    """Testar detecção de dispositivos de loopback."""
    print("🔍 Testando detecção de dispositivos de loopback...")
    
    try:
        import pyaudiowpatch as pyaudio
        
        pa = pyaudio.PyAudio()
        
        # 1. Loopback padrão
        print("\n1️⃣ Loopback padrão:")
        try:
            default_lb = pa.get_default_wasapi_loopback()
            print(f"   ✅ Default loopback: {default_lb['index']} - {default_lb['name']}")
            print(f"      Canais: {default_lb['maxInputChannels']}")
            print(f"      Sample Rate: {int(default_lb['defaultSampleRate'])} Hz")
        except Exception as e:
            print(f"   ❌ Erro ao obter loopback padrão: {e}")
        
        # 2. Todos os loopbacks disponíveis
        print("\n2️⃣ Todos os loopbacks disponíveis:")
        try:
            loopbacks = list(pa.get_loopback_device_info_generator())
            if loopbacks:
                for info in loopbacks:
                    print(f"   📻 {info['index']} - {info['name']}")
                    print(f"      Canais: {info['maxInputChannels']}, Rate: {int(info['defaultSampleRate'])} Hz")
            else:
                print("   ⚠️ Nenhum loopback encontrado")
        except Exception as e:
            print(f"   ❌ Erro ao listar loopbacks: {e}")
        
        # 3. Dispositivos de entrada (microfone)
        print("\n3️⃣ Dispositivos de entrada (microfone):")
        try:
            for i in range(pa.get_device_count()):
                device_info = pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    print(f"   🎤 {i} - {device_info['name']}")
                    print(f"      Canais: {device_info['maxInputChannels']}, Rate: {int(device_info['defaultSampleRate'])} Hz")
        except Exception as e:
            print(f"   ❌ Erro ao listar dispositivos de entrada: {e}")
        
        pa.terminate()
        return True
        
    except ImportError as e:
        print(f"❌ PyAudioWPatch não disponível: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def test_audio_capture():
    """Testar captura de áudio básica."""
    print("\n🎤 Testando captura de áudio básica...")
    
    try:
        import pyaudiowpatch as pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        
        # Configurações
        RATE = 16000  # 16kHz como especificado na Feature 1
        CHUNK = 1024  # ~64ms de buffer
        CHANNELS = 1  # Mono como especificado
        
        print(f"   Configuração: {RATE}Hz, {CHANNELS} canal, chunk={CHUNK}")
        
        # Tentar abrir stream de loopback
        try:
            default_lb = pa.get_default_wasapi_loopback()
            
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=default_lb["index"],
                frames_per_buffer=CHUNK
            )
            
            print("   ✅ Stream de loopback aberto com sucesso!")
            
            # Capturar alguns chunks para teste
            print("   🎵 Capturando 5 chunks de áudio...")
            for i in range(5):
                data = stream.read(CHUNK, exception_on_overflow=False)
                np_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np_data.astype(np.float32)**2))
                print(f"      Chunk {i+1}: RMS = {rms:.2f}")
                time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            print("   ✅ Captura de loopback testada com sucesso!")
            
        except Exception as e:
            print(f"   ❌ Erro na captura de loopback: {e}")
        
        pa.terminate()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de captura: {e}")
        return False

def main():
    """Função principal de teste."""
    print("🚀 PitchAI - Teste de Detecção de Loopback WASAPI")
    print("=" * 50)
    
    setup_logging()
    
    # Teste 1: Detecção de dispositivos
    detection_ok = test_loopback_detection()
    
    # Teste 2: Captura de áudio
    capture_ok = test_audio_capture()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    print(f"Detecção de Loopback: {'✅' if detection_ok else '❌'}")
    print(f"Captura de Áudio: {'✅' if capture_ok else '❌'}")
    
    if detection_ok and capture_ok:
        print("\n🎉 WASAPI LOOPBACK FUNCIONANDO! Podemos implementar a Feature 1!")
    else:
        print("\n⚠️ Alguns testes falharam. Verificar configuração.")

if __name__ == "__main__":
    main() 
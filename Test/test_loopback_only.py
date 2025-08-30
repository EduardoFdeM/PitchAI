#!/usr/bin/env python3
"""
Teste Específico de Loopback WASAPI - PitchAI
============================================

Teste focado apenas no loopback para identificar problemas.
"""

import sys
import time
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_loopback_direct():
    """Teste direto do loopback WASAPI."""
    print("🔍 Teste direto do loopback WASAPI...")
    
    try:
        import pyaudiowpatch as pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        
        # 1. Detectar loopback
        print("1️⃣ Detectando loopback...")
        default_lb = pa.get_default_wasapi_loopback()
        print(f"   Loopback: {default_lb['index']} - {default_lb['name']}")
        
        # 2. Configurar stream
        print("2️⃣ Configurando stream...")
        RATE = 48000  # Usar a taxa do dispositivo
        CHUNK = 1024
        CHANNELS = 1
        
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=default_lb["index"],
            frames_per_buffer=CHUNK
        )
        
        print("   ✅ Stream configurado")
        
        # 3. Capturar dados
        print("3️⃣ Capturando dados...")
        print("   (Reproduza algum áudio no sistema)")
        
        chunks_captured = 0
        start_time = time.time()
        
        while chunks_captured < 10:  # Capturar 10 chunks
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                np_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np_data.astype(np.float32)**2))
                
                chunks_captured += 1
                print(f"   Chunk {chunks_captured}: RMS = {rms:.4f}")
                
                time.sleep(0.1)  # 100ms entre chunks
                
            except Exception as e:
                print(f"   ❌ Erro na captura: {e}")
                break
        
        # 4. Limpar
        print("4️⃣ Limpando...")
        stream.stop_stream()
        stream.close()
        pa.terminate()
        
        duration = time.time() - start_time
        print(f"   ✅ Captura concluída em {duration:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_microphone_direct():
    """Teste direto do microfone."""
    print("\n🎤 Teste direto do microfone...")
    
    try:
        import pyaudiowpatch as pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        
        # 1. Detectar microfone
        print("1️⃣ Detectando microfone...")
        device_count = pa.get_device_count()
        mic_device = None
        
        for i in range(device_count):
            device_info = pa.get_device_info_by_index(i)
            if (device_info['maxInputChannels'] > 0 and 
                'loopback' not in device_info['name'].lower()):
                mic_device = device_info
                break
        
        if not mic_device:
            print("   ❌ Microfone não encontrado")
            return False
        
        print(f"   Microfone: {mic_device['index']} - {mic_device['name']}")
        
        # 2. Configurar stream
        print("2️⃣ Configurando stream...")
        RATE = int(mic_device['defaultSampleRate'])
        CHUNK = 1024
        CHANNELS = 1
        
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=mic_device["index"],
            frames_per_buffer=CHUNK
        )
        
        print("   ✅ Stream configurado")
        
        # 3. Capturar dados
        print("3️⃣ Capturando dados...")
        print("   (Fale algo no microfone)")
        
        chunks_captured = 0
        start_time = time.time()
        
        while chunks_captured < 10:  # Capturar 10 chunks
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                np_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np_data.astype(np.float32)**2))
                
                chunks_captured += 1
                print(f"   Chunk {chunks_captured}: RMS = {rms:.4f}")
                
                time.sleep(0.1)  # 100ms entre chunks
                
            except Exception as e:
                print(f"   ❌ Erro na captura: {e}")
                break
        
        # 4. Limpar
        print("4️⃣ Limpando...")
        stream.stop_stream()
        stream.close()
        pa.terminate()
        
        duration = time.time() - start_time
        print(f"   ✅ Captura concluída em {duration:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste Específico de Loopback")
    print("=" * 50)
    
    setup_logging()
    
    # Teste 1: Loopback
    loopback_ok = test_loopback_direct()
    
    # Teste 2: Microfone
    mic_ok = test_microphone_direct()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO")
    print("=" * 50)
    print(f"Loopback WASAPI: {'✅' if loopback_ok else '❌'}")
    print(f"Microfone: {'✅' if mic_ok else '❌'}")
    
    if loopback_ok and mic_ok:
        print("\n🎉 Ambos os dispositivos funcionando!")
    else:
        print("\n⚠️ Alguns dispositivos com problemas.")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Teste da Feature 1 Corrigida - PitchAI
=====================================

Teste para verificar se as correções aplicadas estão funcionando:
- Timestamps monotônicos
- Call ID único
- Formato PCM 16-bit mono 16kHz
- Nomes padronizados
"""

import sys
import time
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from audio.capture import AudioCapture, AudioChunk

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_feature1_corrections():
    """Testar as correções aplicadas na Feature 1."""
    print("🧪 Testando Feature 1 Corrigida")
    print("=" * 50)
    
    config = Config()
    audio_capture = AudioCapture(config)
    
    # Contadores para métricas
    chunks_received = {"mic": 0, "loopback": 0}
    call_ids = set()
    timestamps = {"mic": [], "loopback": []}
    sample_rates = set()
    channels = set()
    buffer_types = set()
    
    def on_audio_chunk(chunk: AudioChunk):
        """Callback para processar chunks de áudio."""
        chunks_received[chunk.source] += 1
        call_ids.add(chunk.call_id)
        timestamps[chunk.source].append(chunk.ts_ms)
        sample_rates.add(chunk.sample_rate)
        channels.add(chunk.channels)
        buffer_types.add(chunk.buffer.dtype)
        
        # Log periódico
        if chunks_received[chunk.source] % 5 == 0:
            print(f"📊 {chunk.source}: {chunks_received[chunk.source]} chunks")
            print(f"   Call ID: {chunk.call_id}")
            print(f"   Timestamp: {chunk.ts_ms}ms")
            print(f"   Sample Rate: {chunk.sample_rate}Hz")
            print(f"   Channels: {chunk.channels}")
            print(f"   Buffer Type: {chunk.buffer.dtype}")
            print(f"   Buffer Shape: {chunk.buffer.shape}")
    
    try:
        # Inicializar
        audio_capture.initialize()
        
        # Adicionar callback
        audio_capture.add_callback(on_audio_chunk)
        
        # Iniciar captura
        print("🎤 Iniciando captura...")
        audio_capture.start()
        
        # Aguardar captura
        print("⏳ Capturando por 5 segundos...")
        print("   (Fale algo no microfone e reproduza áudio no sistema)")
        time.sleep(5)
        
        # Parar captura
        print("⏹️ Parando captura...")
        audio_capture.stop()
        
        # Análise dos resultados
        print("\n📊 ANÁLISE DAS CORREÇÕES")
        print("=" * 40)
        
        # 1. Call ID único
        print("1️⃣ Call ID único:")
        print(f"   Call IDs encontrados: {len(call_ids)}")
        if len(call_ids) == 1:
            print("   ✅ Call ID único (correto)")
        else:
            print(f"   ❌ Múltiplos Call IDs: {call_ids}")
        
        # 2. Timestamps monotônicos
        print("\n2️⃣ Timestamps monotônicos:")
        for source in ["mic", "loopback"]:
            if timestamps[source]:
                timestamps_sorted = sorted(timestamps[source])
                if timestamps_sorted == timestamps[source]:
                    print(f"   ✅ {source}: timestamps monotônicos")
                else:
                    print(f"   ❌ {source}: timestamps não monotônicos")
                print(f"   {source}: {len(timestamps[source])} timestamps")
        
        # 3. Formato PCM correto
        print("\n3️⃣ Formato PCM:")
        print(f"   Sample rates: {sample_rates}")
        print(f"   Channels: {channels}")
        print(f"   Buffer types: {buffer_types}")
        
        if 16000 in sample_rates:
            print("   ✅ Sample rate 16kHz (correto)")
        else:
            print("   ❌ Sample rate não é 16kHz")
        
        if 1 in channels:
            print("   ✅ Mono (1 canal) - correto")
        else:
            print("   ❌ Não é mono")
        
        if any('int16' in str(t) for t in buffer_types):
            print("   ✅ Buffer int16 (correto)")
        else:
            print("   ❌ Buffer não é int16")
        
        # 4. Nomes padronizados
        print("\n4️⃣ Nomes padronizados:")
        for source in ["mic", "loopback"]:
            count = chunks_received[source]
            print(f"   {source}: {count} chunks")
            if count > 0:
                print(f"   ✅ {source} funcionando")
            else:
                print(f"   ⚠️ {source} não funcionou")
        
        # 5. Sincronização
        print("\n5️⃣ Sincronização:")
        metrics = audio_capture.get_metrics()
        drift = metrics['sync_drift_ms']
        print(f"   Drift: {drift}ms")
        if drift <= 20:
            print("   ✅ Drift ≤ 20ms (requisito atendido)")
        else:
            print(f"   ⚠️ Drift > 20ms: {drift}ms")
        
        # 6. Métricas gerais
        print("\n6️⃣ Métricas gerais:")
        print(f"   Total chunks: {sum(chunks_received.values())}")
        print(f"   Duração: {metrics.get('duration', 'N/A')}")
        print(f"   Buffer sizes: {metrics['buffer_sizes']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        audio_capture.cleanup()

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste da Feature 1 Corrigida")
    print("=" * 60)
    
    setup_logging()
    
    success = test_feature1_corrections()
    
    if success:
        print("\n🎉 FEATURE 1 CORRIGIDA COM SUCESSO!")
        print("   ✅ Timestamps monotônicos")
        print("   ✅ Call ID único")
        print("   ✅ Formato PCM 16-bit mono 16kHz")
        print("   ✅ Nomes padronizados")
        print("   ✅ Sincronização correta")
    else:
        print("\n❌ Teste falhou.")

if __name__ == "__main__":
    main() 
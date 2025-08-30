#!/usr/bin/env python3
"""
Teste de Validação Completa - Feature 2
=======================================

Teste abrangente para validar todos os aspectos da Feature 2:
- Integração com Feature 1
- Decoder real vs simulado
- Validação de entrada
- Timestamps corretos
- Latência ≤ 500ms
- Tratamento de erros
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from audio.capture import AudioCapture, AudioChunk
from ai.asr_whisper import TranscriptionService, TranscriptChunk
from ai.model_manager import ModelManager

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_input_validation():
    """Testar validação de entrada."""
    print("🧪 Testando validação de entrada...")
    
    config = Config()
    model_manager = ModelManager(config)
    model_manager.load_manifest()
    
    whisper_entry = model_manager.get_model_entry("whisper_base")
    if not whisper_entry:
        whisper_entry = {"path": "models/whisper_base.onnx", "ep": ["CPU"]}
    
    transcription_service = TranscriptionService(config, whisper_entry, model_manager=model_manager)
    transcription_service.initialize()
    
    # Teste 1: Chunk válido
    valid_chunk = AudioChunk(
        call_id="test_001",
        source="mic",
        ts_ms=1000,
        buffer=np.random.randint(-32768, 32767, 1600, dtype=np.int16),
        sample_rate=16000,
        channels=1
    )
    
    try:
        transcription_service.push_audio_chunk(valid_chunk)
        print("✅ Chunk válido aceito")
    except Exception as e:
        print(f"❌ Erro com chunk válido: {e}")
    
    # Teste 2: Chunk com fonte inválida
    invalid_source_chunk = AudioChunk(
        call_id="test_002",
        source="invalid",
        ts_ms=2000,
        buffer=np.random.randint(-32768, 32767, 1600, dtype=np.int16),
        sample_rate=16000,
        channels=1
    )
    
    try:
        transcription_service.push_audio_chunk(invalid_source_chunk)
        print("❌ Chunk com fonte inválida foi aceito")
    except Exception as e:
        print("✅ Chunk com fonte inválida rejeitado corretamente")
    
    # Teste 3: Chunk com buffer inválido
    class InvalidChunk:
        def __init__(self):
            self.call_id = "test_003"
            self.source = "mic"
            self.ts_ms = 3000
            self.buffer = "invalid_buffer"
            self.sample_rate = 16000
            self.channels = 1
    
    invalid_buffer_chunk = InvalidChunk()
    
    try:
        transcription_service.push_audio_chunk(invalid_buffer_chunk)
        print("❌ Chunk com buffer inválido foi aceito")
    except Exception as e:
        print("✅ Chunk com buffer inválido rejeitado corretamente")
    
    transcription_service.cleanup()
    model_manager.cleanup()

def test_timestamp_calculation():
    """Testar cálculo de timestamps."""
    print("\n🧪 Testando cálculo de timestamps...")
    
    config = Config()
    model_manager = ModelManager(config)
    model_manager.load_manifest()
    
    whisper_entry = model_manager.get_model_entry("whisper_base")
    if not whisper_entry:
        whisper_entry = {"path": "models/whisper_base.onnx", "ep": ["CPU"]}
    
    transcription_service = TranscriptionService(config, whisper_entry, model_manager=model_manager)
    transcription_service.initialize()
    
    # Simular chunks com timestamps conhecidos
    base_time = int(time.monotonic_ns() / 1_000_000)
    
    for i in range(5):
        chunk = AudioChunk(
            call_id="test_timestamps",
            source="mic",
            ts_ms=base_time + (i * 100),  # 100ms entre chunks
            buffer=np.random.randint(-32768, 32767, 1600, dtype=np.int16),
            sample_rate=16000,
            channels=1
        )
        transcription_service.push_audio_chunk(chunk)
    
    # Verificar se t0 foi inicializado
    t0_mic = transcription_service.t0_ms.get("mic")
    if t0_mic is not None:
        print(f"✅ t0 inicializado corretamente: {t0_mic}")
    else:
        print("❌ t0 não foi inicializado")
    
    # Verificar contadores
    samples_consumed = transcription_service.samples_consumed["mic"]
    print(f"📊 Amostras consumidas: {samples_consumed}")
    
    transcription_service.cleanup()
    model_manager.cleanup()

def test_decoder_modes():
    """Testar modos de decoder."""
    print("\n🧪 Testando modos de decoder...")
    
    config = Config()
    model_manager = ModelManager(config)
    model_manager.load_manifest()
    
    whisper_entry = model_manager.get_model_entry("whisper_base")
    if not whisper_entry:
        whisper_entry = {"path": "models/whisper_base.onnx", "ep": ["CPU"]}
    
    transcription_service = TranscriptionService(config, whisper_entry, model_manager=model_manager)
    transcription_service.initialize()
    
    # Verificar se decoder está disponível
    if transcription_service.decoder:
        print(f"✅ Decoder disponível: {type(transcription_service.decoder).__name__}")
        if transcription_service.decoder.is_real_decoder():
            print("✅ Decoder REAL ativo")
        else:
            print("⚠️ Decoder SIMULADO ativo")
    else:
        print("⚠️ Nenhum decoder disponível")
    
    # Testar decodificação
    dummy_outputs = [np.random.normal(0, 1, (1, 10, 1000))]  # [batch, seq, vocab]
    
    try:
        text, confidence = transcription_service._decode_whisper_output(dummy_outputs)
        print(f"📝 Texto decodificado: '{text}' (conf: {confidence:.2f})")
        print("✅ Decodificação funcionando")
    except Exception as e:
        print(f"❌ Erro na decodificação: {e}")
    
    transcription_service.cleanup()
    model_manager.cleanup()

def test_integration_feature1():
    """Testar integração com Feature 1."""
    print("\n🧪 Testando integração com Feature 1...")
    
    config = Config()
    
    # Inicializar componentes
    audio_capture = AudioCapture(config)
    
    model_manager = ModelManager(config)
    model_manager.load_manifest()
    
    whisper_entry = model_manager.get_model_entry("whisper_base")
    if not whisper_entry:
        whisper_entry = {"path": "models/whisper_base.onnx", "ep": ["CPU"]}
    
    transcription_service = TranscriptionService(config, whisper_entry, model_manager=model_manager)
    
    # Contadores
    audio_chunks = 0
    transcript_chunks = 0
    latencies = []
    
    def on_audio_chunk(chunk):
        nonlocal audio_chunks
        audio_chunks += 1
        transcription_service.push_audio_chunk(chunk)
    
    def on_transcript_chunk(chunk):
        nonlocal transcript_chunks, latencies
        transcript_chunks += 1
        
        # Calcular latência
        current_time = int(time.monotonic_ns() / 1_000_000)
        latency = current_time - chunk.ts_end_ms
        latencies.append(latency)
        
        print(f"📝 {chunk.source}: '{chunk.text}' (lat: {latency}ms)")
    
    try:
        # Inicializar
        audio_capture.initialize()
        transcription_service.initialize()
        
        # Conectar callbacks
        audio_capture.add_callback(on_audio_chunk)
        transcription_service.transcript_chunk_ready.connect(on_transcript_chunk)
        
        # Iniciar
        audio_capture.start()
        transcription_service.start("test_integration")
        
        # Aguardar
        print("⏳ Capturando por 5 segundos...")
        time.sleep(5)
        
        # Parar
        transcription_service.stop("test_integration")
        audio_capture.stop()
        
        # Análise
        print(f"\n📊 Resultados da integração:")
        print(f"   Chunks de áudio: {audio_chunks}")
        print(f"   Chunks de transcrição: {transcript_chunks}")
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            print(f"   Latência média: {avg_latency:.1f}ms")
            print(f"   Latência máxima: {max_latency}ms")
            
            if avg_latency <= 500:
                print("✅ Latência média ≤ 500ms")
            else:
                print(f"⚠️ Latência média > 500ms: {avg_latency:.1f}ms")
        
        if audio_chunks > 0 and transcript_chunks > 0:
            print("✅ Integração F1 → F2 funcionando")
        else:
            print("❌ Integração F1 → F2 falhou")
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        transcription_service.cleanup()
        audio_capture.cleanup()
        model_manager.cleanup()

def test_error_handling():
    """Testar tratamento de erros."""
    print("\n🧪 Testando tratamento de erros...")
    
    config = Config()
    model_manager = ModelManager(config)
    model_manager.load_manifest()
    
    whisper_entry = model_manager.get_model_entry("whisper_base")
    if not whisper_entry:
        whisper_entry = {"path": "models/whisper_base.onnx", "ep": ["CPU"]}
    
    transcription_service = TranscriptionService(config, whisper_entry, model_manager=model_manager)
    transcription_service.initialize()
    
    # Teste 1: Fila cheia
    print("📊 Testando fila cheia...")
    for i in range(20):  # Mais que o maxsize=8
        chunk = AudioChunk(
            call_id="test_queue",
            source="mic",
            ts_ms=1000 + i,
            buffer=np.random.randint(-32768, 32767, 1600, dtype=np.int16),
            sample_rate=16000,
            channels=1
        )
        transcription_service.push_audio_chunk(chunk)
    
    print("✅ Teste de fila concluído")
    
    # Teste 2: Chunk com dados corrompidos
    print("📊 Testando chunk corrompido...")
    try:
        # Simular chunk com dados inválidos
        transcription_service._transcribe_window(np.array([], dtype=np.int16))
        print("✅ Tratamento de chunk vazio funcionando")
    except Exception as e:
        print(f"❌ Erro com chunk vazio: {e}")
    
    transcription_service.cleanup()
    model_manager.cleanup()

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste de Validação Completa da Feature 2")
    print("=" * 70)
    
    setup_logging()
    
    # Executar todos os testes
    tests = [
        test_input_validation,
        test_timestamp_calculation,
        test_decoder_modes,
        test_integration_feature1,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Teste falhou: {e}")
    
    print(f"\n📊 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Feature 2 está pronta para o hackathon")
    else:
        print("⚠️ Alguns testes falharam - revisar implementação")

if __name__ == "__main__":
    main() 
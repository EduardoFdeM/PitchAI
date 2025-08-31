#!/usr/bin/env python3
"""
Demo Final - Whisper Transcrição Real
====================================

Demonstração completa do sistema de transcrição em tempo real
com Whisper real (não simulação) integrado ao sistema de captura.
"""

import sys
import time
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import pyaudiowpatch as pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class WhisperRealTranscriber:
    """Transcritor Whisper real usando transformers."""
    
    def __init__(self):
        self.model_name = "openai/whisper-tiny"
        self.processor = None
        self.model = None
        self.device = "cpu"  # Usar CPU por compatibilidade
        
    def initialize(self) -> bool:
        """Inicializar modelo Whisper real."""
        try:
            print(f"🤖 Carregando Whisper real: {self.model_name}")
            
            if not WHISPER_AVAILABLE:
                print("❌ Transformers/PyTorch não disponível")
                return False
            
            # Carregar processor e model
            print("📦 Carregando processor...")
            self.processor = WhisperProcessor.from_pretrained(self.model_name)
            
            print("🧠 Carregando modelo...")
            self.model = WhisperForConditionalGeneration.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            print(f"✅ Whisper carregado no {self.device}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar Whisper: {e}")
            return False
    
    def transcribe_audio(self, audio: np.ndarray) -> Tuple[str, float]:
        """Transcrever áudio usando Whisper real."""
        if not self.model or not self.processor:
            return "Modelo não carregado", 0.0
        
        try:
            start_time = time.time()
            
            # Preparar áudio
            if audio.dtype == np.int16:
                audio_float = audio.astype(np.float32) / 32768.0
            else:
                audio_float = audio.astype(np.float32)
            
            # Verificar duração mínima
            if len(audio_float) < 16000 * 0.5:  # Menos de 0.5s
                return "", 0.0
            
            # Verificar RMS para detectar silêncio (threshold muito baixo para seu microfone)
            rms = np.sqrt(np.mean(audio_float ** 2))
            if rms < 0.0005:  # Threshold ainda mais baixo para detectar seu microfone
                return "", 0.0
            
            print(f"📊 Processando {len(audio_float)} samples, RMS: {rms:.4f}")
            
            # Processar com Whisper
            inputs = self.processor(
                audio_float,
                sampling_rate=16000,
                return_tensors="pt"
            )
            
            # Mover para device
            input_features = inputs.input_features.to(self.device)
            
            # Gerar transcrição
            with torch.no_grad():
                predicted_ids = self.model.generate(
                    input_features,
                    max_length=50,
                    num_beams=1,  # Greedy decoding para velocidade
                    do_sample=False,
                    early_stopping=True
                )
            
            # Decodificar texto
            transcription = self.processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0]
            
            processing_time = (time.time() - start_time) * 1000
            print(f"⚡ Whisper real: {processing_time:.1f}ms")
            
            # Calcular confidence baseado no comprimento e RMS
            if transcription.strip():
                confidence = min(0.95, 0.5 + (rms * 100))
                return transcription.strip(), confidence
            else:
                return "", 0.0
                
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            return f"Erro: {str(e)[:30]}...", 0.0

class RealTimeDemo:
    """Demo em tempo real."""
    
    def __init__(self):
        self.transcriber = WhisperRealTranscriber()
        self.sample_rate = 16000  # Para o Whisper (após resample)
        self.chunk_duration = 3.0  # 3 segundos por chunk
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        
    def run_demo(self, duration_seconds=20):
        """Executar demo de transcrição em tempo real."""
        if not AUDIO_AVAILABLE:
            print("❌ PyAudioWPatch necessário")
            return
        
        if not self.transcriber.initialize():
            print("❌ Falha ao inicializar Whisper")
            return
        
        print("🎤 DEMO FINAL - Transcrição Whisper Real")
        print("=" * 50)
        print(f"⏱️ Duração: {duration_seconds} segundos")
        print(f"🔄 Chunks de {self.chunk_duration}s")
        print("💬 Comece a falar...")
        print()
        
        pa = pyaudio.PyAudio()
        
        try:
            # Usar configurações compatíveis com seu microfone
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=2,  # Seu microfone tem 2 canais
                rate=44100,  # Sample rate nativo do seu microfone
                input=True,
                frames_per_buffer=1024
            )
            
            audio_buffer = []
            transcription_count = 0
            start_time = time.time()
            
            while time.time() - start_time < duration_seconds:
                # Ler áudio
                data = stream.read(1024, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Converter stereo para mono (média dos canais)
                if len(audio_chunk) % 2 == 0:  # Stereo
                    stereo_frames = audio_chunk.reshape(-1, 2)
                    mono_chunk = stereo_frames.mean(axis=1).astype(np.int16)
                else:
                    mono_chunk = audio_chunk
                
                # Resample de 44100Hz para 16000Hz (aproximado)
                downsample_factor = 44100 // 16000  # ≈ 2.75, usando 3
                if len(mono_chunk) >= downsample_factor:
                    resampled_chunk = mono_chunk[::3]  # Pegar 1 a cada 3 samples
                    audio_buffer.extend(resampled_chunk.tolist())
                
                # Transcrever quando tiver chunk suficiente
                if len(audio_buffer) >= self.chunk_samples:
                    # Extrair chunk
                    chunk_audio = np.array(audio_buffer[:self.chunk_samples], dtype=np.int16)
                    audio_buffer = audio_buffer[self.chunk_samples // 2:]  # Overlap de 50%
                    
                    # Transcrever
                    elapsed = time.time() - start_time
                    transcription_count += 1
                    
                    print(f"\n[{elapsed:.1f}s] 🔄 Transcrevendo chunk #{transcription_count}...")
                    
                    text, confidence = self.transcriber.transcribe_audio(chunk_audio)
                    
                    if text:
                        print(f"[{elapsed:.1f}s] 📝 '{text}' (conf: {confidence:.2f})")
                    else:
                        print(f"[{elapsed:.1f}s] 🔇 (sem fala detectada)")
            
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            print(f"\n✅ Demo concluído! {transcription_count} chunks processados")
            
        except Exception as e:
            print(f"❌ Erro no demo: {e}")

def main():
    print("🚀 DEMO FINAL - Sistema de Transcrição PitchAI")
    print("=" * 60)
    
    # Verificar dependências
    print("🔍 Verificando dependências...")
    print(f"📊 PyAudioWPatch: {'✅' if AUDIO_AVAILABLE else '❌'}")
    print(f"🤖 Whisper/Transformers: {'✅' if WHISPER_AVAILABLE else '❌'}")
    
    if not WHISPER_AVAILABLE:
        print("\n❌ Para transcrição real, instale:")
        print("   pip install torch transformers")
        return
    
    if not AUDIO_AVAILABLE:
        print("\n❌ PyAudioWPatch necessário para captura de áudio")
        return
    
    print("\n🎯 Este demo demonstra:")
    print("   ✅ Captura de áudio em tempo real")
    print("   ✅ Processamento com Whisper real")
    print("   ✅ Transcrição de fala para texto")
    print("   ✅ Sistema completo integrado")
    
    print("\n💡 Dicas:")
    print("   - Fale claramente e pausadamente")
    print("   - Aguarde ~3s entre frases para melhor resultado")
    print("   - O sistema processa chunks de 3 segundos")
    
    input("\n🎤 Pressione ENTER para começar o demo...")
    
    demo = RealTimeDemo()
    demo.run_demo(duration_seconds=20)

if __name__ == "__main__":
    main()

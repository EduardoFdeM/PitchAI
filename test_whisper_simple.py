#!/usr/bin/env python3
"""
Teste simples de transcrição ao vivo com Whisper
Usando implementação padrão do transformers (funciona com CPU)
"""

import torch
from transformers import pipeline
import pyaudio
import numpy as np
import time
import threading
import queue
import signal
import sys

class WhisperLiveSimple:
    def __init__(self, model_size="small"):
        print(f"🚀 Inicializando Whisper {model_size}...")

        # Configurar handler para Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Flag para controle de parada
        self.should_stop = False

        try:
            # Usar pipeline do transformers (mais simples e funciona com CPU)
            device = "cpu"  # Forçar CPU
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=f"openai/whisper-{model_size}",
                device=device,
                torch_dtype=torch.float32
            )

            print(f"✅ Whisper {model_size} carregado com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao carregar Whisper: {e}")
            raise

        # Configurações de áudio
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # Whisper usa 16kHz
        self.record_seconds = 2  # Gravar em blocos de 2 segundos

        # Fila para comunicação entre threads
        self.audio_queue = queue.Queue()

        # Controle de threads
        self.is_recording = False
        self.recording_thread = None
        self.processing_thread = None

    def _signal_handler(self, signum, frame):
        """Handler para Ctrl+C"""
        print("\n⏹️ Recebido sinal de parada (Ctrl+C)...")
        self.should_stop = True
        self.is_recording = False

    def start_recording(self):
        """Inicia a gravação de áudio"""
        if self.is_recording:
            print("⚠️ Já está gravando!")
            return
            
        self.is_recording = True
        self.should_stop = False
        
        self.recording_thread = threading.Thread(target=self._record_audio, daemon=True)
        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)

        self.recording_thread.start()
        self.processing_thread.start()

        print("🎤 Gravando... Fale algo! (Ctrl+C para parar)")
        print("💡 Dica: Fale em português para melhores resultados")

    def stop_recording(self):
        """Para a gravação"""
        print("🛑 Parando gravação...")
        self.is_recording = False
        self.should_stop = True
        
        # Aguardar threads terminarem com timeout
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)
            
        print("✅ Gravação parada")

    def _record_audio(self):
        """Thread para gravar áudio continuamente"""
        audio = pyaudio.PyAudio()

        try:
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            print("🎙️ Microfone aberto. Gravando...")

            while self.is_recording and not self.should_stop:
                try:
                    # Ler chunk de áudio
                    data = stream.read(self.chunk, exception_on_overflow=False)

                    # Converter para numpy array
                    audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Adicionar à fila
                    if not self.audio_queue.full():
                        self.audio_queue.put(audio_data)

                except Exception as e:
                    if not self.should_stop:
                        print(f"Erro na gravação: {e}")
                    break

        except Exception as e:
            print(f"Erro ao abrir microfone: {e}")
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            audio.terminate()
            print("🎙️ Microfone fechado")

    def _process_audio(self):
        """Thread para processar áudio e fazer transcrição"""
        audio_buffer = []

        while (self.is_recording or not self.audio_queue.empty()) and not self.should_stop:
            try:
                # Coletar áudio por alguns segundos
                start_time = time.time()
                while time.time() - start_time < self.record_seconds and self.is_recording and not self.should_stop:
                    try:
                        if not self.audio_queue.empty():
                            chunk = self.audio_queue.get(timeout=0.1)
                            audio_buffer.extend(chunk)
                        else:
                            time.sleep(0.01)
                    except queue.Empty:
                        break

                if len(audio_buffer) > 0 and not self.should_stop:
                    # Converter para numpy array
                    audio_array = np.array(audio_buffer, dtype=np.float32)

                    # Fazer transcrição
                    transcription = self._transcribe_audio(audio_array)

                    if transcription and transcription.strip():
                        print(f"🎯 TRANSCRIÇÃO: {transcription}")

                    # Limpar buffer para próximo segmento
                    audio_buffer = []

            except Exception as e:
                if not self.should_stop:
                    print(f"Erro no processamento: {e}")
                break

        print("🏁 Processamento finalizado")

    def _transcribe_audio(self, audio_array):
        """Transcreve áudio usando Whisper"""
        try:
            # Usar pipeline do transformers
            result = self.pipe(
                audio_array,
                generate_kwargs={
                    "language": "portuguese",  # Forçar português
                    "task": "transcribe"
                },
                return_timestamps=False
            )

            transcription = result["text"].strip()
            return transcription

        except Exception as e:
            print(f"Erro na transcrição: {e}")
            return ""

def main():
    print("🎤 TESTE WHISPER - TRANSCRIÇÃO AO VIVO")
    print("=" * 50)
    print("Usando modelo: Whisper Small (CPU)")
    print("Configuração: Português, tempo real")
    print("=" * 50)

    # Escolher tamanho do modelo
    model_size = "small"  # Opções: tiny, small, medium, large

    whisper = None
    
    try:
        # Inicializar Whisper
        whisper = WhisperLiveSimple(model_size)

        # Iniciar transcrição ao vivo
        whisper.start_recording()

        # Manter programa rodando
        while not whisper.should_stop:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n⏹️ Interrupção do teclado detectada...")
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Instale pyaudio: pip install pyaudio")
        print("2. Verifique se o microfone está funcionando")
        print("3. Tente usar um modelo menor: tiny ao invés de small")
    finally:
        # Parar gravação
        if whisper:
            whisper.stop_recording()
        print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main()

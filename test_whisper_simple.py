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

class WhisperLiveSimple:
    def __init__(self, model_size="small"):
        print(f"🚀 Inicializando Whisper {model_size}...")

        # Usar pipeline do transformers (mais simples e funciona com CPU)
        device = "cpu"  # Forçar CPU
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=f"openai/whisper-{model_size}",
            device=device,
            torch_dtype=torch.float32
        )

        print(f"✅ Whisper {model_size} carregado com sucesso!")

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

    def start_recording(self):
        """Inicia a gravação de áudio"""
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.processing_thread = threading.Thread(target=self._process_audio)

        self.recording_thread.start()
        self.processing_thread.start()

        print("🎤 Gravando... Fale algo! (Ctrl+C para parar)")
        print("💡 Dica: Fale em português para melhores resultados")

    def stop_recording(self):
        """Para a gravação"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        if self.processing_thread:
            self.processing_thread.join()

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

            while self.is_recording:
                try:
                    # Ler chunk de áudio
                    data = stream.read(self.chunk, exception_on_overflow=False)

                    # Converter para numpy array
                    audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Adicionar à fila
                    self.audio_queue.put(audio_data)

                except Exception as e:
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

    def _process_audio(self):
        """Thread para processar áudio e fazer transcrição"""
        audio_buffer = []

        while self.is_recording or not self.audio_queue.empty():
            try:
                # Coletar áudio por alguns segundos
                start_time = time.time()
                while time.time() - start_time < self.record_seconds and self.is_recording:
                    try:
                        if not self.audio_queue.empty():
                            chunk = self.audio_queue.get(timeout=0.1)
                            audio_buffer.extend(chunk)
                        else:
                            time.sleep(0.01)
                    except:
                        break

                if len(audio_buffer) > 0:
                    # Converter para numpy array
                    audio_array = np.array(audio_buffer, dtype=np.float32)

                    # Fazer transcrição
                    transcription = self._transcribe_audio(audio_array)

                    if transcription and transcription.strip():
                        print(f"🎯 TRANSCRIÇÃO: {transcription}")

                    # Limpar buffer para próximo segmento
                    audio_buffer = []

            except Exception as e:
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

    try:
        # Inicializar Whisper
        whisper = WhisperLiveSimple(model_size)

        # Iniciar transcrição ao vivo
        whisper.start_recording()

        # Manter programa rodando
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n⏹️ Finalizando...")

        # Parar gravação
        whisper.stop_recording()

        print("\n✅ Teste concluído!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Instale pyaudio: pip install pyaudio")
        print("2. Verifique se o microfone está funcionando")
        print("3. Tente usar um modelo menor: tiny ao invés de small")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Teste simples de transcrição ao vivo com Whisper Large ONNX
Imprime transcrição em tempo real no terminal
"""

import numpy as np
import torch
import onnxruntime as ort
from transformers import AutoTokenizer, AutoFeatureExtractor
import pyaudio
import wave
import time
import threading
import queue

class WhisperONNXLive:
    def __init__(self, model_path="models/whisper_large"):
        print("🚀 Inicializando Whisper Large ONNX...")

        # Carregar tokenizer e feature extractor
        self.tokenizer = AutoTokenizer.from_pretrained("openai/whisper-large-v3")
        self.feature_extractor = AutoFeatureExtractor.from_pretrained("openai/whisper-large-v3")

        # Configurar ONNX Runtime
        providers = ['CPUExecutionProvider']  # Usar CPU por enquanto
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Carregar encoder
        print("📥 Carregando encoder...")
        self.encoder_session = ort.InferenceSession(
            f"{model_path}/encoder_model.onnx",
            sess_options=session_options,
            providers=providers
        )

        # Carregar decoder
        print("📥 Carregando decoder...")
        self.decoder_session = ort.InferenceSession(
            f"{model_path}/decoder_model.onnx",
            sess_options=session_options,
            providers=providers
        )

        print("✅ Modelos carregados com sucesso!")
        print(f"Encoder inputs: {[inp.name for inp in self.encoder_session.get_inputs()]}")
        print(f"Decoder inputs: {[inp.name for inp in self.decoder_session.get_inputs()]}")

        # Configurações de áudio
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # Whisper usa 16kHz
        self.record_seconds = 3  # Gravar em blocos de 3 segundos

        # Fila para comunicação entre threads
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()

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

        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print("🎙️ Microfone aberto. Gravando...")

        try:
            while self.is_recording:
                # Ler chunk de áudio
                data = stream.read(self.chunk, exception_on_overflow=False)

                # Converter para numpy array
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                # Adicionar à fila
                self.audio_queue.put(audio_data)

        except KeyboardInterrupt:
            print("\n⏹️ Parando gravação...")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def _process_audio(self):
        """Thread para processar áudio e fazer transcrição"""
        audio_buffer = []

        while self.is_recording or not self.audio_queue.empty():
            try:
                # Coletar áudio por alguns segundos
                start_time = time.time()
                while time.time() - start_time < self.record_seconds and self.is_recording:
                    if not self.audio_queue.empty():
                        chunk = self.audio_queue.get(timeout=0.1)
                        audio_buffer.extend(chunk)
                    else:
                        time.sleep(0.01)

                if len(audio_buffer) > 0:
                    # Converter para numpy array
                    audio_array = np.array(audio_buffer, dtype=np.float32)

                    # Fazer transcrição
                    transcription = self._transcribe_audio(audio_array)

                    if transcription.strip():
                        print(f"🎯 TRANSCRIÇÃO: {transcription}")

                    # Limpar buffer
                    audio_buffer = []

            except Exception as e:
                print(f"Erro no processamento: {e}")
                break

        print("🏁 Processamento finalizado")

    def _transcribe_audio(self, audio_array):
        """Transcreve áudio usando modelos ONNX"""
        try:
            # 1. Pré-processar áudio
            inputs = self.feature_extractor(
                audio_array,
                sampling_rate=self.rate,
                return_tensors="np"
            )

            # 2. Extrair features com encoder
            encoder_inputs = {
                "input_features": inputs["input_features"]
            }

            encoder_outputs = self.encoder_session.run(None, encoder_inputs)
            encoder_hidden_states = encoder_outputs[0]

            # 3. Preparar decoder
            # Tokens iniciais: <|startoftranscript|> + <|pt|> (portuguese)
            decoder_start_token_id = self.tokenizer.convert_tokens_to_ids("<|startoftranscript|>")
            language_token_id = self.tokenizer.convert_tokens_to_ids("<|pt|>")

            decoder_input_ids = np.array([[decoder_start_token_id, language_token_id]], dtype=np.int64)

            # 4. Decodificar token por token
            generated_tokens = []
            max_length = 100  # Máximo de tokens para gerar

            for _ in range(max_length):
                decoder_inputs = {
                    "input_ids": decoder_input_ids,
                    "encoder_hidden_states": encoder_hidden_states
                }

                decoder_outputs = self.decoder_session.run(None, decoder_inputs)
                next_token_logits = decoder_outputs[0][:, -1, :]

                # Escolher token com maior probabilidade
                next_token_id = np.argmax(next_token_logits, axis=-1)[0]

                # Adicionar token gerado
                generated_tokens.append(next_token_id)
                decoder_input_ids = np.concatenate([decoder_input_ids, [[next_token_id]]], axis=1)

                # Parar se encontrou token de fim
                if next_token_id == self.tokenizer.eos_token_id:
                    break

            # 5. Decodificar tokens para texto
            transcription = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

            return transcription.strip()

        except Exception as e:
            print(f"Erro na transcrição: {e}")
            return ""

def main():
    print("🎤 TESTE WHISPER LARGE ONNX - TRANSCRIÇÃO AO VIVO")
    print("=" * 60)

    try:
        # Inicializar Whisper
        whisper = WhisperONNXLive()

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

    except Exception as e:
        print(f"❌ Erro: {e}")
        print("Verifique se os arquivos ONNX existem e estão no caminho correto")

if __name__ == "__main__":
    main()

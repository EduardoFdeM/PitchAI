"""
Whisper Transcription - Transcrição em Tempo Real (ONNX NPU)
============================================================

Módulo de transcrição em tempo real utilizando o pipeline do Whisper
com modelos Encoder e Decoder ONNX otimizados para a NPU.
"""

import logging
import numpy as np
import time
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QThread

# Usaremos o processador do transformers apenas para pré e pós-processamento
# A inferência será 100% via ONNX Runtime
try:
    from transformers import WhisperProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Biblioteca `transformers` não encontrada. A transcrição real não funcionará.")
    print("   Instale com: pip install transformers")

# Supondo que a classe ModelManager e AudioChunk estejam disponíveis
# from ..core.contracts import AudioChunk (Exemplo de import)
# from .model_manager import ModelManager (Exemplo de import)

class WhisperASR(QObject):
    """
    Serviço de ASR (Automatic Speech Recognition) com Whisper ONNX.
    Orquestra o pré-processamento, a execução do encoder-decoder e o pós-processamento.
    """
    transcription_ready = pyqtSignal(dict)  # Sinal emitido com o resultado da transcrição
    
    def __init__(self, model_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.model_manager = model_manager
        
        self.processor = None
        self.encoder_session = None
        self.decoder_session = None
        
        self.is_initialized = False

    def initialize(self):
        """Carrega os modelos e o processador."""
        if not TRANSFORMERS_AVAILABLE:
            self.logger.error("Biblioteca `transformers` é necessária para o WhisperASR.")
            return

        try:
            self.logger.info("Inicializando o processador do Whisper...")
            # Usaremos o 'openai/whisper-tiny' pois corresponde aos modelos que você tem
            self.processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
            
            self.logger.info("Carregando sessões ONNX do Whisper via ModelManager...")
            self.encoder_session = self.model_manager.get_session("whisper_tiny_encoder")
            self.decoder_session = self.model_manager.get_session("whisper_tiny_decoder")
            
            if not self.encoder_session or not self.decoder_session:
                raise RuntimeError("Falha ao carregar uma ou mais sessões ONNX do Whisper.")

            self.is_initialized = True
            self.logger.info("✅ WhisperASR inicializado com sucesso.")

        except Exception as e:
            self.logger.error(f"❌ Falha ao inicializar o WhisperASR: {e}")
            self.is_initialized = False
            
    def transcribe(self, audio_chunk: np.ndarray, source: str, call_id: str, ts_ms: int) -> Optional[dict]:
        """
        Executa a transcrição de um chunk de áudio.

        Args:
            audio_chunk (np.ndarray): Array numpy com o áudio PCM 16-bit @ 16kHz.
            source (str): Origem do áudio ('mic' ou 'loopback').
            call_id (str): ID da chamada.
            ts_ms (int): Timestamp do chunk.

        Returns:
            Optional[dict]: Um dicionário com a transcrição ou None se não houver fala.
        """
        if not self.is_initialized:
            self.logger.warning("WhisperASR não foi inicializado. Impossível transcrever.")
            return None

        start_time = time.perf_counter()
        
        try:
            # 1. Pré-processamento: Extrair features (log-mel spectrogram)
            # O áudio já deve estar em float32 no range [-1, 1]
            audio_float32 = audio_chunk.astype(np.float32) / 32768.0
            input_features = self.processor(
                audio_float32, 
                sampling_rate=16000, 
                return_tensors="np"
            ).input_features
            
            # 2. Executar Encoder
            encoder_outputs = self.encoder_session.run(None, {"input_features": input_features})
            encoder_hidden_states = encoder_outputs[0]

            # 3. Executar Decoder (Greedy Search)
            # Começamos com os tokens de início de transcrição
            decoder_input_ids = np.array([[self.processor.tokenizer.bos_token_id]], dtype=np.int64)
            
            # Gerar a sequência de tokens de forma auto-regressiva
            for _ in range(self.processor.tokenizer.model_max_length):
                decoder_outputs = self.decoder_session.run(
                    None,
                    {
                        "input_ids": decoder_input_ids,
                        "encoder_hidden_states": encoder_hidden_states,
                    },
                )
                
                # Obter o token com a maior probabilidade (greedy)
                next_token_logits = decoder_outputs[0][0, -1, :]
                next_token_id = np.argmax(next_token_logits)
                
                # Adicionar o novo token à sequência
                decoder_input_ids = np.append(decoder_input_ids, [[next_token_id]], axis=1).astype(np.int64)

                # Parar se o token de fim de sequência for gerado
                if next_token_id == self.processor.tokenizer.eos_token_id:
                    break

            # 4. Pós-processamento: Decodificar os tokens para texto
            transcribed_ids = decoder_input_ids[0]
            transcription = self.processor.tokenizer.decode(transcribed_ids, skip_special_tokens=True)
            
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000

            if transcription.strip():
                result = {
                    "call_id": call_id,
                    "source": source,
                    "ts_start_ms": ts_ms,
                    "ts_end_ms": ts_ms + int(len(audio_chunk) / 16), # Aproximado
                    "text": transcription.strip(),
                    "confidence": 0.95, # Placeholder, confiança real é mais complexa
                    "processing_time_ms": processing_time_ms
                }
                self.logger.info(f"Transcrição ({source}): '{result['text']}' (em {processing_time_ms:.0f} ms)")
                self.transcription_ready.emit(result)
                return result

        except Exception as e:
            self.logger.error(f"❌ Erro durante a transcrição: {e}", exc_info=True)
        
        return None 
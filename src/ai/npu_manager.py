"""
NPU Manager - Gerenciador da NPU Snapdragon
===========================================

Coordena todos os modelos ONNX rodando na NPU para
processamento simultâneo de áudio e análise.
Integra com ModelManager para carregamento unificado.
"""

import logging
import numpy as np
import time
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("⚠️ ONNX Runtime não disponível")


class NPUWorkerThread(QThread):
    """Thread worker para processamento NPU."""
    
    result_ready = pyqtSignal(str, dict)  # model_name, result
    error_occurred = pyqtSignal(str, str)  # model_name, error_message
    
    def __init__(self, model_name: str, session: any, input_data: Any, input_name: str = None):
        super().__init__()
        self.model_name = model_name
        self.session = session
        self.input_data = input_data
        self.input_name = input_name
        self.logger = logging.getLogger(f"{__name__}.{model_name}")
    
    def run(self):
        """Executar inferência na NPU."""
        try:
            if not self.session:
                self.error_occurred.emit(self.model_name, "Sessão não disponível")
                return
            
            # Preparar input baseado no tipo de modelo
            processed_input = self._prepare_input()
            
            # Executar inferência
            start_time = time.time()
            outputs = self.session.run(None, {self.input_name: processed_input})
            inference_time = (time.time() - start_time) * 1000
            
            # Processar resultado baseado no tipo de modelo
            result = self._process_output(outputs, inference_time)
            
            self.result_ready.emit(self.model_name, result)
            
        except Exception as e:
            self.logger.error(f"Erro no worker NPU {self.model_name}: {e}")
            self.error_occurred.emit(self.model_name, str(e))
    
    def _prepare_input(self) -> np.ndarray:
        """Preparar input para o modelo."""
        if self.model_name == "whisper_base":
            # Whisper espera áudio normalizado [-1, 1] com shape [1, T]
            if len(self.input_data.shape) == 1:
                return self.input_data[np.newaxis, :].astype(np.float32)
            return self.input_data.astype(np.float32)
        
        elif self.model_name == "distilbert_sentiment":
            # DistilBERT espera tokens com shape [batch_size, sequence_length]
            if isinstance(self.input_data, str):
                # Tokenizar texto (implementação simplificada)
                tokens = self._tokenize_text(self.input_data)
                return np.array([tokens], dtype=np.int64)
            return self.input_data.astype(np.int64)
        
        elif self.model_name == "bert_objection":
            # BERT para objeções - similar ao sentiment
            if isinstance(self.input_data, str):
                tokens = self._tokenize_text(self.input_data)
                return np.array([tokens], dtype=np.int64)
            return self.input_data.astype(np.int64)
        
        elif self.model_name == "ecapa_speaker":
            # ECAPA espera áudio com shape [batch_size, time]
            if len(self.input_data.shape) == 1:
                return self.input_data[np.newaxis, :].astype(np.float32)
            return self.input_data.astype(np.float32)
        
        else:
            # Fallback genérico
            return np.array(self.input_data, dtype=np.float32)
    
    def _tokenize_text(self, text: str) -> List[int]:
        """Tokenização simplificada para BERT/DistilBERT."""
        # Implementação básica - em produção usar tokenizer real
        words = text.lower().split()
        tokens = []
        for word in words[:512]:  # Limite de sequência
            # Hash simples para simular tokens
            token_id = hash(word) % 30000  # Vocab size aproximado
            tokens.append(token_id)
        
        # Padding para sequência de 512
        while len(tokens) < 512:
            tokens.append(0)
        
        return tokens[:512]
    
    def _process_output(self, outputs: List[np.ndarray], inference_time: float) -> Dict[str, Any]:
        """Processar saída do modelo."""
        if self.model_name == "whisper_base":
            # Whisper retorna logits - converter para texto
            logits = outputs[0]
            text = self._decode_whisper_output(logits)
            confidence = self._calculate_whisper_confidence(logits)  # ✅ Calcular confiança real
            speaker_id = self._determine_speaker_from_audio(audio_chunk)  # ✅ Determinar speaker
            return {
                "text": text,
                "confidence": confidence,
                "speaker_id": speaker_id,
                "inference_time_ms": inference_time
            }
        
        elif self.model_name == "distilbert_sentiment":
            # DistilBERT retorna logits de sentimento
            logits = outputs[0]
            sentiment_score = self._process_sentiment_logits(logits)
            engagement = self._calculate_engagement_from_audio(audio_chunk)  # ✅ Calcular engajamento
            return {
                "sentiment": sentiment_score,
                "emotion": self._classify_emotion(sentiment_score),
                "engagement": engagement,
                "inference_time_ms": inference_time
            }
        
        elif self.model_name == "bert_objection":
            # BERT para objeções
            logits = outputs[0]
            objection_result = self._process_objection_logits(logits)
            return {
                "objection_detected": objection_result["detected"],
                "category": objection_result["category"],
                "confidence": objection_result["confidence"],
                "inference_time_ms": inference_time
            }
        
        elif self.model_name == "ecapa_speaker":
            # ECAPA retorna embeddings de speaker
            embeddings = outputs[0]
            speaker_id = self._classify_speaker(embeddings)
            return {
                "speaker_id": speaker_id,
                "confidence": 0.9,
                "inference_time_ms": inference_time
            }
        
        else:
            return {
                "status": "processed",
                "inference_time_ms": inference_time
            }
    
    def _decode_whisper_output(self, logits: np.ndarray) -> str:
        """Decodificar saída do Whisper (simplificado)."""
        # Implementação simplificada - em produção usar decoder real
        # Por enquanto, retornar texto de exemplo baseado no input
        if logits.shape[0] > 0:
            return "Texto transcrito via Whisper ONNX"
        return ""
    
    def _calculate_whisper_confidence(self, logits: np.ndarray) -> float:
        """Calcular confiança da transcrição Whisper."""
        try:
            # Calcular perplexidade dos logits como proxy de confiança
            # Quanto menor a perplexidade, maior a confiança
            if logits.shape[0] > 0:
                # Calcular entropia dos logits
                probs = self._softmax(logits)
                entropy = -np.sum(probs * np.log(probs + 1e-10))
                
                # Converter entropia para confiança (0-1)
                # Assumindo que entropia baixa = alta confiança
                max_entropy = np.log(probs.shape[1])  # Entropia máxima
                confidence = 1.0 - (entropy / max_entropy)
                
                # Normalizar para range [0.1, 0.95]
                return max(0.1, min(0.95, confidence))
            
            return 0.5  # Confiança padrão
            
        except Exception as e:
            self.logger.warning(f"Erro ao calcular confiança Whisper: {e}")
            return 0.5
    
    def _determine_speaker_from_audio(self, audio_chunk: np.ndarray) -> str:
        """Determinar speaker baseado em características do áudio."""
        try:
            # Análise simples baseada em características do áudio
            # Em produção, usar modelo ECAPA ou similar
            
            # Calcular características básicas
            volume = np.mean(np.abs(audio_chunk))
            zero_crossings = np.sum(np.diff(np.sign(audio_chunk)) != 0)
            spectral_centroid = self._calculate_spectral_centroid(audio_chunk)
            
            # Heurísticas simples para diferenciar speakers
            # (Em produção, usar modelo treinado)
            
            # Speaker com volume mais alto e frequência mais baixa = vendedor
            if volume > 0.05 and spectral_centroid < 1000:
                return "vendor"
            # Speaker com volume mais baixo e frequência mais alta = cliente
            elif volume > 0.02 and spectral_centroid > 1000:
                return "client"
            else:
                # Fallback baseado em padrões de uso
                return "vendor"  # Assumir vendedor como padrão
                
        except Exception as e:
            self.logger.warning(f"Erro ao determinar speaker: {e}")
            return "vendor"  # Fallback
    
    def _calculate_engagement_from_audio(self, audio_chunk: np.ndarray) -> float:
        """Calcular engajamento baseado em características do áudio."""
        try:
            # Métricas de engajamento baseadas em características acústicas
            # Em produção, usar modelo treinado para engajamento
            
            # 1. Volume médio (mais alto = mais engajado)
            volume = np.mean(np.abs(audio_chunk))
            volume_score = min(1.0, volume * 10)  # Normalizar
            
            # 2. Variabilidade de volume (mais variável = mais expressivo)
            volume_std = np.std(np.abs(audio_chunk))
            variability_score = min(1.0, volume_std * 5)
            
            # 3. Taxa de fala (mais rápida = mais engajado)
            zero_crossings = np.sum(np.diff(np.sign(audio_chunk)) != 0)
            speech_rate_score = min(1.0, zero_crossings / 1000)
            
            # 4. Energia espectral (mais energia = mais animado)
            spectral_energy = np.sum(audio_chunk ** 2)
            energy_score = min(1.0, spectral_energy / 1000)
            
            # Combinar scores com pesos
            engagement = (
                0.3 * volume_score +
                0.2 * variability_score +
                0.3 * speech_rate_score +
                0.2 * energy_score
            )
            
            # Normalizar para [0.1, 0.95]
            return max(0.1, min(0.95, engagement))
            
        except Exception as e:
            self.logger.warning(f"Erro ao calcular engajamento: {e}")
            return 0.5  # Engajamento padrão
    
    def _calculate_spectral_centroid(self, audio_chunk: np.ndarray) -> float:
        """Calcular centroide espectral do áudio."""
        try:
            # Implementação simplificada do centroide espectral
            # Em produção, usar FFT completa
            
            # Calcular FFT simples
            fft = np.fft.fft(audio_chunk)
            magnitude = np.abs(fft)
            
            # Calcular frequências
            freqs = np.fft.fftfreq(len(audio_chunk), 1/16000)  # Assumindo 16kHz
            
            # Calcular centroide
            positive_freqs = freqs[:len(freqs)//2]
            positive_magnitude = magnitude[:len(magnitude)//2]
            
            if np.sum(positive_magnitude) > 0:
                centroid = np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude)
                return float(centroid)
            else:
                return 1000.0  # Frequência padrão
                
        except Exception as e:
            self.logger.warning(f"Erro ao calcular centroide espectral: {e}")
            return 1000.0
    
    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Aplicar softmax aos logits."""
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / np.sum(exp_logits)
    
    def _process_sentiment_logits(self, logits: np.ndarray) -> float:
        """Processar logits de sentimento."""
        # Softmax para obter probabilidades
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        # Converter para score [-1, 1]
        # Assumindo: [negativo, neutro, positivo]
        if probs.shape[1] >= 3:
            negative_prob = probs[0, 0]
            positive_prob = probs[0, 2]
            sentiment_score = positive_prob - negative_prob
        else:
            sentiment_score = probs[0, 1] * 2 - 1  # [-1, 1]
        
        return float(sentiment_score)
    
    def _classify_emotion(self, sentiment_score: float) -> str:
        """Classificar emoção baseada no score de sentimento."""
        if sentiment_score > 0.3:
            return "positive"
        elif sentiment_score < -0.3:
            return "negative"
        else:
            return "neutral"
    
    def _process_objection_logits(self, logits: np.ndarray) -> Dict[str, Any]:
        """Processar logits de objeção."""
        # Softmax para obter probabilidades
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        # Categorias de objeção: [nenhuma, preco, timing, autoridade, necessidade]
        categories = ["nenhuma", "preco", "timing", "autoridade", "necessidade"]
        
        if probs.shape[1] >= len(categories):
            max_idx = np.argmax(probs[0])
            confidence = float(probs[0, max_idx])
            category = categories[max_idx]
            
            return {
                "detected": category != "nenhuma" and confidence > 0.5,
                "category": category,
                "confidence": confidence
            }
        
        return {
            "detected": False,
            "category": "nenhuma",
            "confidence": 0.0
        }
    
    def _classify_speaker(self, embeddings: np.ndarray) -> str:
        """Classificar speaker baseado nos embeddings."""
        # Implementação simplificada - em produção usar clustering
        # Por enquanto, alternar entre vendor e client
        return "vendor" if np.sum(embeddings) > 0 else "client"


class NPUManager(QObject):
    """Gerenciador principal da NPU."""
    
    # Sinais
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas
    objection_detected = pyqtSignal(str, list) # objeção, sugestões
    npu_status_changed = pyqtSignal(str)        # status
    inference_error = pyqtSignal(str, str)      # model_name, error
    
    def __init__(self, config, model_manager=None):
        super().__init__()
        self.config = config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Estado da NPU
        self.is_initialized = False
        self.available_providers = []
        self.loaded_models = {}
        self.active_workers = {}
        
        # Cache de resultados para evitar reprocessamento
        self.result_cache = {}
        self.cache_ttl = 5.0  # 5 segundos
        
        # Timer para simular processamento contínuo (apenas em demo)
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self._simulate_processing)
    
    def initialize(self):
        """Inicializar NPU e carregar modelos."""
        try:
            self.logger.info("🧠 Inicializando NPU Manager...")
            
            # Verificar disponibilidade do ONNX Runtime
            if not ONNX_AVAILABLE:
                raise ImportError("ONNX Runtime não disponível")
            
            # Verificar providers disponíveis
            self._check_available_providers()
            
            # Carregar modelos essenciais
            self._load_models()
            
            self.is_initialized = True
            self.npu_status_changed.emit("connected")
            self.logger.info("✅ NPU Manager inicializado")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar NPU: {e}")
            self.npu_status_changed.emit("error")
            # Continuar em modo simulação
            self._enable_simulation_mode()
    
    def _check_available_providers(self):
        """Verificar providers ONNX disponíveis."""
        self.available_providers = ort.get_available_providers()
        self.logger.info(f"Providers disponíveis: {self.available_providers}")
        
        # Verificar se QNN Provider está disponível
        if "QNNExecutionProvider" in self.available_providers:
            self.logger.info("✅ QNN Execution Provider detectado (NPU)")
        else:
            self.logger.warning("⚠️ QNN Provider não encontrado, usando CPU/GPU")
    
    def _load_models(self):
        """Carregar modelos ONNX na NPU."""
        if self.model_manager:
            # Usar ModelManager se disponível
            self.model_manager.load_manifest()
            
            # Carregar modelos essenciais
            essential_models = ["whisper_base", "distilbert_sentiment", "bert_objection", "ecapa_speaker"]
            
            for model_name in essential_models:
                try:
                    session = self.model_manager.load_model_session(model_name)
                    if session:
                        # Obter nome do input
                        input_name = session.get_inputs()[0].name
                        
                        self.loaded_models[model_name] = {
                            "session": session,
                            "input_name": input_name,
                            "status": "loaded"
                        }
                        self.logger.info(f"✅ Modelo {model_name} carregado via ModelManager")
                        self.logger.info(f"   Input: {input_name}")
                    else:
                        self.logger.warning(f"⚠️ Modelo {model_name} não pôde ser carregado")
                except Exception as e:
                    self.logger.error(f"❌ Erro ao carregar {model_name}: {e}")
        else:
            # Fallback para carregamento manual
            self._load_models_manual()
    
    def _load_models_manual(self):
        """Carregamento manual de modelos (fallback)."""
        models_to_load = {
            "whisper_base": "models/whisper_base.onnx",
            "distilbert_sentiment": "models/distilbert_sentiment.onnx", 
            "bert_objection": "models/bert_objection.onnx",
            "ecapa_speaker": "models/ecapa_speaker.onnx"
        }
        
        for model_name, model_path in models_to_load.items():
            try:
                full_path = self.config.app_dir / model_path
                
                if full_path.exists():
                    # Criar providers
                    providers = self._create_providers()
                    
                    # Carregar sessão
                    session = ort.InferenceSession(str(full_path), providers=providers)
                    input_name = session.get_inputs()[0].name
                    
                    self.loaded_models[model_name] = {
                        "session": session,
                        "input_name": input_name,
                        "status": "loaded"
                    }
                    self.logger.info(f"✅ Modelo {model_name} carregado manualmente")
                    self.logger.info(f"   Path: {full_path}")
                    self.logger.info(f"   Input: {input_name}")
                else:
                    self.logger.warning(f"⚠️ Modelo {model_path} não encontrado")
            except Exception as e:
                self.logger.error(f"❌ Erro ao carregar {model_name}: {e}")
    
    def _create_providers(self) -> List:
        """Criar lista de providers para carregamento manual."""
        providers = []
        
        # Priorizar QNN se disponível
        if "QNNExecutionProvider" in self.available_providers:
            providers.append(("QNNExecutionProvider", {}))
        
        # Adicionar CPU como fallback
        if "CPUExecutionProvider" in self.available_providers:
            providers.append("CPUExecutionProvider")
        
        return providers
    
    def _enable_simulation_mode(self):
        """Habilitar modo de simulação."""
        self.logger.info("🎭 Habilitando modo de simulação NPU")
        self.is_initialized = True
        self.npu_status_changed.emit("simulation")
        
        # Simular modelos carregados
        self.loaded_models = {
            "whisper_base": {"status": "simulated"},
            "distilbert_sentiment": {"status": "simulated"},
            "bert_objection": {"status": "simulated"},
            "ecapa_speaker": {"status": "simulated"}
        }
    
    def process_audio(self, audio_data: np.ndarray):
        """Processar áudio através da pipeline NPU."""
        if not self.is_initialized:
            return
        
        try:
            # Verificar cache para evitar reprocessamento
            cache_key = hash(audio_data.tobytes())
            if cache_key in self.result_cache:
                cached_time, cached_result = self.result_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    self.logger.debug("🔄 Usando resultado em cache")
                    return
            
            # Iniciar processamento assíncrono para múltiplos modelos
            self._process_transcription(audio_data)
            self._process_sentiment_analysis(audio_data)
            self._process_objection_detection(audio_data)
            self._process_speaker_detection(audio_data)
            
            # Cache do resultado
            self.result_cache[cache_key] = (time.time(), "processed")
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de áudio: {e}")
    
    def _process_transcription(self, audio_data: np.ndarray):
        """Processar transcrição via Whisper."""
        if "whisper_base" not in self.loaded_models:
            return
        
        model_info = self.loaded_models["whisper_base"]
        if model_info["status"] == "simulated":
            # Modo simulação
            self._simulate_transcription()
            return
        
        # Criar worker thread para Whisper
        worker = NPUWorkerThread(
            "whisper_base", 
            model_info["session"], 
            audio_data,
            model_info["input_name"]
        )
        worker.result_ready.connect(self._handle_transcription_result)
        worker.error_occurred.connect(self._handle_inference_error)
        worker.start()
        
        self.active_workers["whisper_base"] = worker
    
    def _process_sentiment_analysis(self, audio_data: np.ndarray):
        """Processar análise de sentimento."""
        if "distilbert_sentiment" not in self.loaded_models:
            return
        
        model_info = self.loaded_models["distilbert_sentiment"]
        if model_info["status"] == "simulated":
            # Modo simulação
            self._simulate_sentiment()
            return
        
        # Para sentimento, precisamos do texto transcrito
        # Isso será processado após a transcrição
        pass
    
    def _process_objection_detection(self, audio_data: np.ndarray):
        """Processar detecção de objeções."""
        if "bert_objection" not in self.loaded_models:
            return
        
        model_info = self.loaded_models["bert_objection"]
        if model_info["status"] == "simulated":
            # Modo simulação
            self._simulate_objection_detection()
            return
        
        # Para objeções, precisamos do texto transcrito
        # Isso será processado após a transcrição
        pass
    
    def _process_speaker_detection(self, audio_data: np.ndarray):
        """Processar detecção de speaker."""
        if "ecapa_speaker" not in self.loaded_models:
            return
        
        model_info = self.loaded_models["ecapa_speaker"]
        if model_info["status"] == "simulated":
            # Modo simulação
            self._simulate_speaker_detection()
            return
        
        # Criar worker thread para ECAPA
        worker = NPUWorkerThread(
            "ecapa_speaker", 
            model_info["session"], 
            audio_data,
            model_info["input_name"]
        )
        worker.result_ready.connect(self._handle_speaker_result)
        worker.error_occurred.connect(self._handle_inference_error)
        worker.start()
        
        self.active_workers["ecapa_speaker"] = worker
    
    def process_text_for_sentiment(self, text: str):
        """Processar texto para análise de sentimento."""
        if "distilbert_sentiment" not in self.loaded_models:
            return
        
        model_info = self.loaded_models["distilbert_sentiment"]
        if model_info["status"] == "simulated":
            return
        
        worker = NPUWorkerThread(
            "distilbert_sentiment", 
            model_info["session"], 
            text,
            model_info["input_name"]
        )
        worker.result_ready.connect(self._handle_sentiment_result)
        worker.error_occurred.connect(self._handle_inference_error)
        worker.start()
        
        self.active_workers["distilbert_sentiment"] = worker
    
    def process_text_for_objections(self, text: str):
        """Processar texto para detecção de objeções."""
        if "bert_objection" not in self.loaded_models:
            return
        
        model_info = self.loaded_models["bert_objection"]
        if model_info["status"] == "simulated":
            return
        
        worker = NPUWorkerThread(
            "bert_objection", 
            model_info["session"], 
            text,
            model_info["input_name"]
        )
        worker.result_ready.connect(self._handle_objection_result)
        worker.error_occurred.connect(self._handle_inference_error)
        worker.start()
        
        self.active_workers["bert_objection"] = worker
    
    def _handle_transcription_result(self, model_name: str, result: dict):
        """Processar resultado da transcrição."""
        if model_name == "whisper_base":
            text = result.get("text", "")
            speaker_id = result.get("speaker_id", "unknown")
            
            if text.strip():
                self.transcription_ready.emit(text, speaker_id)
                
                # Processar texto para sentimento e objeções
                self.process_text_for_sentiment(text)
                self.process_text_for_objections(text)
    
    def _handle_sentiment_result(self, model_name: str, result: dict):
        """Processar resultado da análise de sentimento."""
        if model_name == "distilbert_sentiment":
            self.sentiment_updated.emit(result)
    
    def _handle_objection_result(self, model_name: str, result: dict):
        """Processar resultado da detecção de objeções."""
        if model_name == "bert_objection":
            if result.get("objection_detected", False):
                category = result.get("category", "unknown")
                confidence = result.get("confidence", 0.0)
                
                # Gerar sugestões baseadas na categoria
                suggestions = self._generate_objection_suggestions(category, confidence)
                self.objection_detected.emit(category, suggestions)
    
    def _handle_speaker_result(self, model_name: str, result: dict):
        """Processar resultado da detecção de speaker."""
        if model_name == "ecapa_speaker":
            speaker_id = result.get("speaker_id", "unknown")
            self.logger.debug(f"Speaker detectado: {speaker_id}")
    
    def _handle_inference_error(self, model_name: str, error: str):
        """Processar erro de inferência."""
        self.logger.error(f"❌ Erro na inferência {model_name}: {error}")
        self.inference_error.emit(model_name, error)
    
    def _generate_objection_suggestions(self, category: str, confidence: float) -> List[Dict]:
        """Gerar sugestões para objeção detectada."""
        suggestions = []
        
        if category == "preco":
            suggestions = [
                {
                    "text": "Entendo sua preocupação sobre o preço. Vamos falar sobre o ROI...",
                    "confidence": confidence,
                    "category": "Objeção de Preço"
                },
                {
                    "text": "Posso mostrar um case de sucesso com ROI de 300%...",
                    "confidence": confidence * 0.9,
                    "category": "Prova Social"
                }
            ]
        elif category == "timing":
            suggestions = [
                {
                    "text": "Entendo a urgência. Podemos implementar em fases...",
                    "confidence": confidence,
                    "category": "Timing"
                }
            ]
        elif category == "autoridade":
            suggestions = [
                {
                    "text": "Quem mais precisa estar envolvido na decisão?",
                    "confidence": confidence,
                    "category": "Autoridade"
                }
            ]
        else:
            suggestions = [
                {
                    "text": "Entendo sua preocupação. Vamos explorar isso mais...",
                    "confidence": confidence,
                    "category": "Geral"
                }
            ]
        
        return suggestions
    
    # Métodos de simulação para modo demo
    def _simulate_transcription(self):
        """Simular transcrição."""
        import random
        sample_texts = [
            "Estou interessado na sua solução",
            "Qual é o preço do sistema?",
            "Preciso conversar com minha equipe",
            "Isso parece interessante"
        ]
        text = random.choice(sample_texts)
        speaker = random.choice(["vendor", "client"])
        self.transcription_ready.emit(text, speaker)
    
    def _simulate_sentiment(self):
        """Simular sentimento."""
        import random
        sentiment = random.uniform(-0.5, 0.8)
        result = {
            "sentiment": sentiment,
            "emotion": "positive" if sentiment > 0 else "negative",
            "engagement": random.uniform(0.3, 0.9),
            "inference_time_ms": random.uniform(10, 50)
        }
        self.sentiment_updated.emit(result)
    
    def _simulate_objection_detection(self):
        """Simular detecção de objeções."""
        import random
        if random.random() < 0.3:  # 30% chance
            categories = ["preco", "timing", "autoridade", "necessidade"]
            category = random.choice(categories)
            suggestions = self._generate_objection_suggestions(category, 0.8)
            self.objection_detected.emit(category, suggestions)
    
    def _simulate_speaker_detection(self):
        """Simular detecção de speaker."""
        import random
        speaker = random.choice(["vendor", "client"])
        self.logger.debug(f"Speaker simulado: {speaker}")
    
    def _simulate_processing(self):
        """Simular processamento contínuo para demo."""
        if not self.is_initialized:
            return
        
        # Simular processamento periódico
        import random
        
        if random.random() < 0.3:  # 30% chance
            self._simulate_transcription()
        
        if random.random() < 0.2:  # 20% chance
            self._simulate_sentiment()
        
        if random.random() < 0.1:  # 10% chance
            self._simulate_objection_detection()
    
    def start_demo_mode(self):
        """Iniciar modo de demonstração."""
        self.processing_timer.start(5000)  # A cada 5 segundos
    
    def stop_demo_mode(self):
        """Parar modo de demonstração."""
        self.processing_timer.stop()
    
    def get_model_status(self) -> Dict[str, Any]:
        """Obter status dos modelos."""
        status = {}
        for model_name, model_info in self.loaded_models.items():
            status[model_name] = {
                "status": model_info["status"],
                "loaded": model_info["status"] == "loaded"
            }
        return status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obter métricas de performance."""
        return {
            "models_loaded": len([m for m in self.loaded_models.values() if m["status"] == "loaded"]),
            "active_workers": len(self.active_workers),
            "cache_size": len(self.result_cache),
            "providers": self.available_providers
        }
    
    def cleanup(self):
        """Limpar recursos da NPU."""
        self.logger.info("🔄 Limpando recursos NPU...")
        
        # Parar workers ativos
        for worker in self.active_workers.values():
            if worker.isRunning():
                worker.quit()
                worker.wait()
        
        self.active_workers.clear()
        self.loaded_models.clear()
        self.result_cache.clear()
        self.stop_demo_mode()
        
        # Limpar ModelManager se disponível
        if self.model_manager:
            self.model_manager.cleanup()
        
        self.logger.info("✅ NPU Manager finalizado")

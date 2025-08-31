"""
PitchAI - ONNX Manager
======================

Gerenciador ONNX para execução de modelos de IA em tempo real.
Preparado para integração com modelos ONNX reais.
"""

import logging
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import time
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("⚠️ ONNX Runtime não disponível")


class ONNXManager(QObject):
    """Gerenciador ONNX para modelos de IA."""

    # Sinais para comunicação
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas de sentimento
    objection_detected = pyqtSignal(str, list) # objeção, sugestões

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Modelos ONNX (serão carregados quando disponíveis)
        self.whisper_model: Optional[ort.InferenceSession] = None
        self.sentiment_model: Optional[ort.InferenceSession] = None
        self.objection_model: Optional[ort.InferenceSession] = None
        self.speaker_model: Optional[ort.InferenceSession] = None
        
        # Configurações de performance
        self.audio_buffer_size = 20  # ms
        self.sentiment_window = 3    # segundos
        self.objection_threshold = 0.7
        self.sentiment_sensitivity = 0.3
        self.speaker_confidence = 0.9
        
        # Estado
        self.is_initialized = False
        self.models_loaded = False
        
        # Cache para otimização
        self._transcription_cache = {}
        self._sentiment_cache = {}
        
    def initialize(self):
        """Inicializar NPU Manager."""
        try:
            self.logger.info("Inicializando ONNX Manager...")
            
            # Verificar disponibilidade do ONNX Runtime
            if not ONNX_AVAILABLE:
                self.logger.warning("⚠️ ONNX Runtime não disponível - usando simulação")
                self._setup_simulation_mode()
                return
            
            # Verificar providers disponíveis
            providers = ort.get_available_providers()
            self.logger.info(f"Providers disponíveis: {providers}")
            
            # Tentar carregar modelos
            self._load_models()
            
            if self.models_loaded:
                self.logger.info("✅ Modelos ONNX carregados com sucesso")
            else:
                self.logger.warning("⚠️ Modelos não encontrados - usando simulação")
                self._setup_simulation_mode()
            
            self.is_initialized = True
            self.logger.info("✅ NPU Manager inicializado")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar NPU Manager: {e}")
            self._setup_simulation_mode()
    
    def _load_models(self):
        """Carregar modelos ONNX."""
        models_dir = Path(self.config.app_dir) / "models"
        
        if not models_dir.exists():
            self.logger.warning(f"⚠️ Diretório de modelos não encontrado: {models_dir}")
            return
        
        # Lista de modelos necessários
        model_files = {
            'whisper': models_dir / "whisper_base.onnx",
            'sentiment': models_dir / "distilbert_sentiment.onnx", 
            'objection': models_dir / "bert_objection.onnx",
            'speaker': models_dir / "ecapa_speaker.onnx"
        }
        
        # Verificar quais modelos estão disponíveis
        available_models = {}
        for name, path in model_files.items():
            if path.exists():
                available_models[name] = path
                self.logger.info(f"✅ Modelo {name} encontrado: {path}")
            else:
                self.logger.warning(f"⚠️ Modelo {name} não encontrado: {path}")
        
        if not available_models:
            self.logger.warning("⚠️ Nenhum modelo encontrado")
            return
        
        # Carregar modelos disponíveis
        try:
            # Configurar sessão ONNX
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Priorizar NPU se disponível
            providers = ['QNNExecutionProvider', 'CoreMLExecutionProvider', 'CPUExecutionProvider']
            available_providers = [p for p in providers if p in ort.get_available_providers()]
            
            if not available_providers:
                available_providers = ['CPUExecutionProvider']
            
            self.logger.info(f"Usando providers: {available_providers}")
            
            # Carregar cada modelo
            for name, path in available_models.items():
                try:
                    session = ort.InferenceSession(
                        str(path), 
                        sess_options=session_options,
                        providers=available_providers
                    )
                    
                    if name == 'whisper':
                        self.whisper_model = session
                    elif name == 'sentiment':
                        self.sentiment_model = session
                    elif name == 'objection':
                        self.objection_model = session
                    elif name == 'speaker':
                        self.speaker_model = session
                    
                    self.logger.info(f"✅ Modelo {name} carregado com sucesso")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao carregar modelo {name}: {e}")
            
            self.models_loaded = len(available_models) > 0
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar modelos: {e}")
    
    def _setup_simulation_mode(self):
        """Configurar modo de simulação quando modelos não estão disponíveis."""
        self.logger.info("🔧 Configurando modo de simulação")
        self.models_loaded = False
        
        # Configurações de simulação
        self.simulation_config = {
            'transcription_delay': 0.5,  # segundos
            'sentiment_update_interval': 3.0,  # segundos
            'objection_detection_rate': 0.1,  # 10% de chance
        }
    
    def transcribe_audio(self, audio_chunk: bytes, speaker_id: str = "unknown") -> Tuple[str, float]:
        """Transcrever áudio usando Whisper."""
        if self.whisper_model and self.models_loaded:
            return self._transcribe_with_model(audio_chunk, speaker_id)
        else:
            return self._simulate_transcription(audio_chunk, speaker_id)
    
    def _transcribe_with_model(self, audio_chunk: bytes, speaker_id: str) -> Tuple[str, float]:
        """Transcrever usando modelo Whisper real."""
        try:
            # Preparar input para o modelo
            # Nota: Esta é uma implementação base - ajustar conforme especificações do modelo
            audio_array = np.frombuffer(audio_chunk, dtype=np.float32)
            
            # Normalizar e preparar para o modelo
            if len(audio_array.shape) == 1:
                audio_array = audio_array.reshape(1, -1)
            
            # Executar inferência
            input_name = self.whisper_model.get_inputs()[0].name
            output_names = [output.name for output in self.whisper_model.get_outputs()]
            
            result = self.whisper_model.run(
                output_names,
                {input_name: audio_array}
            )
            
            # Processar resultado (ajustar conforme formato de saída do modelo)
            if len(result) >= 2:
                text = result[0] if isinstance(result[0], str) else str(result[0])
                confidence = float(result[1]) if len(result) > 1 else 0.8
            else:
                text = str(result[0]) if result else ""
                confidence = 0.8
            
            return text.strip(), confidence
            
        except Exception as e:
            self.logger.error(f"❌ Erro na transcrição com modelo: {e}")
            return self._simulate_transcription(audio_chunk, speaker_id)
    
    def _simulate_transcription(self, audio_chunk: bytes, speaker_id: str) -> Tuple[str, float]:
        """Simular transcrição quando modelo não está disponível."""
        import random
        
        # Simular delay de processamento
        time.sleep(self.simulation_config['transcription_delay'])
        
        # Frases de exemplo para simulação
        phrases = [
            "Entendo sua preocupação com o preço",
            "Vamos analisar o ROI do projeto",
            "Qual seria o prazo ideal para vocês?",
            "Posso enviar uma proposta detalhada",
            "Como está o orçamento disponível?",
            "Vamos fazer um piloto primeiro",
            "Qual é o processo de aprovação?",
            "Posso agendar uma demonstração",
            "Vamos discutir os benefícios",
            "Como podemos adaptar à sua necessidade"
        ]
        
        text = random.choice(phrases)
        confidence = random.uniform(0.7, 0.95)
        
        return text, confidence
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analisar sentimento do texto."""
        if self.sentiment_model and self.models_loaded:
            return self._analyze_sentiment_with_model(text)
        else:
            return self._simulate_sentiment(text)
    
    def _analyze_sentiment_with_model(self, text: str) -> Dict[str, Any]:
        """Analisar sentimento usando modelo real."""
        try:
            # Preparar input para o modelo
            # Nota: Ajustar conforme especificações do modelo de sentimento
            input_text = text[:512]  # Limitar tamanho se necessário
            
            # Tokenizar (ajustar conforme modelo específico)
            # Esta é uma implementação base
            input_name = self.sentiment_model.get_inputs()[0].name
            output_names = [output.name for output in self.sentiment_model.get_outputs()]
            
            # Executar inferência
            result = self.sentiment_model.run(
                output_names,
                {input_name: input_text}
            )
            
            # Processar resultado
            if len(result) >= 2:
                valence = float(result[0])
                engagement = float(result[1])
            else:
                valence = 0.5
                engagement = 0.5
            
            return {
                'valence': valence,
                'engagement': engagement,
                'timestamp': datetime.now(),
                'confidence': 0.8
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de sentimento: {e}")
            return self._simulate_sentiment(text)
    
    def _simulate_sentiment(self, text: str) -> Dict[str, Any]:
        """Simular análise de sentimento."""
        import random
        
        # Palavras-chave para simular sentimento
        positive_words = ['bom', 'ótimo', 'excelente', 'interessante', 'gosto', 'concordo']
        negative_words = ['caro', 'difícil', 'problema', 'não', 'ruim', 'preocupado']
        
        text_lower = text.lower()
        
        # Calcular sentimento baseado em palavras-chave
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            valence = random.uniform(0.6, 0.9)
        elif negative_count > positive_count:
            valence = random.uniform(0.1, 0.4)
        else:
            valence = random.uniform(0.4, 0.6)
        
        engagement = random.uniform(0.3, 0.8)
        
        return {
            'valence': valence,
            'engagement': engagement,
            'timestamp': datetime.now(),
            'confidence': random.uniform(0.7, 0.9)
        }
    
    def detect_objections(self, text: str) -> List[Dict[str, Any]]:
        """Detectar objeções no texto."""
        if self.objection_model and self.models_loaded:
            return self._detect_objections_with_model(text)
        else:
            return self._simulate_objection_detection(text)
    
    def _detect_objections_with_model(self, text: str) -> List[Dict[str, Any]]:
        """Detectar objeções usando modelo real."""
        try:
            # Preparar input para o modelo
            input_text = text[:512]
            
            input_name = self.objection_model.get_inputs()[0].name
            output_names = [output.name for output in self.objection_model.get_outputs()]
            
            # Executar inferência
            result = self.objection_model.run(
                output_names,
                {input_name: input_text}
            )
            
            # Processar resultado
            objections = []
            if len(result) >= 2:
                categories = ['preco', 'timing', 'autoridade', 'necessidade']
                confidences = result[1] if len(result) > 1 else [0.5] * 4
                
                for i, (category, confidence) in enumerate(zip(categories, confidences)):
                    if confidence > self.objection_threshold:
                        objections.append({
                            'category': category,
                            'confidence': float(confidence),
                            'text': text,
                            'timestamp': datetime.now()
                        })
            
            return objections
            
        except Exception as e:
            self.logger.error(f"❌ Erro na detecção de objeções: {e}")
            return self._simulate_objection_detection(text)
    
    def _simulate_objection_detection(self, text: str) -> List[Dict[str, Any]]:
        """Simular detecção de objeções."""
        import random
        
        objections = []
        text_lower = text.lower()
        
        # Palavras-chave para cada categoria
        objection_keywords = {
            'preco': ['caro', 'preço', 'custo', 'orçamento', 'valor'],
            'timing': ['prazo', 'tempo', 'quando', 'agenda', 'data'],
            'autoridade': ['chefe', 'diretor', 'aprovador', 'decisão'],
            'necessidade': ['preciso', 'necessidade', 'problema', 'solução']
        }
        
        for category, keywords in objection_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                if random.random() < self.simulation_config['objection_detection_rate']:
                    objections.append({
                        'category': category,
                        'confidence': random.uniform(0.7, 0.95),
                        'text': text,
                        'timestamp': datetime.now()
                    })
        
        return objections
    
    def identify_speaker(self, audio_chunk: bytes) -> Tuple[str, float]:
        """Identificar falante usando modelo de speaker ID."""
        if self.speaker_model and self.models_loaded:
            return self._identify_speaker_with_model(audio_chunk)
        else:
            return self._simulate_speaker_identification(audio_chunk)
    
    def _identify_speaker_with_model(self, audio_chunk: bytes) -> Tuple[str, float]:
        """Identificar falante usando modelo real."""
        try:
            # Preparar input para o modelo
            audio_array = np.frombuffer(audio_chunk, dtype=np.float32)
            
            input_name = self.speaker_model.get_inputs()[0].name
            output_names = [output.name for output in self.speaker_model.get_outputs()]
            
            # Executar inferência
            result = self.speaker_model.run(
                output_names,
                {input_name: audio_array}
            )
            
            # Processar resultado
            if len(result) >= 2:
                speaker_id = str(result[0])
                confidence = float(result[1])
            else:
                speaker_id = "unknown"
                confidence = 0.5
            
            return speaker_id, confidence
            
        except Exception as e:
            self.logger.error(f"❌ Erro na identificação de falante: {e}")
            return self._simulate_speaker_identification(audio_chunk)
    
    def _simulate_speaker_identification(self, audio_chunk: bytes) -> Tuple[str, float]:
        """Simular identificação de falante."""
        import random
        
        speakers = ["vendedor", "cliente"]
        speaker_id = random.choice(speakers)
        confidence = random.uniform(0.7, 0.95)
        
        return speaker_id, confidence
    
    def get_model_status(self) -> Dict[str, Any]:
        """Obter status dos modelos."""
        return {
            'models_loaded': self.models_loaded,
            'whisper_available': self.whisper_model is not None,
            'sentiment_available': self.sentiment_model is not None,
            'objection_available': self.objection_model is not None,
            'speaker_available': self.speaker_model is not None,
            'simulation_mode': not self.models_loaded
        }

    def process_audio(self, audio_data):
        """Processar dados de áudio e emitir sinais."""
        try:
            self.logger.debug(f"📡 Processando {len(audio_data)} bytes de áudio")

            # Processar transcrição
            transcription = self.transcribe_audio(audio_data)
            if transcription:
                self.transcription_ready.emit(transcription, "unknown")

            # Processar sentimento
            sentiment = self.analyze_sentiment(audio_data)
            if sentiment:
                self.sentiment_updated.emit(sentiment)

            # Detectar objeções
            objections = self.detect_objections(audio_data)
            if objections:
                self.objection_detected.emit(objections[0], objections[1:])

        except Exception as e:
            self.logger.error(f"❌ Erro ao processar áudio: {e}")

    def cleanup(self):
        """Limpar recursos do ONNX Manager."""
        self.logger.info("🧹 Limpando ONNX Manager...")
        self.shutdown()

    def shutdown(self):
        """Encerrar NPU Manager."""
        self.logger.info("🔄 Encerrando NPU Manager...")
        
        # Limpar cache
        self._transcription_cache.clear()
        self._sentiment_cache.clear()
        
        self.logger.info("✅ NPU Manager encerrado")

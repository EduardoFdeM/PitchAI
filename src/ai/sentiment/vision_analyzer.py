"""
Vision Analyzer - RF-3.3: Motor de visão (opcional)
=================================================

Análise de expressões faciais para complementar sentimento e engajamento.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️ ONNX Runtime não disponível. Usando simulação.")

from .models import Face, Expression, SentimentConfig


class VisionAnalyzer:
    """RF-3.3: Motor de visão (opcional)"""
    
    def __init__(self, config: SentimentConfig = None, model_manager=None, opt_in: bool = False):
        self.config = config or SentimentConfig()
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuração de privacidade
        self.enabled = opt_in and self.config.enable_vision
        
        # Modelo ONNX para detecção facial
        self.face_detector = None
        self.expression_classifier = None
        
        # Configurações de processamento
        self.frame_width = 640
        self.frame_height = 480
        self.face_confidence_threshold = 0.7
        
        # Inicializar se habilitado
        if self.enabled:
            self._initialize_models()
    
    def _initialize_models(self):
        """Inicializar modelos de visão."""
        try:
            if not ONNX_AVAILABLE:
                self.logger.warning("ONNX não disponível, usando simulação")
                return
            
            # Tentar carregar via ModelManager
            if self.model_manager:
                self.expression_classifier = self.model_manager.get_session("face_expression")
                if self.expression_classifier:
                    self.logger.info("✅ Modelo de expressão facial carregado via ModelManager")
                    return
            
            # Fallback para carregamento manual
            model_path = "models/face_expression.onnx"
            providers = ["QNNExecutionProvider", "CPUExecutionProvider"]
            
            try:
                self.expression_classifier = ort.InferenceSession(model_path, providers=providers)
                self.logger.info(f"✅ Modelo de expressão facial carregado: {model_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar modelo: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização dos modelos: {e}")
    
    def is_enabled(self) -> bool:
        """Verificar se a análise visual está habilitada."""
        return self.enabled
    
    def enable_analysis(self, opt_in: bool = True):
        """Habilitar análise visual (opt-in)."""
        if opt_in:
            self.enabled = True
            self.config.enable_vision = True
            self._initialize_models()
            self.logger.info("✅ Análise visual habilitada (opt-in)")
        else:
            self.enabled = False
            self.config.enable_vision = False
            self.logger.info("❌ Análise visual desabilitada")
    
    def detect_faces(self, frame: np.ndarray) -> List[Face]:
        """Detectar faces na imagem."""
        if not self.enabled:
            return []
        
        try:
            if self.face_detector:
                # Usar modelo ONNX real
                return self._detect_faces_with_model(frame)
            else:
                # Simulação para desenvolvimento
                return self._simulate_face_detection(frame)
                
        except Exception as e:
            self.logger.error(f"Erro na detecção de faces: {e}")
            return []
    
    def _detect_faces_with_model(self, frame: np.ndarray) -> List[Face]:
        """Detecção usando modelo ONNX."""
        try:
            # TODO: Implementar detecção real
            # Por enquanto, usar simulação
            return self._simulate_face_detection(frame)
            
        except Exception as e:
            self.logger.error(f"Erro no modelo de detecção: {e}")
            return self._simulate_face_detection(frame)
    
    def _simulate_face_detection(self, frame: np.ndarray) -> List[Face]:
        """Simular detecção de faces."""
        faces = []
        
        # Simular 0-2 faces baseado no tamanho da imagem
        height, width = frame.shape[:2]
        
        # Probabilidade de detectar face baseada no tamanho
        face_probability = min(width * height / (640 * 480), 0.8)
        
        if np.random.random() < face_probability:
            # Simular uma face
            face = Face(
                bbox=[width//4, height//4, width//2, height//2],  # centro da imagem
                landmarks=[[width//2, height//3], [width//2, height//2]],  # pontos básicos
                confidence=0.85
            )
            faces.append(face)
        
        return faces
    
    def classify_expressions(self, faces: List[Face]) -> List[Expression]:
        """Classificar expressões faciais."""
        if not self.enabled or not faces:
            return []
        
        try:
            expressions = []
            
            for i, face in enumerate(faces):
                if self.expression_classifier:
                    # Usar modelo ONNX real
                    expression = self._classify_with_model(face, i)
                else:
                    # Simulação
                    expression = self._simulate_expression_classification(face, i)
                
                if expression:
                    expressions.append(expression)
            
            return expressions
            
        except Exception as e:
            self.logger.error(f"Erro na classificação de expressões: {e}")
            return []
    
    def _classify_with_model(self, face: Face, face_id: int) -> Optional[Expression]:
        """Classificação usando modelo ONNX."""
        try:
            # TODO: Implementar classificação real
            # Por enquanto, usar simulação
            return self._simulate_expression_classification(face, face_id)
            
        except Exception as e:
            self.logger.error(f"Erro no modelo de classificação: {e}")
            return self._simulate_expression_classification(face, face_id)
    
    def _simulate_expression_classification(self, face: Face, face_id: int) -> Optional[Expression]:
        """Simular classificação de expressões."""
        # Expressões possíveis
        possible_expressions = [
            "neutral", "joy", "surprise", "sadness", "anger", "fear", "disgust"
        ]
        
        # Simular expressão baseada na confiança da face
        if face.confidence > 0.8:
            # Face bem detectada - expressão mais confiável
            expression = np.random.choice(possible_expressions, p=[0.4, 0.2, 0.1, 0.1, 0.05, 0.05, 0.1])
            confidence = np.random.uniform(0.7, 0.95)
        else:
            # Face mal detectada - mais neutro
            expression = np.random.choice(possible_expressions, p=[0.7, 0.1, 0.05, 0.05, 0.02, 0.02, 0.06])
            confidence = np.random.uniform(0.3, 0.6)
        
        intensity = np.random.uniform(0.3, 0.9)
        
        return Expression(
            face_id=face_id,
            expression=expression,
            confidence=confidence,
            intensity=intensity
        )
    
    def analyze_frame(self, frame: np.ndarray, ts_ms: int) -> Dict[str, Any]:
        """Análise completa de um frame."""
        if not self.enabled:
            return {
                "enabled": False,
                "faces_detected": 0,
                "expressions": [],
                "sentiment": 0.0,
                "engagement": 0.0,
                "ts_ms": ts_ms
            }
        
        try:
            # Detectar faces
            faces = self.detect_faces(frame)
            
            # Classificar expressões
            expressions = self.classify_expressions(faces)
            
            # Calcular sentimento e engajamento
            sentiment = self._calculate_visual_sentiment(expressions)
            engagement = self._calculate_visual_engagement(expressions)
            
            return {
                "enabled": True,
                "faces_detected": len(faces),
                "expressions": expressions,
                "sentiment": sentiment,
                "engagement": engagement,
                "ts_ms": ts_ms,
                "confidence": np.mean([e.confidence for e in expressions]) if expressions else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de frame: {e}")
            return {
                "enabled": True,
                "faces_detected": 0,
                "expressions": [],
                "sentiment": 0.0,
                "engagement": 0.0,
                "ts_ms": ts_ms,
                "error": str(e)
            }
    
    def _calculate_visual_sentiment(self, expressions: List[Expression]) -> float:
        """Calcular sentimento baseado em expressões faciais."""
        if not expressions:
            return 0.0
        
        # Mapeamento de expressões para sentimento (-1 a +1)
        expression_sentiment = {
            "joy": 0.8,
            "surprise": 0.3,
            "neutral": 0.0,
            "sadness": -0.6,
            "anger": -0.8,
            "fear": -0.7,
            "disgust": -0.5
        }
        
        # Calcular sentimento ponderado por confiança
        total_weight = 0.0
        weighted_sentiment = 0.0
        
        for expr in expressions:
            sentiment_value = expression_sentiment.get(expr.expression, 0.0)
            weight = expr.confidence * expr.intensity
            
            weighted_sentiment += sentiment_value * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_sentiment / total_weight
        else:
            return 0.0
    
    def _calculate_visual_engagement(self, expressions: List[Expression]) -> float:
        """Calcular engajamento baseado em expressões faciais."""
        if not expressions:
            return 0.0
        
        # Expressões que indicam engajamento
        engagement_expressions = ["joy", "surprise", "interest"]
        
        # Calcular engajamento baseado na presença de expressões de interesse
        engagement_score = 0.0
        total_weight = 0.0
        
        for expr in expressions:
            weight = expr.confidence * expr.intensity
            
            if expr.expression in engagement_expressions:
                engagement_score += weight
            elif expr.expression == "neutral":
                engagement_score += weight * 0.3  # neutro = baixo engajamento
            
            total_weight += weight
        
        if total_weight > 0:
            return np.clip(engagement_score / total_weight, 0.0, 1.0)
        else:
            return 0.0
    
    def get_visual_metrics(self) -> Dict[str, Any]:
        """Obter métricas de análise visual."""
        return {
            "enabled": self.enabled,
            "opt_in": self.config.enable_vision,
            "models_loaded": {
                "face_detector": self.face_detector is not None,
                "expression_classifier": self.expression_classifier is not None
            },
            "frame_size": f"{self.frame_width}x{self.frame_height}",
            "confidence_threshold": self.face_confidence_threshold
        }
    
    def cleanup(self):
        """Limpar recursos de visão."""
        self.enabled = False
        self.config.enable_vision = False
        self.logger.info("Recursos de análise visual limpos") 
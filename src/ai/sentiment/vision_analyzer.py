"""
Vision Analyzer - RF-3.3: Motor de visão (opcional)
=================================================

Análise de expressões faciais para complementar sentimento e engajamento usando AnythingLLM.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
import base64
import io
from PIL import Image
import time

from .models import Face, Expression, SentimentConfig
from ...core.event_bus import publish_event
from ...core.contracts import EventType, create_error


class VisionAnalyzer:
    """Analisador de expressões faciais."""
    
    analysis_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config: SentimentConfig = None, opt_in: bool = False):
        super().__init__()
        self.config = config or SentimentConfig()
        self.is_enabled_flag = opt_in
        self.logger = logging.getLogger(__name__)
        
        # TODO: Adicionar inicialização de modelos de visão ONNX
        self.face_detector = None
        self.expression_classifier = None
        
        self.frame_count = 0
        self.last_analysis_time = 0

    def is_enabled(self) -> bool:
        """Verifica se a análise de vídeo está habilitada."""
        return self.is_enabled_flag

    def classify_expressions(self, faces: List[Face]) -> List[Expression]:
        """Classificar expressões faciais usando AnythingLLM."""
        if not self.is_enabled_flag or not faces:
            return []
        
        try:
            if self.anythingllm_client:
                return self._classify_with_anythingllm(faces)
            else:
                return self._simulate_expressions(faces)
                
        except Exception as e:
            self.logger.error(f"Erro na classificação de expressões: {e}")
            return []
    
    def _classify_with_anythingllm(self, faces: List[Face]) -> List[Expression]:
        """Classificar expressões usando AnythingLLM."""
        try:
            expressions = []
            
            for i, face in enumerate(faces):
                # Preparar descrição da face
                face_desc = f"""
                Face #{i+1}:
                - Confiança de detecção: {face.confidence:.2f}
                - Posição: {face.bbox}
                - Número de landmarks: {len(face.landmarks)}
                """
                
                # Prompt para classificação
                system_prompt = (
                    "Você é um especialista em análise de expressões faciais. "
                    "Analise a face descrita e determine a expressão emocional dominante. "
                    "Responda APENAS com: expressão,confiança,intensidade "
                    "onde expressão = joy/surprise/doubt/anger/sadness/neutral, "
                    "confiança = 0.0-1.0, intensidade = 0.0-1.0. "
                    "Exemplo: joy,0.85,0.7"
                )
                
                user_prompt = f"{face_desc}\n\nExpressão (formato: expressão,confiança,intensidade):"
                
                # Configurar payload
                payload = {
                    "model": self.anythingllm_client.default_model,
                    "temperature": 0.1,
                    "stream": False,
                    "max_tokens": 20,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
                
                # Fazer requisição
                response = self.anythingllm_client._make_request(payload, stream=False)
                
                if response.status_code != 200:
                    self.logger.warning(f"Erro na API AnythingLLM: {response.status_code}")
                    # Publicar erro no EventBus
                    error_event = create_error("rag", "anythingllm_api_error", 
                                             f"Erro na API AnythingLLM: {response.status_code}")
                    publish_event(EventType.ERROR.value, error_event.to_dict())
                    continue
                
                # Processar resposta
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                
                # Parsear resposta
                try:
                    parts = content.split(',')
                    if len(parts) >= 3:
                        expression_name = parts[0].strip()
                        confidence = float(parts[1].strip())
                        intensity = float(parts[2].strip())
                        
                        # Validar expressão
                        valid_expressions = ['joy', 'surprise', 'doubt', 'anger', 'sadness', 'neutral']
                        if expression_name not in valid_expressions:
                            expression_name = 'neutral'
                        
                        expr = Expression(
                            face_id=i,
                            expression=expression_name,
                            confidence=np.clip(confidence, 0.0, 1.0),
                            intensity=np.clip(intensity, 0.0, 1.0)
                        )
                        expressions.append(expr)
                        
                except (ValueError, IndexError):
                    self.logger.warning(f"Resposta inválida do AnythingLLM: {content}")
                    continue
            
            return expressions
            
        except Exception as e:
            self.logger.error(f"Erro na classificação com AnythingLLM: {e}")
            # Publicar erro no EventBus
            error_event = create_error("sentiment", "vision_analysis_error", 
                                     f"Erro na análise visual: {e}")
            publish_event(EventType.ERROR.value, error_event.to_dict())
            return self._simulate_expressions(faces)
    
    def _simulate_expressions(self, faces: List[Face]) -> List[Expression]:
        """Simular classificação de expressões."""
        expressions = []
        for i, face in enumerate(faces):
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
            
            expressions.append(Expression(
                face_id=i,
                expression=expression,
                confidence=confidence,
                intensity=intensity
            ))
        return expressions
    
    def analyze_frame(self, frame: np.ndarray, ts_ms: int) -> Dict[str, Any]:
        """Análise completa de um frame."""
        if not self.is_enabled_flag:
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
            
            result = {
                "enabled": True,
                "faces_detected": len(faces),
                "expressions": expressions,
                "sentiment": sentiment,
                "engagement": engagement,
                "ts_ms": ts_ms,
                "confidence": np.mean([e.confidence for e in expressions]) if expressions else 0.0
            }
            
            # Publicar métricas de visão no EventBus se houver faces detectadas
            if faces:
                vision_metrics = {
                    "faces_detected": len(faces),
                    "sentiment": sentiment,
                    "engagement": engagement,
                    "confidence": result["confidence"],
                    "ts_ms": ts_ms
                }
                # Nota: Este evento seria usado para complementar o sentimento geral
                # publish_event("vision.metrics", vision_metrics)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na análise de frame: {e}")
            # Publicar erro no EventBus
            error_event = create_error("sentiment", "vision_frame_error", 
                                     f"Erro na análise de frame: {e}")
            publish_event(EventType.ERROR.value, error_event.to_dict())
            
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
            "enabled": self.is_enabled_flag,
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
        self.is_enabled_flag = False
        self.config.enable_vision = False
        self.logger.info("Recursos de análise visual limpos") 
    
    def enable_analysis(self, opt_in: bool = True):
        """Habilitar análise visual (opt-in)."""
        if opt_in:
            self.is_enabled_flag = True
            self.config.enable_vision = True
            self.logger.info("✅ Análise visual habilitada (opt-in)")
        else:
            self.is_enabled_flag = False
            self.config.enable_vision = False
            self.logger.info("❌ Análise visual desabilitada")
    
    def detect_faces(self, frame: np.ndarray) -> List[Face]:
        """Detectar faces na imagem."""
        if not self.is_enabled_flag:
            return []
        
        try:
            # Simulação para desenvolvimento
            # Em produção, usar detector de faces real
            return self._simulate_face_detection(frame)
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de faces: {e}")
            return []
    
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
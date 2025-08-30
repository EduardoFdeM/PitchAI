"""
Fusion Engine - RF-3.4: Fusão de dados
=====================================

Fusão de dados de texto, prosódia e visão para análise de sentimento.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .models import SentimentSample, SentimentConfig


class FusionEngine:
    """RF-3.4: Fusão de dados"""
    
    def __init__(self, config: SentimentConfig = None):
        self.config = config or SentimentConfig()
        self.logger = logging.getLogger(__name__)
        
        # Pesos padrão de fusão
        self.weights = {
            "text": self.config.text_weight,
            "voice": self.config.voice_weight,
            "vision": self.config.vision_weight
        }
        
        # Histórico para suavização temporal
        self.sentiment_history = []
        self.engagement_history = []
        self.history_window = 5  # últimos 5 samples
    
    def fuse_sentiment(self, text_score: float, voice_score: float, 
                      vision_score: Optional[float] = None) -> float:
        """Fundir scores de sentimento."""
        try:
            # Preparar scores disponíveis
            scores = {"text": text_score, "voice": voice_score}
            available_weights = {"text": self.weights["text"], "voice": self.weights["voice"]}
            
            # Adicionar visão se disponível
            if vision_score is not None:
                scores["vision"] = vision_score
                available_weights["vision"] = self.weights["vision"]
            
            # Normalizar pesos para fontes disponíveis
            total_weight = sum(available_weights.values())
            if total_weight == 0:
                return 0.0
            
            normalized_weights = {k: v / total_weight for k, v in available_weights.items()}
            
            # Fusão ponderada
            fused_score = sum(scores[source] * normalized_weights[source] 
                            for source in scores.keys())
            
            # Suavização temporal
            fused_score = self._apply_temporal_smoothing(fused_score, "sentiment")
            
            return np.clip(fused_score, -1.0, 1.0)
            
        except Exception as e:
            self.logger.error(f"Erro na fusão de sentimento: {e}")
            return 0.0
    
    def fuse_engagement(self, text_eng: float, voice_eng: float,
                       vision_eng: Optional[float] = None) -> float:
        """Fundir scores de engajamento."""
        try:
            # Preparar scores disponíveis
            scores = {"text": text_eng, "voice": voice_eng}
            available_weights = {"text": self.weights["text"], "voice": self.weights["voice"]}
            
            # Adicionar visão se disponível
            if vision_eng is not None:
                scores["vision"] = vision_eng
                available_weights["vision"] = self.weights["vision"]
            
            # Normalizar pesos para fontes disponíveis
            total_weight = sum(available_weights.values())
            if total_weight == 0:
                return 0.0
            
            normalized_weights = {k: v / total_weight for k, v in available_weights.items()}
            
            # Fusão ponderada
            fused_score = sum(scores[source] * normalized_weights[source] 
                            for source in scores.keys())
            
            # Suavização temporal
            fused_score = self._apply_temporal_smoothing(fused_score, "engagement")
            
            return np.clip(fused_score, 0.0, 1.0)
            
        except Exception as e:
            self.logger.error(f"Erro na fusão de engajamento: {e}")
            return 0.0
    
    def _apply_temporal_smoothing(self, score: float, metric_type: str) -> float:
        """Aplicar suavização temporal."""
        try:
            if metric_type == "sentiment":
                history = self.sentiment_history
            else:
                history = self.engagement_history
            
            # Adicionar novo score ao histórico
            history.append(score)
            
            # Manter apenas os últimos N scores
            if len(history) > self.history_window:
                history.pop(0)
            
            # Calcular média ponderada (mais peso para scores recentes)
            if len(history) == 1:
                return score
            
            weights = np.linspace(0.5, 1.0, len(history))
            weights = weights / np.sum(weights)
            
            smoothed_score = np.average(history, weights=weights)
            
            return smoothed_score
            
        except Exception as e:
            self.logger.warning(f"Erro na suavização temporal: {e}")
            return score
    
    def create_sentiment_sample(self, call_id: str, ts_start_ms: int, ts_end_ms: int,
                               text_analysis: Dict[str, Any],
                               voice_analysis: Dict[str, Any],
                               vision_analysis: Optional[Dict[str, Any]] = None) -> SentimentSample:
        """Criar amostra de sentimento fundida."""
        try:
            # Extrair scores individuais
            text_sentiment = text_analysis.get("sentiment", 0.0)
            text_engagement = text_analysis.get("engagement", 0.0)
            
            voice_valence = voice_analysis.get("valence", 0.0)
            voice_engagement = self._estimate_voice_engagement(voice_analysis)
            
            vision_sentiment = None
            vision_engagement = None
            if vision_analysis:
                vision_sentiment = vision_analysis.get("sentiment", 0.0)
                vision_engagement = vision_analysis.get("engagement", 0.0)
            
            # Fundir scores
            fused_sentiment = self.fuse_sentiment(text_sentiment, voice_valence, vision_sentiment)
            fused_engagement = self.fuse_engagement(text_engagement, voice_engagement, vision_engagement)
            
            # Preparar detalhes
            details = {
                "text_analysis": text_analysis,
                "voice_analysis": voice_analysis,
                "fusion_weights": self.weights.copy()
            }
            
            if vision_analysis:
                details["vision_analysis"] = vision_analysis
            
            # Criar amostra
            sample = SentimentSample(
                call_id=call_id,
                ts_start_ms=ts_start_ms,
                ts_end_ms=ts_end_ms,
                score_valence=fused_sentiment,
                score_engagement=fused_engagement,
                weights=self.weights.copy(),
                details=details
            )
            
            return sample
            
        except Exception as e:
            self.logger.error(f"Erro na criação de amostra: {e}")
            return SentimentSample(
                call_id=call_id,
                ts_start_ms=ts_start_ms,
                ts_end_ms=ts_end_ms,
                score_valence=0.0,
                score_engagement=0.0,
                weights=self.weights.copy(),
                details={"error": str(e)}
            )
    
    def _estimate_voice_engagement(self, voice_analysis: Dict[str, Any]) -> float:
        """Estimar engajamento baseado na análise de voz."""
        try:
            features = voice_analysis.get("features")
            if not features:
                return 0.5
            
            engagement_score = 0.0
            
            # Taxa de fala moderada = mais engajamento
            speaking_rate = getattr(features, 'speaking_rate', 3.0)
            if 2.0 <= speaking_rate <= 5.0:
                engagement_score += 0.3
            elif 1.5 <= speaking_rate <= 6.0:
                engagement_score += 0.2
            
            # Menos pausas = mais engajamento
            pause_ratio = getattr(features, 'pause_ratio', 0.3)
            if pause_ratio < 0.2:
                engagement_score += 0.3
            elif pause_ratio < 0.4:
                engagement_score += 0.2
            
            # Energia consistente = mais engajamento
            energy_std = getattr(features, 'energy_std', 0.05)
            if energy_std < 0.05:
                engagement_score += 0.2
            elif energy_std < 0.1:
                engagement_score += 0.1
            
            # F0 estável = mais engajamento
            f0_std = getattr(features, 'f0_std', 50.0)
            if f0_std < 30:
                engagement_score += 0.2
            elif f0_std < 60:
                engagement_score += 0.1
            
            return np.clip(engagement_score, 0.0, 1.0)
            
        except Exception as e:
            self.logger.warning(f"Erro na estimativa de engajamento vocal: {e}")
            return 0.5
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Atualizar pesos de fusão."""
        try:
            # Validar pesos
            total_weight = sum(new_weights.values())
            if total_weight <= 0:
                self.logger.warning("Pesos inválidos, mantendo configuração atual")
                return
            
            # Normalizar pesos
            normalized_weights = {k: v / total_weight for k, v in new_weights.items()}
            
            # Atualizar pesos
            self.weights.update(normalized_weights)
            
            # Atualizar configuração
            self.config.text_weight = self.weights.get("text", 0.5)
            self.config.voice_weight = self.weights.get("voice", 0.3)
            self.config.vision_weight = self.weights.get("vision", 0.2)
            
            self.logger.info(f"Pesos de fusão atualizados: {self.weights}")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar pesos: {e}")
    
    def get_fusion_confidence(self, text_analysis: Dict[str, Any],
                            voice_analysis: Dict[str, Any],
                            vision_analysis: Optional[Dict[str, Any]] = None) -> float:
        """Calcular confiança da fusão."""
        try:
            confidences = []
            
            # Confiança do texto (baseada na presença de palavras-chave)
            text_keywords = text_analysis.get("keywords", [])
            text_confidence = min(len(text_keywords) * 0.2, 1.0) if text_keywords else 0.5
            confidences.append(text_confidence)
            
            # Confiança da voz (baseada na qualidade do áudio)
            voice_features = voice_analysis.get("features")
            if voice_features:
                # F0 válido indica boa qualidade
                f0_mean = getattr(voice_features, 'f0_mean', 0)
                voice_confidence = 0.8 if 80 <= f0_mean <= 400 else 0.4
            else:
                voice_confidence = 0.3
            confidences.append(voice_confidence)
            
            # Confiança da visão (se disponível)
            if vision_analysis:
                vision_confidence = vision_analysis.get("confidence", 0.5)
                confidences.append(vision_confidence)
            
            # Média ponderada das confianças
            if confidences:
                return np.mean(confidences)
            else:
                return 0.5
                
        except Exception as e:
            self.logger.warning(f"Erro no cálculo de confiança: {e}")
            return 0.5
    
    def clear_history(self):
        """Limpar histórico de suavização."""
        self.sentiment_history.clear()
        self.engagement_history.clear()
        self.logger.info("Histórico de fusão limpo")
    
    def get_fusion_stats(self) -> Dict[str, Any]:
        """Obter estatísticas da fusão."""
        return {
            "weights": self.weights.copy(),
            "sentiment_history_length": len(self.sentiment_history),
            "engagement_history_length": len(self.engagement_history),
            "history_window": self.history_window
        } 
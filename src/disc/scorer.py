"""
DISC Scorer
==========

Calcula scores DISC (Dominância, Influência, eStabilidade, Consciência)
baseado em features linguísticas e prosódicas extraídas.
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def _clip01(x: float) -> float:
    """Limita valor entre 0 e 1."""
    return float(max(0.0, min(1.0, x)))


def _agg(features: List[Dict], keys: List[str]) -> tuple[Dict[str, float], Dict[str, float]]:
    """Agrega features usando mediana e variância."""
    A = {k: np.array([f.get(k, 0.0) for f in features], dtype=float) for k in keys}
    med = {k: float(np.median(A[k])) for k in keys}
    var = {k: float(np.var(A[k])) for k in keys}
    return med, var


class DiscScorer:
    """Calculador de scores DISC baseado em features extraídas."""
    
    def __init__(self):
        # Pesos para cada dimensão DISC (baseado em metodologia prática)
        self.weights = {
            'D': {  # Dominância
                'talk_ratio': 0.35,
                'imperatives': 0.35,
                'hedges': -0.15,  # Negativo - hedges reduzem dominância
                'interrupt_rate': 0.15
            },
            'I': {  # Influência
                'open_questions': 0.40,
                'empathy': 0.35,
                'valence_var': 0.25
            },
            'S': {  # eStabilidade
                'interrupt_rate': -0.45,  # Negativo - interrupções reduzem estabilidade
                'empathy': 0.35,
                'turn_balance': 0.20
            },
            'C': {  # Consciência
                'structure': 0.40,
                'closed_questions': 0.35,
                'risk_aversion': 0.25
            }
        }
    
    def score_disc(self, features: List[Dict[str, float]], normalizer=None, model=None) -> Dict[str, Any]:
        """
        Calcula scores DISC a partir de features extraídas.
        
        Args:
            features: Lista de dicionários com features por janela
            normalizer: StatsService para normalização dinâmica
            model: Modelo ONNX opcional para refinamento
            
        Returns:
            Dict com scores D, I, S, C, confidence e sample_size
        """
        if not features:
            return self._default_scores()
        
        try:
            # Definir todas as features disponíveis
            keys = ["talk_ratio", "imperatives", "hedges", "interrupt_rate", "open_questions",
                    "empathy", "valence_var", "turn_balance", "structure", "closed_questions",
                    "risk_aversion", "wpm", "latency", "ttr", "assert_ratio", "question_ratio"]
            
            # Agregação robusta (mediana + variância)
            med, var = _agg(features, keys)
            
            # Função de normalização
            def N(k):
                x = med.get(k, 0.0)
                return normalizer.normalize("seller_feature", k, x, method="z") if normalizer else x
            
            # Fórmula revista com novas features
            D = (0.25 * N("talk_ratio") + 0.25 * N("imperatives") + 
                 0.15 * N("assert_ratio") + 0.15 * N("wpm") - 
                 0.10 * N("hedges") + 0.10 * N("interrupt_rate"))
            
            I = (0.30 * N("open_questions") + 0.25 * N("empathy") + 
                 0.20 * N("valence_var") + 0.15 * N("ttr") + 
                 0.10 * N("question_ratio"))
            
            S = (0.35 * (1 - N("interrupt_rate")) + 0.25 * N("empathy") + 
                 0.20 * N("turn_balance") + 0.20 * N("latency"))
            
            C = (0.35 * N("structure") + 0.25 * N("closed_questions") + 
                 0.20 * N("risk_aversion") + 0.20 * (1 - N("valence_var")))
            
            # Opcional: sobrepor com modelo leve ONNX
            if model is not None:
                try:
                    Dm, Im, Sm, Cm = model.predict(med)  # modelo opcional ONNX
                    alpha = 0.6
                    D = alpha * Dm + (1 - alpha) * D
                    I = alpha * Im + (1 - alpha) * I
                    S = alpha * Sm + (1 - alpha) * S
                    C = alpha * Cm + (1 - alpha) * C
                except Exception as e:
                    logger.warning(f"Erro no modelo ONNX: {e}, usando apenas heurística")
            
            # Confiança: ↑ com #janelas e ↓ com variância
            n = len(features)
            v = np.mean([var.get(k, 0.0) for k in ["talk_ratio", "empathy", "interrupt_rate", "wpm", "latency"]])
            confidence = float(min(1.0, (n / 200.0))) * float(1.0 / (1.0 + v))
            
            # Clamp final
            D, I, S, C = [_clip01(x) for x in (D, I, S, C)]
            
            result = {
                'D': D,
                'I': I, 
                'S': S,
                'C': C,
                'confidence': confidence,
                'n': n,
                'var': float(v)
            }
            
            logger.info(f"Scores DISC calculados: D={D:.2f}, I={I:.2f}, "
                       f"S={S:.2f}, C={C:.2f}, conf={confidence:.2f}, var={v:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao calcular scores DISC: {e}")
            return self._default_scores()
    
    def _default_scores(self) -> Dict[str, Any]:
        """Retorna scores padrão quando não há dados suficientes."""
        return {
            'D': 0.25,
            'I': 0.25,
            'S': 0.25,
            'C': 0.25,
            'confidence': 0.0,
            'n': 0
        }
    
    def _calculate_feature_means(self, features: List[Dict[str, float]]) -> Dict[str, float]:
        """Calcula médias das features por janela."""
        if not features:
            return {}
        
        # Obter todas as chaves de features
        all_keys = set()
        for feat in features:
            all_keys.update(feat.keys())
        
        # Calcular médias
        means = {}
        for key in all_keys:
            values = [feat.get(key, 0.0) for feat in features]
            means[key] = float(np.mean(values))
        
        return means
    
    def _calculate_disc_scores(self, feature_means: Dict[str, float]) -> Dict[str, float]:
        """Calcula scores DISC usando pesos pré-definidos."""
        scores = {}
        
        # Dominância (D)
        d_score = 0.0
        for feature, weight in self.weights['D'].items():
            if feature in feature_means:
                d_score += weight * feature_means[feature]
        scores['D'] = _clip01(d_score)
        
        # Influência (I)
        i_score = 0.0
        for feature, weight in self.weights['I'].items():
            if feature in feature_means:
                i_score += weight * feature_means[feature]
        scores['I'] = _clip01(i_score)
        
        # eStabilidade (S)
        s_score = 0.0
        for feature, weight in self.weights['S'].items():
            if feature in feature_means:
                s_score += weight * feature_means[feature]
        scores['S'] = _clip01(s_score)
        
        # Consciência (C)
        c_score = 0.0
        for feature, weight in self.weights['C'].items():
            if feature in feature_means:
                c_score += weight * feature_means[feature]
        scores['C'] = _clip01(c_score)
        
        return scores
    
    def _calculate_confidence(self, features: List[Dict[str, float]]) -> float:
        """
        Calcula confiança baseada em:
        1. Quantidade de dados (sample_size)
        2. Consistência dos dados (baixa variância)
        """
        n = len(features)
        
        if n < 10:
            return 0.0  # Muito poucos dados
        
        # Calcular variância das features principais
        key_features = ['talk_ratio', 'empathy', 'interrupt_rate']
        variances = []
        
        for feature in key_features:
            values = [feat.get(feature, 0.0) for feat in features]
            if values:
                variance = float(np.var(values))
                variances.append(variance)
        
        if not variances:
            return 0.0
        
        # Média das variâncias
        avg_variance = np.mean(variances)
        
        # Confiança baseada em variância (menor variância = maior confiança)
        variance_confidence = _clip01(1.0 - avg_variance)
        
        # Confiança baseada em quantidade de dados
        # 200+ janelas = alta confiança
        size_confidence = _clip01(n / 200.0)
        
        # Confiança final é produto das duas
        confidence = variance_confidence * size_confidence
        
        return confidence
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Normaliza scores para que D+I+S+C = 1.
        Opcional - pode manter as escalas independentes.
        """
        total = sum(scores.values())
        if total > 0:
            return {k: v / total for k, v in scores.items()}
        return scores
    
    def get_disc_type(self, scores: Dict[str, float]) -> str:
        """
        Determina o tipo DISC predominante.
        
        Args:
            scores: Dict com scores D, I, S, C
            
        Returns:
            String com tipo predominante (ex: "DI", "SC", "D", etc.)
        """
        if not scores:
            return "BALANCED"
        
        # Encontrar scores mais altos
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Se há um score claramente dominante (>0.4)
        if sorted_scores[0][1] > 0.4:
            return sorted_scores[0][0]
        
        # Se há dois scores altos (>0.3)
        high_scores = [s for s in sorted_scores if s[1] > 0.3]
        if len(high_scores) >= 2:
            return ''.join([s[0] for s in high_scores[:2]])
        
        return "BALANCED"
    
    def get_strengths_weaknesses(self, scores: Dict[str, float]) -> Dict[str, List[str]]:
        """
        Identifica pontos fortes e fracos baseado nos scores.
        
        Args:
            scores: Dict com scores D, I, S, C
            
        Returns:
            Dict com 'strengths' e 'weaknesses'
        """
        if not scores:
            return {'strengths': [], 'weaknesses': []}
        
        strengths = []
        weaknesses = []
        
        # Limiares para determinar força/fraqueza
        strong_threshold = 0.6
        weak_threshold = 0.3
        
        for dimension, score in scores.items():
            if score >= strong_threshold:
                strengths.append(f"{dimension}_alta")
            elif score <= weak_threshold:
                weaknesses.append(f"{dimension}_baixa")
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        } 
"""
DISC Feature Extractor
=====================

Extrai features linguísticas e prosódicas das transcrições
para inferir o perfil DISC do vendedor.
"""

import json
import re
import math
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def _wpm(tokens: int, duration_s: float) -> float:
    """Calcula palavras por minuto."""
    if duration_s <= 0:
        return 0.0
    # clamp 60..240 wpm
    return min(240.0, max(60.0, 60.0 * tokens / duration_s))


def _response_latency(prev_client_end_ms: int, seller_start_ms: int) -> float:
    """Calcula latência de resposta do vendedor."""
    if prev_client_end_ms is None or seller_start_ms is None:
        return 1.0
    delta = max(0, (seller_start_ms - prev_client_end_ms) / 1000.0)
    return min(3.0, delta) / 3.0  # 0..1 (maior = mais paciente)


def _type_token_ratio(tokens: List[str]) -> float:
    """Calcula Type-Token Ratio (diversidade lexical)."""
    if not tokens:
        return 0.0
    return min(1.0, len(set(tokens)) / max(1, len(tokens)))


def _sentence_type_ratio(text: str) -> Tuple[float, float]:
    """Calcula proporção de tipos de frases (assertiva vs pergunta)."""
    t = (text or "").lower().strip()
    is_question = "?" in t or any(w in t for w in ["como", "quando", "onde", "por que", "quem", "qual"])
    is_assert = "!" in t or (not is_question and t.endswith("."))
    return (1.0 if is_assert else 0.0, 1.0 if is_question else 0.0)


class DiscFeatureExtractor:
    """Extrator de features DISC baseado em transcrições de vendas."""
    
    def __init__(self, dao):
        self.dao = dao
        
        # Dicionários para detecção de padrões
        self._imperatives = {
            'vamos', 'faça', 'façam', 'deixe', 'deixem', 'precisa', 'precisam',
            'deve', 'devem', 'tem que', 'têm que', 'obrigatório', 'essencial',
            'crucial', 'fundamental', 'vital', 'imprescindível'
        }
        
        self._hedges = {
            'talvez', 'acho que', 'penso que', 'creio que', 'acredito que',
            'poderia', 'poderia ser', 'seria', 'seria bom', 'pode ser',
            'possivelmente', 'provavelmente', 'eventualmente', 'quem sabe',
            'não sei', 'não tenho certeza', 'vou ver', 'vou analisar'
        }
        
        self._empathy_words = {
            'entendo', 'compreendo', 'percebo', 'vejo que', 'imagino',
            'sei como é', 'faz sentido', 'concordo', 'tem razão',
            'excelente', 'ótimo', 'maravilhoso', 'fantástico', 'perfeito',
            'obrigado', 'obrigada', 'agradeço', 'muito obrigado'
        }
        
        self._caution_words = {
            'cuidado', 'atenção', 'cautela', 'precaução', 'risco',
            'pode dar problema', 'pode dar errado', 'não tenho certeza',
            'vou verificar', 'vou confirmar', 'preciso analisar',
            'depende', 'vai depender', 'pode ser que', 'talvez'
        }
        
        self._structure_words = {
            'primeiro', 'segundo', 'terceiro', 'quarto', 'quinto',
            'passo 1', 'passo 2', 'passo 3', 'etapa 1', 'etapa 2',
            '1º', '2º', '3º', 'primeiramente', 'em seguida',
            'por fim', 'finalmente', 'conclusão', 'resumindo'
        }
    
    def from_calls(self, seller_id: str, since_days: int = 90) -> List[Dict[str, float]]:
        """Extrai features DISC de todas as calls do vendedor."""
        features = []
        
        try:
            # Buscar calls do vendedor
            calls = self.dao.get_calls_by_seller(seller_id, since_days)
            
            for call in calls:
                call_features = self._extract_from_call(call)
                features.extend(call_features)
                
            logger.info(f"Extraídas {len(features)} janelas de features para vendedor {seller_id}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair features para {seller_id}: {e}")
            
        return features
    
    def _extract_from_call(self, call: Dict[str, Any]) -> List[Dict[str, float]]:
        """Extrai features de uma call específica."""
        features = []
        
        try:
            # Buscar transcrições da call
            transcriptions = self.dao.get_transcriptions_by_call(call['id'])
            
            # Agrupar por janelas de 3 segundos
            windows = self._group_into_windows(transcriptions, window_size_ms=3000)
            
            for window in windows:
                window_features = self._extract_window_features(window)
                if window_features:
                    features.append(window_features)
                    
        except Exception as e:
            logger.error(f"Erro ao processar call {call.get('id')}: {e}")
            
        return features
    
    def _group_into_windows(self, transcriptions: List[Dict], window_size_ms: int = 3000) -> List[Dict]:
        """Agrupa transcrições em janelas de tempo."""
        if not transcriptions:
            return []
            
        windows = []
        current_window = {
            'start_ms': transcriptions[0]['ts_start_ms'],
            'end_ms': transcriptions[0]['ts_start_ms'] + window_size_ms,
            'transcriptions': []
        }
        
        for trans in transcriptions:
            if trans['ts_start_ms'] >= current_window['end_ms']:
                # Nova janela
                if current_window['transcriptions']:
                    windows.append(current_window)
                    
                current_window = {
                    'start_ms': trans['ts_start_ms'],
                    'end_ms': trans['ts_start_ms'] + window_size_ms,
                    'transcriptions': [trans]
                }
            else:
                # Mesma janela
                current_window['transcriptions'].append(trans)
        
        # Adicionar última janela
        if current_window['transcriptions']:
            windows.append(current_window)
            
        return windows
    
    def _extract_window_features(self, window: Dict) -> Optional[Dict[str, float]]:
        """Extrai features de uma janela de tempo."""
        if not window['transcriptions']:
            return None
            
        # Concatenar texto da janela
        seller_text = ""
        client_text = ""
        total_duration = 0
        
        for trans in window['transcriptions']:
            duration = trans['ts_end_ms'] - trans['ts_start_ms']
            total_duration += duration
            
            if trans['source'] == 'vendedor':
                seller_text += " " + trans['text']
            else:
                client_text += " " + trans['text']
        
        seller_text = seller_text.strip()
        client_text = client_text.strip()
        
        if not seller_text:
            return None
            
        # Calcular features básicas
        features = {
            'talk_ratio': self._calculate_talk_ratio(seller_text, client_text, total_duration),
            'imperatives': self._detect_imperatives(seller_text),
            'open_questions': self._detect_open_questions(seller_text),
            'closed_questions': self._detect_closed_questions(seller_text),
            'hedges': self._detect_hedges(seller_text),
            'empathy': self._detect_empathy(seller_text),
            'interrupt_rate': self._detect_interruptions(window['transcriptions']),
            'structure': self._detect_structure(seller_text),
            'risk_aversion': self._detect_risk_aversion(seller_text),
            'valence_var': self._get_valence_variability(window['transcriptions']),
            'turn_balance': self._calculate_turn_balance(seller_text, client_text)
        }
        
        # NOVAS FEATURES
        seller_tokens = seller_text.split()
        duration_s = total_duration / 1000.0
        
        features["wpm"] = _wpm(len(seller_tokens), duration_s)
        features["latency"] = self._calculate_response_latency(window['transcriptions'])
        features["ttr"] = _type_token_ratio(seller_tokens)
        assert_ratio, question_ratio = _sentence_type_ratio(seller_text)
        features["assert_ratio"] = assert_ratio
        features["question_ratio"] = question_ratio
        
        return features
    
    def _calculate_talk_ratio(self, seller_text: str, client_text: str, duration_ms: int) -> float:
        """Calcula proporção de fala do vendedor."""
        seller_words = len(seller_text.split())
        client_words = len(client_text.split())
        total_words = seller_words + client_words
        
        if total_words == 0:
            return 0.5  # Neutro se não há fala
            
        return seller_words / total_words
    
    def _detect_imperatives(self, text: str) -> float:
        """Detecta uso de imperativos e afirmações fortes."""
        words = text.lower().split()
        imperative_count = sum(1 for word in words if word in self._imperatives)
        
        # Normalizar pelo número de palavras
        return min(1.0, imperative_count / max(1, len(words)))
    
    def _detect_open_questions(self, text: str) -> float:
        """Detecta perguntas abertas (wh- questions)."""
        # Padrões de perguntas abertas
        open_patterns = [
            r'\b(como|quando|onde|por que|porque|quem|qual|quais|o que|que)\b',
            r'\b(explique|descreva|conte|fale sobre|me diga)\b'
        ]
        
        count = 0
        for pattern in open_patterns:
            count += len(re.findall(pattern, text.lower()))
            
        return min(1.0, count / max(1, len(text.split())))
    
    def _detect_closed_questions(self, text: str) -> float:
        """Detecta perguntas fechadas (sim/não)."""
        # Padrões de perguntas fechadas
        closed_patterns = [
            r'\b(é|está|tem|faz|gosta|precisa|quer|pode|vai|vem)\b.*\?',
            r'\b(concorda|entende|sabe|acha|pensa)\b.*\?'
        ]
        
        count = 0
        for pattern in closed_patterns:
            count += len(re.findall(pattern, text.lower()))
            
        return min(1.0, count / max(1, len(text.split())))
    
    def _detect_hedges(self, text: str) -> float:
        """Detecta uso de hedges (palavras de hesitação)."""
        words = text.lower().split()
        hedge_count = sum(1 for word in words if word in self._hedges)
        
        return min(1.0, hedge_count / max(1, len(words)))
    
    def _detect_empathy(self, text: str) -> float:
        """Detecta uso de palavras empáticas."""
        words = text.lower().split()
        empathy_count = sum(1 for word in words if word in self._empathy_words)
        
        return min(1.0, empathy_count / max(1, len(words)))
    
    def _detect_interruptions(self, transcriptions: List[Dict]) -> float:
        """Detecta interrupções baseado em sobreposição de tempo."""
        interruptions = 0
        total_transitions = max(1, len(transcriptions) - 1)
        
        for i in range(len(transcriptions) - 1):
            current = transcriptions[i]
            next_trans = transcriptions[i + 1]
            
            # Se há sobreposição significativa (>500ms)
            overlap = current['ts_end_ms'] - next_trans['ts_start_ms']
            if overlap > 500:
                interruptions += 1
                
        return interruptions / total_transitions
    
    def _detect_structure(self, text: str) -> float:
        """Detecta uso de estrutura e organização."""
        words = text.lower().split()
        structure_count = sum(1 for word in words if word in self._structure_words)
        
        # Bônus para números
        number_count = len(re.findall(r'\b\d+\b', text))
        
        return min(1.0, (structure_count + number_count * 0.5) / max(1, len(words)))
    
    def _detect_risk_aversion(self, text: str) -> float:
        """Detecta aversão a risco e cautela."""
        words = text.lower().split()
        caution_count = sum(1 for word in words if word in self._caution_words)
        
        return min(1.0, caution_count / max(1, len(words)))
    
    def _get_valence_variability(self, transcriptions: List[Dict]) -> float:
        """Calcula variabilidade de valência (se disponível)."""
        valences = []
        
        for trans in transcriptions:
            if 'valence' in trans:
                valences.append(trans['valence'])
        
        if len(valences) < 2:
            return 0.5  # Neutro se não há dados suficientes
            
        # Calcular variância normalizada
        mean_valence = sum(valences) / len(valences)
        variance = sum((v - mean_valence) ** 2 for v in valences) / len(valences)
        
        # Normalizar para 0..1
        return min(1.0, variance * 10)  # Fator de escala
    
    def _calculate_turn_balance(self, seller_text: str, client_text: str) -> float:
        """Calcula equilíbrio de turnos de fala."""
        seller_words = len(seller_text.split())
        client_words = len(client_text.split())
        total_words = seller_words + client_words
        
        if total_words == 0:
            return 0.5
            
        # Quanto mais próximo de 0.5, mais equilibrado
        balance = seller_words / total_words
        return 1.0 - abs(balance - 0.5) * 2  # 0.5 = perfeito equilíbrio
    
    def _calculate_response_latency(self, transcriptions: List[Dict]) -> float:
        """Calcula latência de resposta do vendedor."""
        if len(transcriptions) < 2:
            return 1.0  # Fallback: paciente
        
        # Buscar transições cliente -> vendedor
        latencies = []
        prev_client_end = None
        
        for trans in transcriptions:
            if trans['source'] == 'cliente':
                prev_client_end = trans['ts_end_ms']
            elif trans['source'] == 'vendedor' and prev_client_end is not None:
                latency = (trans['ts_start_ms'] - prev_client_end) / 1000.0
                if latency > 0:
                    latencies.append(latency)
        
        if not latencies:
            return 1.0
        
        # Média das latências, normalizada
        avg_latency = sum(latencies) / len(latencies)
        return min(3.0, avg_latency) / 3.0  # 0..1 (maior = mais paciente) 
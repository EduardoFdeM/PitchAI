"""
Text Analyzer - RF-3.1: Motor textual (NLP)
==========================================

Análise de sentimento e detecção de palavras-gatilho em texto.
"""

import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️ ONNX Runtime não disponível. Usando simulação.")

from .models import KeywordMatch, SentimentConfig


class TextAnalyzer:
    """RF-3.1: Motor textual (NLP)"""
    
    def __init__(self, config: SentimentConfig = None, model_manager=None):
        self.config = config or SentimentConfig()
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Modelo ONNX para sentimento
        self.sentiment_session = None
        self.tokenizer = None
        
        # Cache de análise
        self.sentiment_cache = {}
        self.keyword_cache = {}
        
        # Inicializar
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializar modelo de sentimento."""
        try:
            if not ONNX_AVAILABLE:
                self.logger.warning("ONNX não disponível, usando simulação")
                return
            
            # Tentar carregar via ModelManager
            if self.model_manager:
                self.sentiment_session = self.model_manager.get_session("distilbert_sentiment")
                if self.sentiment_session:
                    self.logger.info("✅ Modelo de sentimento carregado via ModelManager")
                    return
            
            # Fallback para carregamento manual
            model_path = "models/distilbert_sentiment.onnx"
            providers = ["QNNExecutionProvider", "CPUExecutionProvider"]
            
            try:
                self.sentiment_session = ort.InferenceSession(model_path, providers=providers)
                self.logger.info(f"✅ Modelo de sentimento carregado: {model_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar modelo: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização do modelo: {e}")
    
    def analyze_sentiment(self, text: str) -> float:
        """Inferir sentimento de texto (-1 a +1)."""
        if not text or not text.strip():
            return 0.0
        
        # Verificar cache
        cache_key = text.lower().strip()
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        try:
            if self.sentiment_session:
                # Usar modelo ONNX
                score = self._analyze_with_model(text)
            else:
                # Simulação baseada em palavras-chave
                score = self._simulate_sentiment(text)
            
            # Cache resultado
            self.sentiment_cache[cache_key] = score
            
            return score
            
        except Exception as e:
            self.logger.error(f"Erro na análise de sentimento: {e}")
            return 0.0
    
    def _analyze_with_model(self, text: str) -> float:
        """Análise usando AnythingLLM."""
        try:
            if not self.anythingllm_client:
                return self._simulate_sentiment(text)
            
            # Prompt para análise de sentimento
            system_prompt = (
                "Você é um especialista em análise de sentimento. "
                "Analise o texto e retorne APENAS um número entre -1 e +1, "
                "onde -1 = muito negativo, 0 = neutro, +1 = muito positivo. "
                "Exemplo: 0.8"
            )
            
            user_prompt = f"Texto: '{text}'\n\nSentimento (-1 a +1):"
            
            # Configurar payload
            payload = {
                "model": self.anythingllm_client.default_model,
                "temperature": 0.1,
                "stream": False,
                "max_tokens": 10,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            # Fazer requisição
            response = self.anythingllm_client._make_request(payload, stream=False)
            
            if response.status_code != 200:
                return self._simulate_sentiment(text)
            
            # Processar resposta
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Parsear número
            try:
                score = float(content)
                return np.clip(score, -1.0, 1.0)
            except ValueError:
                return self._simulate_sentiment(text)
                
        except Exception as e:
            self.logger.error(f"Erro na análise com AnythingLLM: {e}")
            return self._simulate_sentiment(text)
            # Por enquanto, usar simulação
            return self._simulate_sentiment(text)
            
        except Exception as e:
            self.logger.error(f"Erro no modelo ONNX: {e}")
            return self._simulate_sentiment(text)
    
    def _simulate_sentiment(self, text: str) -> float:
        """Simular análise de sentimento baseada em palavras-chave."""
        text_lower = text.lower()
        
        # Palavras positivas
        positive_words = [
            "bom", "ótimo", "excelente", "fantástico", "maravilhoso",
            "satisfeito", "feliz", "gosto", "interessante", "legal",
            "sim", "concordo", "perfeito", "ideal", "funciona"
        ]
        
        # Palavras negativas
        negative_words = [
            "ruim", "péssimo", "terrível", "horrível", "insatisfeito",
            "não gosto", "problema", "difícil", "caro", "complicado",
            "não", "discordo", "impossível", "inviável", "não funciona"
        ]
        
        # Contar palavras
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calcular score
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        pos_score = pos_count / total_words
        neg_score = neg_count / total_words
        
        # Normalizar para -1 a +1
        score = (pos_score - neg_score) * 2
        score = np.clip(score, -1.0, 1.0)
        
        return score
    
    def detect_keywords(self, text: str) -> List[KeywordMatch]:
        """Detectar palavras-gatilho."""
        if not text or not text.strip():
            return []
        
        # Verificar cache
        cache_key = text.lower().strip()
        if cache_key in self.keyword_cache:
            return self.keyword_cache[cache_key]
        
        matches = []
        text_lower = text.lower()
        
        for keyword in self.config.keywords:
            # Buscar keyword no texto
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            for match in re.finditer(pattern, text_lower):
                # Calcular confiança baseada no contexto
                confidence = self._calculate_keyword_confidence(text, match.start(), match.end())
                
                # Extrair contexto
                context_start = max(0, match.start() - 20)
                context_end = min(len(text), match.end() + 20)
                context = text[context_start:context_end]
                
                keyword_match = KeywordMatch(
                    keyword=keyword,
                    confidence=confidence,
                    position=match.start(),
                    context=context
                )
                matches.append(keyword_match)
        
        # Cache resultado
        self.keyword_cache[cache_key] = matches
        
        return matches
    
    def _calculate_keyword_confidence(self, text: str, start: int, end: int) -> float:
        """Calcular confiança de uma palavra-gatilho."""
        # Base: confiança alta para palavras-gatilho
        base_confidence = 0.8
        
        # Ajustar baseado no contexto
        context_start = max(0, start - 10)
        context_end = min(len(text), end + 10)
        context = text[context_start:context_end].lower()
        
        # Palavras que aumentam confiança
        boost_words = ["muito", "realmente", "definitivamente", "absolutamente"]
        for word in boost_words:
            if word in context:
                base_confidence += 0.1
        
        # Palavras que diminuem confiança
        reduce_words = ["não", "nem", "talvez", "possivelmente"]
        for word in reduce_words:
            if word in context:
                base_confidence -= 0.2
        
        return np.clip(base_confidence, 0.0, 1.0)
    
    def calculate_engagement(self, text: str) -> float:
        """Calcular engajamento textual."""
        if not text or not text.strip():
            return 0.0
        
        text_lower = text.lower()
        words = text.split()
        
        if len(words) == 0:
            return 0.0
        
        # Fatores de engajamento
        engagement_score = 0.0
        
        # 1. Tamanho da resposta (mais palavras = mais engajamento)
        word_count_score = min(len(words) / 20.0, 1.0)  # normalizar para 20 palavras
        engagement_score += word_count_score * 0.3
        
        # 2. Perguntas (indicam interesse)
        question_count = text.count('?')
        question_score = min(question_count / 3.0, 1.0)
        engagement_score += question_score * 0.2
        
        # 3. Palavras de interesse
        interest_words = ["interessante", "como", "quando", "onde", "por que", "explique"]
        interest_count = sum(1 for word in interest_words if word in text_lower)
        interest_score = min(interest_count / 2.0, 1.0)
        engagement_score += interest_score * 0.2
        
        # 4. Palavras de ação
        action_words = ["vamos", "fazer", "testar", "experimentar", "ver", "mostrar"]
        action_count = sum(1 for word in action_words if word in text_lower)
        action_score = min(action_count / 2.0, 1.0)
        engagement_score += action_score * 0.3
        
        return np.clip(engagement_score, 0.0, 1.0)
    
    def analyze_text_chunk(self, text: str, ts_start_ms: int, ts_end_ms: int) -> Dict[str, Any]:
        """Análise completa de um chunk de texto."""
        return {
            "sentiment": self.analyze_sentiment(text),
            "engagement": self.calculate_engagement(text),
            "keywords": self.detect_keywords(text),
            "ts_start_ms": ts_start_ms,
            "ts_end_ms": ts_end_ms,
            "text_length": len(text),
            "word_count": len(text.split())
        }
    
    def clear_cache(self):
        """Limpar cache de análise."""
        self.sentiment_cache.clear()
        self.keyword_cache.clear()
        self.logger.info("Cache de análise de texto limpo") 
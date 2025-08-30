"""
Keyword Detector - Detecção de palavras-gatilho
=============================================

Detecção de palavras-gatilho e geração de alertas contextuais.
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

from .models import SentimentEvent, KeywordMatch, SentimentConfig


class KeywordDetector:
    """Detector de palavras-gatilho e gerador de alertas."""
    
    def __init__(self, config: SentimentConfig = None):
        self.config = config or SentimentConfig()
        self.logger = logging.getLogger(__name__)
        
        # Histórico de keywords por call_id
        self.keyword_history = defaultdict(list)  # call_id -> [KeywordMatch]
        self.alert_history = defaultdict(list)    # call_id -> [SentimentEvent]
        
        # Contadores de frequência
        self.keyword_counts = defaultdict(Counter)  # call_id -> Counter
        
        # Controle de alertas já enviados
        self._sent_alerts = set()
        
        # Configurações de alerta
        self.alert_thresholds = {
            "preço": 2,      # alerta após 2 menções
            "contrato": 1,   # alerta após 1 menção
            "prazo": 1,      # alerta após 1 menção
            "ROI": 1,        # alerta após 1 menção
            "piloto": 1      # alerta após 1 menção
        }
        
        # Palavras que indicam sinais de compra
        self.buying_signals = [
            "comprar", "adquirir", "contratar", "fechar", "aceitar",
            "concordar", "aprovado", "interessado", "vamos fazer",
            "quando começar", "qual o prazo", "como funciona"
        ]
        
        # Palavras que indicam risco
        self.risk_signals = [
            "não", "nunca", "impossível", "muito caro", "não posso",
            "sem orçamento", "não tenho tempo", "não estou interessado",
            "vou pensar", "depois", "talvez"
        ]
    
    def process_keywords(self, call_id: str, keywords: List[KeywordMatch], 
                        ts_ms: int) -> List[SentimentEvent]:
        """Processar keywords e gerar eventos."""
        try:
            events = []
            
            # Adicionar ao histórico
            self.keyword_history[call_id].extend(keywords)
            
            # Atualizar contadores
            for keyword_match in keywords:
                self.keyword_counts[call_id][keyword_match.keyword] += 1
            
            # Verificar alertas por frequência
            frequency_events = self._check_frequency_alerts(call_id, ts_ms)
            events.extend(frequency_events)
            
            # Verificar sinais de compra
            buying_events = self._check_buying_signals(call_id, keywords, ts_ms)
            events.extend(buying_events)
            
            # Verificar sinais de risco
            risk_events = self._check_risk_signals(call_id, keywords, ts_ms)
            events.extend(risk_events)
            
            # Adicionar eventos ao histórico
            self.alert_history[call_id].extend(events)
            
            return events
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de keywords: {e}")
            return []
    
    def _check_frequency_alerts(self, call_id: str, ts_ms: int) -> List[SentimentEvent]:
        """Verificar alertas baseados em frequência."""
        events = []
        counter = self.keyword_counts[call_id]
        
        for keyword, threshold in self.alert_thresholds.items():
            count = counter[keyword]
            
            if count == threshold:
                # Verificar se já geramos alerta para esta keyword nesta chamada
                alert_key = f"{call_id}_{keyword}"
                if alert_key not in self._sent_alerts:
                    # Gerar alerta
                    event = SentimentEvent(
                        call_id=call_id,
                        ts_ms=ts_ms,
                        kind="alert",
                        label=keyword,
                        strength=min(count / 5.0, 1.0)  # normalizar strength
                    )
                    events.append(event)
                    
                    # Marcar que já enviamos este alerta
                    self._sent_alerts.add(alert_key)
                    
                    self.logger.info(f"🚨 Alerta: '{keyword}' mencionado {count}x na chamada {call_id}")
        
        return events
    
    def _check_buying_signals(self, call_id: str, keywords: List[KeywordMatch], 
                            ts_ms: int) -> List[SentimentEvent]:
        """Verificar sinais de compra."""
        events = []
        
        for keyword_match in keywords:
            keyword_lower = keyword_match.keyword.lower()
            
            # Verificar se é sinal de compra
            for signal in self.buying_signals:
                if signal in keyword_match.context.lower():
                    event = SentimentEvent(
                        call_id=call_id,
                        ts_ms=ts_ms,
                        kind="buying_signal",
                        label=signal,
                        strength=keyword_match.confidence
                    )
                    events.append(event)
                    
                    self.logger.info(f"💰 Sinal de compra: '{signal}' detectado na chamada {call_id}")
                    break
        
        return events
    
    def _check_risk_signals(self, call_id: str, keywords: List[KeywordMatch], 
                          ts_ms: int) -> List[SentimentEvent]:
        """Verificar sinais de risco."""
        events = []
        
        for keyword_match in keywords:
            keyword_lower = keyword_match.keyword.lower()
            
            # Verificar se é sinal de risco
            for signal in self.risk_signals:
                if signal in keyword_match.context.lower():
                    event = SentimentEvent(
                        call_id=call_id,
                        ts_ms=ts_ms,
                        kind="risk",
                        label=signal,
                        strength=keyword_match.confidence
                    )
                    events.append(event)
                    
                    self.logger.info(f"⚠️ Sinal de risco: '{signal}' detectado na chamada {call_id}")
                    break
        
        return events
    
    def get_keyword_summary(self, call_id: str) -> Dict[str, Any]:
        """Obter resumo de keywords para uma chamada."""
        try:
            counter = self.keyword_counts[call_id]
            history = self.keyword_history[call_id]
            alerts = self.alert_history[call_id]
            
            # Top keywords
            top_keywords = counter.most_common(5)
            
            # Estatísticas por tipo
            alert_count = len([e for e in alerts if e.kind == "alert"])
            buying_count = len([e for e in alerts if e.kind == "buying_signal"])
            risk_count = len([e for e in alerts if e.kind == "risk"])
            
            return {
                "total_keywords": len(history),
                "unique_keywords": len(counter),
                "top_keywords": top_keywords,
                "alerts": alert_count,
                "buying_signals": buying_count,
                "risk_signals": risk_count,
                "recent_alerts": alerts[-5:] if alerts else []
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            return {}
    
    def get_active_alerts(self, call_id: str) -> List[Dict[str, Any]]:
        """Obter alertas ativos para uma chamada."""
        try:
            alerts = []
            counter = self.keyword_counts[call_id]
            
            for keyword, threshold in self.alert_thresholds.items():
                count = counter[keyword]
                if count >= threshold:
                    alerts.append({
                        "keyword": keyword,
                        "count": count,
                        "threshold": threshold,
                        "status": "active"
                    })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Erro ao obter alertas ativos: {e}")
            return []
    
    def detect_keyword_patterns(self, call_id: str) -> List[Dict[str, Any]]:
        """Detectar padrões de keywords."""
        try:
            patterns = []
            history = self.keyword_history[call_id]
            
            if len(history) < 2:
                return patterns
            
            # Agrupar keywords por proximidade temporal
            time_groups = defaultdict(list)
            for keyword_match in history:
                # Agrupar por janelas de 30 segundos
                time_window = keyword_match.position // 30000
                time_groups[time_window].append(keyword_match)
            
            # Analisar grupos
            for time_window, keywords in time_groups.items():
                if len(keywords) >= 2:
                    # Múltiplas keywords em curto período
                    pattern = {
                        "type": "keyword_cluster",
                        "keywords": [k.keyword for k in keywords],
                        "time_window": time_window,
                        "intensity": len(keywords)
                    }
                    patterns.append(pattern)
            
            # Detectar sequências
            keyword_sequence = [k.keyword for k in history]
            for i in range(len(keyword_sequence) - 1):
                current = keyword_sequence[i]
                next_keyword = keyword_sequence[i + 1]
                
                # Sequências importantes
                important_sequences = [
                    ("preço", "contrato"),
                    ("ROI", "investimento"),
                    ("prazo", "início"),
                    ("piloto", "teste")
                ]
                
                for seq in important_sequences:
                    if current == seq[0] and next_keyword == seq[1]:
                        pattern = {
                            "type": "keyword_sequence",
                            "sequence": seq,
                            "position": i
                        }
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de padrões: {e}")
            return []
    
    def clear_call_data(self, call_id: str):
        """Limpar dados de uma chamada específica."""
        try:
            if call_id in self.keyword_history:
                del self.keyword_history[call_id]
            
            if call_id in self.alert_history:
                del self.alert_history[call_id]
            
            if call_id in self.keyword_counts:
                del self.keyword_counts[call_id]
            
            self.logger.info(f"Dados da chamada {call_id} limpos")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar dados: {e}")
    
    def update_alert_thresholds(self, new_thresholds: Dict[str, int]):
        """Atualizar thresholds de alerta."""
        try:
            self.alert_thresholds.update(new_thresholds)
            self.logger.info(f"Thresholds atualizados: {self.alert_thresholds}")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar thresholds: {e}")
    
    def get_detector_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do detector."""
        total_calls = len(self.keyword_history)
        total_keywords = sum(len(history) for history in self.keyword_history.values())
        total_alerts = sum(len(alerts) for alerts in self.alert_history.values())
        
        return {
            "total_calls": total_calls,
            "total_keywords": total_keywords,
            "total_alerts": total_alerts,
            "avg_keywords_per_call": total_keywords / max(total_calls, 1),
            "avg_alerts_per_call": total_alerts / max(total_calls, 1),
            "alert_thresholds": self.alert_thresholds.copy()
        } 
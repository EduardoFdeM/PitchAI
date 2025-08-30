"""
Sentiment Service - Serviço Principal de Análise de Sentimento
============================================================

Coordena análise de texto, prosódia e visão para inferir sentimento e engajamento.
"""

import logging
import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

from .models import (
    SentimentSample, SentimentEvent, DashboardData, 
    SentimentConfig, KeywordMatch
)
from .text_analyzer import TextAnalyzer
from .prosody_analyzer import ProsodyAnalyzer
from .vision_analyzer import VisionAnalyzer
from .fusion_engine import FusionEngine
from .keyword_detector import KeywordDetector


class SentimentService(QObject):
    """Serviço principal de análise de sentimento."""
    
    # Sinais para UI
    sentiment_updated = pyqtSignal(object)  # SentimentSample
    alert_triggered = pyqtSignal(object)    # SentimentEvent
    dashboard_updated = pyqtSignal(object)  # DashboardData
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config: SentimentConfig = None, model_manager=None):
        super().__init__()
        self.config = config or SentimentConfig()
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Componentes de análise
        self.text_analyzer = TextAnalyzer(self.config, model_manager)
        self.prosody_analyzer = ProsodyAnalyzer(self.config, model_manager)
        self.vision_analyzer = VisionAnalyzer(self.config, model_manager, opt_in=False)
        self.fusion_engine = FusionEngine(self.config)
        self.keyword_detector = KeywordDetector(self.config)
        
        # Estado do serviço
        self.is_running = False
        self.current_call_id = None
        
        # Buffers de dados
        self.text_buffer = deque(maxlen=10)  # últimos 10 chunks de texto
        self.audio_buffer = deque(maxlen=10)  # últimos 10 chunks de áudio
        self.vision_buffer = deque(maxlen=5)  # últimos 5 frames
        
        # Histórico para dashboard
        self.sentiment_history = deque(maxlen=90)  # últimos 90s
        self.engagement_history = deque(maxlen=90)
        self.alerts_history = deque(maxlen=20)
        
        # Métricas
        self.samples_processed = 0
        self.alerts_generated = 0
        self.last_update_time = 0
        
        # Timer para atualizações do dashboard
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self._update_dashboard)
        self.dashboard_timer.setInterval(1000)  # 1 segundo
    
    def initialize(self):
        """Inicializar serviço de sentimento."""
        try:
            self.logger.info("🧠 Inicializando serviço de sentimento...")
            
            # Inicializar componentes
            self.text_analyzer._initialize_model()
            self.prosody_analyzer._initialize_model()
            
            # Verificar status dos componentes
            vision_enabled = self.vision_analyzer.is_enabled()
            
            self.logger.info("✅ Serviço de sentimento inicializado")
            self.logger.info(f"   Text Analyzer: ✅")
            self.logger.info(f"   Prosody Analyzer: ✅")
            self.logger.info(f"   Vision Analyzer: {'✅' if vision_enabled else '❌ (opt-in)'}")
            self.logger.info(f"   Fusion Engine: ✅")
            self.logger.info(f"   Keyword Detector: ✅")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {e}")
            self.error_occurred.emit(str(e))
    
    def start(self, call_id: str, opts: Dict[str, Any] = None):
        """Iniciar análise de sentimento para uma chamada."""
        if self.is_running:
            return
        
        try:
            self.current_call_id = call_id
            self.is_running = True
            
            # Configurar análise visual se solicitado
            if opts and opts.get("video", False):
                self.vision_analyzer.enable_analysis(opt_in=True)
                self.logger.info("📹 Análise visual habilitada")
            
            # Limpar buffers e histórico
            self._clear_buffers()
            
            # Iniciar timer do dashboard
            self.dashboard_timer.start()
            
            self.logger.info(f"🎤 Análise de sentimento iniciada para call_id: {call_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar análise: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self, call_id: str):
        """Parar análise de sentimento."""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            # Parar timer do dashboard
            self.dashboard_timer.stop()
            
            # Processar buffers restantes
            self._process_remaining_buffers()
            
            # Limpar dados da chamada
            self.keyword_detector.clear_call_data(call_id)
            
            # Log de métricas
            self.logger.info(f"⏹️ Análise de sentimento parada para call_id: {call_id}")
            self.logger.info(f"   Amostras processadas: {self.samples_processed}")
            self.logger.info(f"   Alertas gerados: {self.alerts_generated}")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar análise: {e}")
    
    def process_text_chunk(self, text: str, ts_start_ms: int, ts_end_ms: int):
        """Processar chunk de texto da Feature 2."""
        if not self.is_running:
            return
        
        try:
            # Analisar texto
            text_analysis = self.text_analyzer.analyze_text_chunk(text, ts_start_ms, ts_end_ms)
            
            # Adicionar ao buffer
            self.text_buffer.append({
                "analysis": text_analysis,
                "ts_start": ts_start_ms,
                "ts_end": ts_end_ms
            })
            
            # Processar se temos dados suficientes
            self._process_analysis_window()
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de texto: {e}")
    
    def process_audio_chunk(self, audio: np.ndarray, ts_start_ms: int, ts_end_ms: int):
        """Processar chunk de áudio da Feature 1."""
        if not self.is_running:
            return
        
        try:
            # Analisar prosódia
            voice_analysis = self.prosody_analyzer.analyze_audio_chunk(audio, ts_start_ms, ts_end_ms)
            
            # Adicionar ao buffer
            self.audio_buffer.append({
                "analysis": voice_analysis,
                "ts_start": ts_start_ms,
                "ts_end": ts_end_ms
            })
            
            # Processar se temos dados suficientes
            self._process_analysis_window()
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de áudio: {e}")
    
    def process_video_frame(self, frame: np.ndarray, ts_ms: int):
        """Processar frame de vídeo (opcional)."""
        if not self.is_running or not self.vision_analyzer.is_enabled():
            return
        
        try:
            # Analisar frame
            vision_analysis = self.vision_analyzer.analyze_frame(frame, ts_ms)
            
            # Adicionar ao buffer
            self.vision_buffer.append({
                "analysis": vision_analysis,
                "ts": ts_ms
            })
            
        except Exception as e:
            self.logger.error(f"Erro no processamento de vídeo: {e}")
    
    def _process_analysis_window(self):
        """Processar janela de análise quando temos dados suficientes."""
        try:
            # Verificar se temos dados suficientes
            if len(self.text_buffer) == 0 or len(self.audio_buffer) == 0:
                return
            
            # Obter análises mais recentes
            text_data = self.text_buffer[-1]
            audio_data = self.audio_buffer[-1]
            
            # Verificar se os timestamps são compatíveis
            time_diff = abs(text_data["ts_end"] - audio_data["ts_end"])
            if time_diff > 5000:  # 5 segundos de diferença
                return
            
            # Obter análise visual se disponível
            vision_data = None
            if self.vision_analyzer.is_enabled() and len(self.vision_buffer) > 0:
                vision_data = self.vision_buffer[-1]
                
                # Verificar se o frame é recente
                frame_time_diff = abs(vision_data["ts"] - text_data["ts_end"])
                if frame_time_diff > 2000:  # 2 segundos de diferença
                    vision_data = None
            
            # Criar amostra de sentimento fundida
            sample = self.fusion_engine.create_sentiment_sample(
                call_id=self.current_call_id,
                ts_start_ms=min(text_data["ts_start"], audio_data["ts_start"]),
                ts_end_ms=max(text_data["ts_end"], audio_data["ts_end"]),
                text_analysis=text_data["analysis"],
                voice_analysis=audio_data["analysis"],
                vision_analysis=vision_data["analysis"] if vision_data else None
            )
            
            # Processar keywords e gerar alertas
            keywords = text_data["analysis"].get("keywords", [])
            events = self.keyword_detector.process_keywords(
                self.current_call_id, keywords, sample.ts_end_ms
            )
            
            # Atualizar histórico
            self._update_history(sample, events)
            
            # Emitir sinais
            self.sentiment_updated.emit(sample)
            
            for event in events:
                self.alert_triggered.emit(event)
                self.alerts_generated += 1
            
            # Atualizar métricas
            self.samples_processed += 1
            self.last_update_time = time.time()
            
        except Exception as e:
            self.logger.error(f"Erro no processamento da janela: {e}")
    
    def _update_history(self, sample: SentimentSample, events: List[SentimentEvent]):
        """Atualizar histórico para dashboard."""
        try:
            # Adicionar ao histórico de sentimento
            self.sentiment_history.append(sample.score_valence)
            self.engagement_history.append(sample.score_engagement)
            
            # Adicionar eventos ao histórico
            for event in events:
                self.alerts_history.append({
                    "kind": event.kind,
                    "label": event.label,
                    "strength": event.strength,
                    "ts": event.ts_ms
                })
            
        except Exception as e:
            self.logger.warning(f"Erro ao atualizar histórico: {e}")
    
    def _update_dashboard(self):
        """Atualizar dashboard com dados em tempo real."""
        try:
            if not self.is_running:
                return
            
            # Calcular métricas atuais
            current_sentiment = 0.0
            current_engagement = 0.0
            
            if self.sentiment_history:
                current_sentiment = self.sentiment_history[-1]
            if self.engagement_history:
                current_engagement = self.engagement_history[-1]
            
            # Converter para percentuais
            sentiment_percent = int((current_sentiment + 1) * 50)  # -1..+1 -> 0..100
            engagement_percent = int(current_engagement * 100)     # 0..1 -> 0..100
            
            # Contar sinais de compra
            buying_signals = len([a for a in self.alerts_history if a["kind"] == "buying_signal"])
            
            # Alertas ativos
            active_alerts = self.keyword_detector.get_active_alerts(self.current_call_id)
            
            # Criar dados do dashboard
            dashboard_data = DashboardData(
                sentiment_percent=sentiment_percent,
                engagement_percent=engagement_percent,
                buying_signals_count=buying_signals,
                alerts=active_alerts,
                sparkline_data=list(self.sentiment_history)[-30:]  # últimos 30 pontos
            )
            
            # Emitir atualização
            self.dashboard_updated.emit(dashboard_data)
            
        except Exception as e:
            self.logger.warning(f"Erro na atualização do dashboard: {e}")
    
    def _process_remaining_buffers(self):
        """Processar buffers restantes ao parar."""
        try:
            # Processar qualquer dado restante
            while len(self.text_buffer) > 0 and len(self.audio_buffer) > 0:
                self._process_analysis_window()
                
        except Exception as e:
            self.logger.warning(f"Erro no processamento de buffers restantes: {e}")
    
    def _clear_buffers(self):
        """Limpar buffers e histórico."""
        self.text_buffer.clear()
        self.audio_buffer.clear()
        self.vision_buffer.clear()
        self.sentiment_history.clear()
        self.engagement_history.clear()
        self.alerts_history.clear()
        
        self.samples_processed = 0
        self.alerts_generated = 0
        self.last_update_time = 0
        
        # Limpar histórico de fusão
        self.fusion_engine.clear_history()
    
    def get_sentiment_summary(self, call_id: str) -> Dict[str, Any]:
        """Obter resumo de sentimento para uma chamada."""
        try:
            # Resumo de keywords
            keyword_summary = self.keyword_detector.get_keyword_summary(call_id)
            
            # Estatísticas de sentimento
            if self.sentiment_history:
                avg_sentiment = sum(self.sentiment_history) / len(self.sentiment_history)
                max_sentiment = max(self.sentiment_history)
                min_sentiment = min(self.sentiment_history)
            else:
                avg_sentiment = max_sentiment = min_sentiment = 0.0
            
            if self.engagement_history:
                avg_engagement = sum(self.engagement_history) / len(self.engagement_history)
                max_engagement = max(self.engagement_history)
                min_engagement = min(self.engagement_history)
            else:
                avg_engagement = max_engagement = min_engagement = 0.0
            
            return {
                "call_id": call_id,
                "samples_processed": self.samples_processed,
                "alerts_generated": self.alerts_generated,
                "sentiment_stats": {
                    "average": avg_sentiment,
                    "maximum": max_sentiment,
                    "minimum": min_sentiment
                },
                "engagement_stats": {
                    "average": avg_engagement,
                    "maximum": max_engagement,
                    "minimum": min_engagement
                },
                "keyword_summary": keyword_summary,
                "fusion_stats": self.fusion_engine.get_fusion_stats(),
                "vision_enabled": self.vision_analyzer.is_enabled()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            return {}
    
    def update_config(self, new_config: Dict[str, Any]):
        """Atualizar configurações em tempo real."""
        try:
            # Atualizar pesos de fusão
            if "fusion_weights" in new_config:
                self.fusion_engine.update_weights(new_config["fusion_weights"])
            
            # Atualizar thresholds de alerta
            if "alert_thresholds" in new_config:
                self.keyword_detector.update_alert_thresholds(new_config["alert_thresholds"])
            
            # Atualizar análise visual
            if "enable_vision" in new_config:
                self.vision_analyzer.enable_analysis(opt_in=new_config["enable_vision"])
            
            self.logger.info("Configurações atualizadas")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar configurações: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do serviço."""
        return {
            "is_running": self.is_running,
            "current_call_id": self.current_call_id,
            "samples_processed": self.samples_processed,
            "alerts_generated": self.alerts_generated,
            "last_update_time": self.last_update_time,
            "buffer_sizes": {
                "text": len(self.text_buffer),
                "audio": len(self.audio_buffer),
                "vision": len(self.vision_buffer)
            },
            "history_sizes": {
                "sentiment": len(self.sentiment_history),
                "engagement": len(self.engagement_history),
                "alerts": len(self.alerts_history)
            },
            "component_stats": {
                "text_analyzer": self.text_analyzer.get_analyzer_stats() if hasattr(self.text_analyzer, 'get_analyzer_stats') else {},
                "keyword_detector": self.keyword_detector.get_detector_stats(),
                "fusion_engine": self.fusion_engine.get_fusion_stats(),
                "vision_analyzer": self.vision_analyzer.get_visual_metrics()
            }
        }
    
    def cleanup(self):
        """Limpar recursos do serviço."""
        try:
            self.logger.info("🔄 Limpando recursos de sentimento...")
            
            # Parar se estiver rodando
            if self.is_running:
                self.stop(self.current_call_id or "")
            
            # Limpar buffers
            self._clear_buffers()
            
            # Limpar componentes
            self.text_analyzer.clear_cache()
            self.fusion_engine.clear_history()
            self.vision_analyzer.cleanup()
            
            self.logger.info("✅ Recursos de sentimento limpos")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}") 
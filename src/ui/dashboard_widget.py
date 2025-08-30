"""
Dashboard Widget - Métricas em Tempo Real
=========================================

Exibe métricas de performance e sentimento em tempo real.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QProgressBar, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont
import random


class DashboardWidget(QWidget):
    """Widget de dashboard com métricas em tempo real."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setMaximumHeight(120)
        
        # Valores atuais das métricas
        self.current_metrics = {
            'sentiment': 'Positivo',
            'sentiment_score': 72,
            'confidence': 87,
            'objections': 2,
            'duration': '00:00',
            'npu_models': 5
        }
        
        self._setup_ui()
        
        # Timer para atualizar métricas dinamicamente
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        self.duration_seconds = 0
    
    def _setup_ui(self):
        """Configurar interface do dashboard."""
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        
        # ===== SENTIMENTO =====
        self.sentiment_frame = self._create_metric_frame(
            "😊 Sentimento", self.current_metrics['sentiment'], "CLIENTE", "#A3BE8C"
        )
        layout.addWidget(self.sentiment_frame)
        
        # ===== CONFIDENCE =====
        self.confidence_frame = self._create_metric_frame(
            "🎯 Confidence", f"{self.current_metrics['confidence']}%", "SCORE", "#88C0D0"
        )
        layout.addWidget(self.confidence_frame)
        
        # ===== OBJEÇÕES =====
        self.objections_frame = self._create_metric_frame(
            "🛡️ Objeções", str(self.current_metrics['objections']), "DETECTADAS", "#EBCB8B"
        )
        layout.addWidget(self.objections_frame)
        
        # ===== TEMPO =====
        self.time_frame = self._create_metric_frame(
            "⏱️ Duração", self.current_metrics['duration'], "MINUTOS", "#D08770"
        )
        layout.addWidget(self.time_frame)
        
        # ===== NPU STATUS =====
        self.npu_frame = self._create_metric_frame(
            "🧠 NPU", str(self.current_metrics['npu_models']), "MODELOS", "#A3BE8C"
        )
        layout.addWidget(self.npu_frame)
    
    def _create_metric_frame(self, title: str, value: str, 
                           subtitle: str, color: str) -> QFrame:
        """Criar frame para uma métrica."""
        frame = QFrame()
        frame.setObjectName("metricFrame")
        frame.setStyleSheet(f"""
            QFrame#metricFrame {{
                background: rgba(59, 66, 82, 0.9);
                border: 1px solid rgba(129, 161, 193, 0.4);
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        
        # Valor principal
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            color: #ECEFF4;
            font-size: 22px;
            font-weight: bold;
            margin: 5px 0px;
        """)
        
        # Subtítulo
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #D8DEE9; font-size: 10px;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)
        
        # Armazenar referências para atualização
        frame.value_label = value_label
        frame.title_label = title_label
        
        return frame
    
    def start_demo(self):
        """Iniciar modo demo com atualizações dinâmicas."""
        self.update_timer.start(1000)  # Atualizar a cada segundo
    
    def stop_demo(self):
        """Parar modo demo."""
        self.update_timer.stop()
        self.duration_seconds = 0
        self.current_metrics['duration'] = "00:00"
        self._update_metric_display()
    
    def _update_metrics(self):
        """Atualizar métricas com novos valores."""
        # Atualizar duração
        self.duration_seconds += 1
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        self.current_metrics['duration'] = f"{minutes:02d}:{seconds:02d}"
        
        # Atualizar confidence ocasionalmente
        if random.random() < 0.3:  # 30% chance
            self.current_metrics['confidence'] = random.randint(75, 95)
        
        # Atualizar objeções ocasionalmente
        if random.random() < 0.2:  # 20% chance
            self.current_metrics['objections'] = random.randint(0, 5)
        
        # Atualizar sentimento ocasionalmente
        if random.random() < 0.25:  # 25% chance
            sentiments = ['Positivo', 'Neutro', 'Preocupado', 'Muito Positivo']
            self.current_metrics['sentiment'] = random.choice(sentiments)
        
        self._update_metric_display()
    
    def _update_metric_display(self):
        """Atualizar displays das métricas."""
        # Atualizar confidence
        if hasattr(self, 'confidence_frame'):
            self.confidence_frame.value_label.setText(f"{self.current_metrics['confidence']}%")
        
        # Atualizar objeções
        if hasattr(self, 'objections_frame'):
            self.objections_frame.value_label.setText(str(self.current_metrics['objections']))
        
        # Atualizar duração
        if hasattr(self, 'time_frame'):
            self.time_frame.value_label.setText(self.current_metrics['duration'])
        
        # Atualizar sentimento
        if hasattr(self, 'sentiment_frame'):
            self.sentiment_frame.value_label.setText(self.current_metrics['sentiment'])
    
    @pyqtSlot(dict)
    def update_sentiment(self, metrics: dict):
        """Atualizar métricas de sentimento."""
        sentiment_score = metrics.get('sentiment', 0.5)
        confidence = metrics.get('confidence', 0.8)
        
        # Determinar sentimento baseado no score
        if sentiment_score > 0.7:
            sentiment_text = "Muito Positivo"
        elif sentiment_score > 0.4:
            sentiment_text = "Positivo"
        elif sentiment_score > 0.2:
            sentiment_text = "Neutro"
        else:
            sentiment_text = "Preocupado"
        
        self.current_metrics['sentiment'] = sentiment_text
        self.current_metrics['confidence'] = int(confidence * 100)
        self._update_metric_display()
    
    @pyqtSlot(int)
    def update_objections_count(self, count: int):
        """Atualizar contador de objeções."""
        self.current_metrics['objections'] = count
        self._update_metric_display()

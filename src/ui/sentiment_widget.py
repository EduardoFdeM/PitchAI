"""
Sentiment Widget - Dashboard de Sentimento
========================================

Widget PyQt6 para exibir métricas de sentimento em tempo real.
"""

import logging
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QListWidget, QListWidgetItem,
    QFrame, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from ai.sentiment.models import DashboardData, SentimentEvent


class SentimentWidget(QWidget):
    """Widget do dashboard de sentimento."""
    
    # Sinais
    vision_toggled = pyqtSignal(bool)  # Análise visual habilitada/desabilitada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Estado
        self.current_sentiment = 0
        self.current_engagement = 0
        self.buying_signals_count = 0
        self.alerts = []
        
        # Timer para atualizações
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # Atualizar a cada 1 segundo
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar interface."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title = QLabel("📊 Análise de Sentimento")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Métricas principais
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        metrics_layout = QVBoxLayout(metrics_frame)
        
        # Sentimento
        sentiment_layout = QHBoxLayout()
        sentiment_label = QLabel("😊 Sentimento:")
        sentiment_label.setFont(QFont("Segoe UI", 10))
        self.sentiment_value = QLabel("0%")
        self.sentiment_value.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.sentiment_bar = QProgressBar()
        self.sentiment_bar.setRange(0, 100)
        self.sentiment_bar.setFormat("")
        
        sentiment_layout.addWidget(sentiment_label)
        sentiment_layout.addWidget(self.sentiment_value)
        sentiment_layout.addWidget(self.sentiment_bar)
        metrics_layout.addLayout(sentiment_layout)
        
        # Engajamento
        engagement_layout = QHBoxLayout()
        engagement_label = QLabel("🎯 Engajamento:")
        engagement_label.setFont(QFont("Segoe UI", 10))
        self.engagement_value = QLabel("0%")
        self.engagement_value.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.engagement_bar = QProgressBar()
        self.engagement_bar.setRange(0, 100)
        self.engagement_bar.setFormat("")
        
        engagement_layout.addWidget(engagement_label)
        engagement_layout.addWidget(self.engagement_value)
        engagement_layout.addWidget(self.engagement_bar)
        metrics_layout.addLayout(engagement_layout)
        
        # Sinais de compra
        signals_layout = QHBoxLayout()
        signals_label = QLabel("⚡ Sinais de compra:")
        signals_label.setFont(QFont("Segoe UI", 10))
        self.signals_value = QLabel("0")
        self.signals_value.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.signals_value.setStyleSheet("color: #28a745;")
        
        signals_layout.addWidget(signals_label)
        signals_layout.addWidget(self.signals_value)
        signals_layout.addStretch()
        metrics_layout.addLayout(signals_layout)
        
        layout.addWidget(metrics_frame)
        
        # Configurações
        config_frame = QFrame()
        config_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        config_layout = QVBoxLayout(config_frame)
        
        config_title = QLabel("⚙️ Configurações")
        config_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        config_layout.addWidget(config_title)
        
        # Checkbox para análise visual
        self.vision_checkbox = QCheckBox("📹 Análise facial (opt-in)")
        self.vision_checkbox.setFont(QFont("Segoe UI", 9))
        self.vision_checkbox.toggled.connect(self._on_vision_toggled)
        config_layout.addWidget(self.vision_checkbox)
        
        # Botão para limpar dados
        clear_button = QPushButton("🗑️ Limpar dados")
        clear_button.setFont(QFont("Segoe UI", 9))
        clear_button.clicked.connect(self._clear_data)
        config_layout.addWidget(clear_button)
        
        layout.addWidget(config_frame)
        
        # Alertas
        alerts_frame = QFrame()
        alerts_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        alerts_layout = QVBoxLayout(alerts_frame)
        
        alerts_title = QLabel("🚨 Alertas")
        alerts_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        alerts_layout.addWidget(alerts_title)
        
        self.alerts_list = QListWidget()
        self.alerts_list.setMaximumHeight(120)
        self.alerts_list.setFont(QFont("Segoe UI", 9))
        alerts_layout.addWidget(self.alerts_list)
        
        layout.addWidget(alerts_frame)
        
        self.setLayout(layout)
        self._apply_styles()
    
    def _apply_styles(self):
        """Aplicar estilos CSS."""
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
            
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                background-color: #e9ecef;
            }
            
            QProgressBar::chunk {
                border-radius: 3px;
            }
            
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
    
    def update_dashboard(self, data: DashboardData):
        """Atualizar dashboard com novos dados."""
        try:
            self.current_sentiment = data.sentiment_percent
            self.current_engagement = data.engagement_percent
            self.buying_signals_count = data.buying_signals_count
            self.alerts = data.alerts
            
            self._update_display()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar dashboard: {e}")
    
    def add_alert(self, event: SentimentEvent):
        """Adicionar novo alerta."""
        try:
            # Criar item da lista
            alert_text = f"{self._get_alert_icon(event.kind)} {event.label}"
            if event.strength > 0:
                alert_text += f" (força: {event.strength:.1f})"
            
            item = QListWidgetItem(alert_text)
            
            # Aplicar cor baseada no tipo
            color = self._get_alert_color(event.kind)
            item.setForeground(color)
            
            # Adicionar ao topo da lista
            self.alerts_list.insertItem(0, item)
            
            # Manter apenas os últimos 10 alertas
            while self.alerts_list.count() > 10:
                self.alerts_list.takeItem(self.alerts_list.count() - 1)
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar alerta: {e}")
    
    def _get_alert_icon(self, kind: str) -> str:
        """Obter ícone para tipo de alerta."""
        icons = {
            "alert": "🚨",
            "buying_signal": "💰",
            "risk": "⚠️",
            "keyword": "🔍"
        }
        return icons.get(kind, "📌")
    
    def _get_alert_color(self, kind: str) -> QColor:
        """Obter cor para tipo de alerta."""
        colors = {
            "alert": QColor("#dc3545"),      # Vermelho
            "buying_signal": QColor("#28a745"),  # Verde
            "risk": QColor("#ffc107"),       # Amarelo
            "keyword": QColor("#17a2b8")     # Azul
        }
        return colors.get(kind, QColor("#6c757d"))
    
    def _update_display(self):
        """Atualizar exibição dos valores."""
        try:
            # Atualizar sentimento
            self.sentiment_value.setText(f"{self.current_sentiment}%")
            self.sentiment_bar.setValue(self.current_sentiment)
            
            # Aplicar cor baseada no valor
            if self.current_sentiment >= 70:
                color = "#28a745"  # Verde
            elif self.current_sentiment >= 40:
                color = "#ffc107"  # Amarelo
            else:
                color = "#dc3545"  # Vermelho
            
            self.sentiment_bar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            
            # Atualizar engajamento
            self.engagement_value.setText(f"{self.current_engagement}%")
            self.engagement_bar.setValue(self.current_engagement)
            
            # Aplicar cor baseada no valor
            if self.current_engagement >= 70:
                color = "#28a745"  # Verde
            elif self.current_engagement >= 40:
                color = "#ffc107"  # Amarelo
            else:
                color = "#dc3545"  # Vermelho
            
            self.engagement_bar.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            
            # Atualizar sinais de compra
            self.signals_value.setText(str(self.buying_signals_count))
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar display: {e}")
    
    def _on_vision_toggled(self, enabled: bool):
        """Callback para toggle de análise visual."""
        self.vision_toggled.emit(enabled)
        self.logger.info(f"Análise visual {'habilitada' if enabled else 'desabilitada'}")
    
    def _clear_data(self):
        """Limpar dados do dashboard."""
        self.current_sentiment = 0
        self.current_engagement = 0
        self.buying_signals_count = 0
        self.alerts = []
        self.alerts_list.clear()
        self._update_display()
        self.logger.info("Dados do dashboard limpos")
    
    def get_vision_enabled(self) -> bool:
        """Verificar se análise visual está habilitada."""
        return self.vision_checkbox.isChecked()
    
    def set_vision_enabled(self, enabled: bool):
        """Definir se análise visual está habilitada."""
        self.vision_checkbox.setChecked(enabled) 
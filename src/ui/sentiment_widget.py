"""
Sentiment Widget - Análise de Sentimento
========================================

Widget para exibir a análise de sentimento em tempo real.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SentimentWidget(QWidget):
    """Widget de análise de sentimento."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sentimentWidget")
        self._setup_ui()

    def _setup_ui(self):
        """Configurar a interface do widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título da Seção
        title_label = QLabel("😊 Sentimento")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ECEFF4;")
        
        # Valor do Sentimento (será atualizado dinamicamente)
        self.sentiment_value_label = QLabel("Positivo (78%)")
        sentiment_value_font = QFont()
        sentiment_value_font.setPointSize(24)
        sentiment_value_font.setWeight(QFont.Weight.Light)
        self.sentiment_value_label.setFont(sentiment_value_font)
        self.sentiment_value_label.setStyleSheet("color: #A3BE8C;") # Verde para positivo
        
        layout.addWidget(title_label)
        layout.addWidget(self.sentiment_value_label)
        
        self._apply_styles()

    def _apply_styles(self):
        """Aplicar estilos glassmorphism."""
        # Estilos movidos para glassmorphism.qss
        pass

    def update_sentiment(self, score, text):
        """Atualiza o display de sentimento."""
        self.sentiment_value_label.setText(f"{text} ({score:.0%})")
        # Mudar a cor com base no sentimento
        if score > 0.6:
            self.sentiment_value_label.setStyleSheet("color: #A3BE8C;") # Verde
        elif score > 0.4:
            self.sentiment_value_label.setStyleSheet("color: #EBCB8B;") # Amarelo
        else:
            self.sentiment_value_label.setStyleSheet("color: #BF616A;") # Vermelho

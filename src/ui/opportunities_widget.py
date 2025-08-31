"""
Opportunities Widget - Detecção de Oportunidades
================================================

Widget para exibir oportunidades detectadas pela IA.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

class OpportunitiesWidget(QWidget):
    """Widget de oportunidades."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("opportunitiesWidget")
        self._setup_ui()
        self.hide() # Inicia oculto

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("Oportunidades")
        font = QFont()
        font.setPointSize(14)
        font.setWeight(QFont.Weight.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #88C0D0;")
        
        self.content_label = QLabel("Nenhuma oportunidade detectada.")
        
        layout.addWidget(title_label)
        layout.addWidget(self.content_label)
        
        # Estilos movidos para glassmorphism.qss

    def set_opportunity(self, text):
        self.content_label.setText(text)
        self.show()

    def clear_opportunity(self):
        self.content_label.setText("Nenhuma oportunidade detectada.")
        self.hide()

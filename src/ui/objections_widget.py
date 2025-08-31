"""
Objections Widget - Detecção de Objeções
=========================================

Widget para exibir objeções detectadas pela IA.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

class ObjectionsWidget(QWidget):
    """Widget de objeções."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("objectionsWidget")
        self._setup_ui()
        self.hide() # Inicia oculto

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("🛡️ Objeções")
        font = QFont()
        font.setPointSize(14)
        font.setWeight(QFont.Weight.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #EBCB8B;")
        
        self.content_label = QLabel("Nenhuma objeção detectada.")
        
        layout.addWidget(title_label)
        layout.addWidget(self.content_label)
        
        # Estilos movidos para glassmorphism.qss

    def set_objection(self, text):
        self.content_label.setText(text)
        self.show()

    def clear_objection(self):
        self.content_label.setText("Nenhuma objeção detectada.")
        self.hide()

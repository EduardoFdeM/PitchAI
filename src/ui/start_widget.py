"""
Start Widget - Tela Inicial
===========================

Tela inicial da aplicação com o botão para iniciar a análise.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class StartWidget(QWidget):
    """Widget da tela inicial."""
    
    start_analysis_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar a interface do widget estilo glassmorphism card."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Card central
        card = QWidget()
        card.setObjectName("startCard")
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(40)
        card_layout.setContentsMargins(40, 60, 40, 60)
        
        # Título principal
        title_label = QLabel("Ready for your next meeting")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Light)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        # Botão de Iniciar Análise
        self.start_button = QPushButton("Start Analysis")
        self.start_button.setFixedSize(200, 50)
        self.start_button.clicked.connect(self.start_analysis_requested)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(card)
        
        self._apply_styles()

    def _apply_styles(self):
        """Aplicar estilos glassmorphism ao card e botão."""
        style = """
        QWidget#startCard {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.15), stop: 1 rgba(255, 255, 255, 0.08));
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(78, 205, 196, 0.8), stop: 1 rgba(85, 98, 112, 0.8));
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: rgba(255, 255, 255, 0.95);
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(78, 205, 196, 1.0), stop: 1 rgba(85, 98, 112, 1.0));
            border: 1px solid rgba(255, 255, 255, 0.4);
        }
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(58, 185, 176, 1.0), stop: 1 rgba(65, 78, 92, 1.0));
        }
        """
        self.setStyleSheet(style)

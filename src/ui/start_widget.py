"""
Start Widget - Tela de Splash
============================

Tela de splash minimalista com logo PitchAI.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class StartWidget(QWidget):
    """Widget da tela de splash."""
    
    start_analysis_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface de splash minimalista."""
        # Layout principal sem margens para efeito fullscreen
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal com fundo escuro
        self.splash_container = QWidget()
        self.splash_container.setObjectName("splashContainer")
        
        # Layout centralizado dentro do container
        splash_layout = QVBoxLayout(self.splash_container)
        splash_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_layout.setContentsMargins(0, 0, 0, 0)
        splash_layout.setSpacing(30)
        
        # Logo "P" em branco dentro de quadrado arredondado
        logo_container = QWidget()
        logo_container.setObjectName("logoContainer")
        logo_container.setFixedSize(80, 80)
        
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel("P")
        logo_font = QFont()
        logo_font.setPointSize(36)
        logo_font.setWeight(QFont.Weight.Bold)
        logo_label.setFont(logo_font)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("color: white;")
        
        logo_layout.addWidget(logo_label)
        
        # Texto "PitchAI" com "AI" em negrito
        title_label = QLabel("Pitch<span style='font-weight: bold;'>AI</span>")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Normal)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: white;")
        
        splash_layout.addWidget(logo_container, alignment=Qt.AlignmentFlag.AlignCenter)
        splash_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(self.splash_container)
        
        self._apply_splash_styles()
        self._start_splash_sequence()

    def _apply_splash_styles(self):
        """Aplicar estilos da tela de splash."""
        # Estilos movidos para glassmorphism.qss
        pass
    
    def _start_splash_sequence(self):
        """Iniciar sequência de splash."""
        # Aguardar 2 segundos e navegar para a próxima tela
        QTimer.singleShot(2000, self.start_analysis_requested.emit)
    
    def restart_splash(self):
        """Reiniciar sequência de splash."""
        self._start_splash_sequence()


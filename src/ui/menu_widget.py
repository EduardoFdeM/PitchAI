"""
Menu Widget - Menu Lateral
=========================

Widget de menu lateral com opções de navegação.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class MenuWidget(QWidget):
    """Widget de menu lateral."""
    
    # Sinais
    close_app_requested = pyqtSignal()
    history_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface do menu."""
        self.setObjectName("menuWidget")
        self.setFixedWidth(200)
        self.setFixedHeight(140)  # Altura para 3 itens com mais espaço
        print("🔧 Menu widget criado com sucesso")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Botão de histórico
        history_btn = QPushButton("☰ Histórico")
        history_btn.setObjectName("menuOptionBtn")
        history_btn.clicked.connect(self._open_history)
        layout.addWidget(history_btn)
        
        # Botão de configurações
        settings_btn = QPushButton("⚙️ Configurações")
        settings_btn.setObjectName("menuOptionBtn")
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)
        
        # Botão de fechar aplicação
        close_app_btn = QPushButton("↩ Fechar")
        close_app_btn.setObjectName("closeAppBtn")
        close_app_btn.clicked.connect(self._close_app)
        layout.addWidget(close_app_btn)
        
        self._apply_styles()
        
    def _open_history(self):
        """Abrir histórico de gravações."""
        self.hide()  # Fechar menu
        self.history_requested.emit()
    
    def _open_settings(self):
        """Abrir configurações."""
        self.hide()  # Fechar menu
        self.settings_requested.emit()
    
    def _close_app(self):
        """Fechar aplicação."""
        self.hide()  # Fechar menu primeiro
        self.close_app_requested.emit()
    
    def _apply_styles(self):
        """Aplicar estilos do menu."""
        # Estilos movidos para o CSS principal para evitar duplicação
        pass

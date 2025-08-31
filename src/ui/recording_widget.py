"""
Recording Widget - Tela Principal de Gravação
============================================

Tela principal onde o usuário grava suas reuniões com UI dinâmico.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class MenuWidget(QWidget):
    """Menu expansível no canto superior esquerdo."""
    
    # Sinais
    settings_requested = pyqtSignal()
    history_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.is_expanded = False
        
    def _setup_ui(self):
        """Configurar interface do menu."""
        self.setFixedSize(200, 160)
        self.setObjectName("expandableMenu")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Botão de configurações
        settings_btn = QPushButton("⚙️ Configurações")
        settings_btn.setObjectName("menuButton")
        settings_btn.clicked.connect(self.settings_requested)
        
        # Botão de histórico  
        history_btn = QPushButton("📚 Histórico")
        history_btn.setObjectName("menuButton")
        history_btn.clicked.connect(self.history_requested)
        
        # Botão de sair
        exit_btn = QPushButton("🚪 Sair")
        exit_btn.setObjectName("menuButton")
        exit_btn.clicked.connect(self.exit_requested)
        
        layout.addWidget(settings_btn)
        layout.addWidget(history_btn)
        layout.addWidget(exit_btn)
        
        self._apply_styles()
        self.hide()  # Iniciar oculto
    
    def _apply_styles(self):
        """Aplicar estilos liquid glass ao menu."""
        style = """
        QWidget#expandableMenu {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.15), 
                stop: 1 rgba(255, 255, 255, 0.08));
            border: 1px solid rgba(175, 177, 240, 0.3);
            border-radius: 15px;
            backdrop-filter: blur(20px);
        }
        
        QPushButton#menuButton {
            background: rgba(175, 177, 240, 0.1);
            border: 1px solid rgba(175, 177, 240, 0.2);
            border-radius: 8px;
            color: rgba(175, 177, 240, 0.9);
            font-size: 13px;
            font-weight: bold;
            padding: 10px 15px;
            text-align: left;
        }
        
        QPushButton#menuButton:hover {
            background: rgba(175, 177, 240, 0.2);
            border: 1px solid rgba(175, 177, 240, 0.4);
        }
        
        QPushButton#menuButton:pressed {
            background: rgba(73, 65, 206, 0.3);
        }
        """
        self.setStyleSheet(style)


class RecordingWidget(QWidget):
    """Widget principal de gravação com UI dinâmico."""
    
    # Sinais
    analysis_requested = pyqtSignal()
    back_to_start_requested = pyqtSignal()
    
    def __init__(self, config, app_instance, parent=None):
        super().__init__(parent)
        self.config = config
        self.app_instance = app_instance
        self.is_recording = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface de gravação dinâmica."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal liquid glass
        self.main_container = QWidget()
        self.main_container.setObjectName("recordingGlass")
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(0)
        
        # ===== HEADER COM MENU =====
        header_layout = QHBoxLayout()
        
        # Botão de menu (canto superior esquerdo)
        self.menu_button = QPushButton("☰")
        self.menu_button.setObjectName("menuToggle")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.clicked.connect(self._toggle_menu)
        
        header_layout.addWidget(self.menu_button)
        header_layout.addStretch()
        
        container_layout.addLayout(header_layout)
        
        # ===== ÁREA CENTRAL =====
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.addStretch()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(40)
        
        # Título Ready for your next meeting
        title_label = QLabel("Ready for your<br>next meeting")
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setWeight(QFont.Weight.Light)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: rgba(236, 239, 244, 0.9); line-height: 1.2;")
        
        # Botão principal com blur (Start Analysis)
        self.main_action_button = QPushButton("Start Analysis")
        self.main_action_button.setObjectName("blurActionButton")
        self.main_action_button.setFixedSize(280, 60)
        self.main_action_button.clicked.connect(self._start_analysis)
        
        center_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.main_action_button, alignment=Qt.AlignmentFlag.AlignCenter)
        center_layout.addStretch()
        
        container_layout.addWidget(center_widget, 1)
        container_layout.addStretch()
        
        main_layout.addWidget(self.main_container)
        
        # ===== MENU EXPANSÍVEL =====
        self.menu_widget = MenuWidget(self)
        self.menu_widget.move(40, 40)  # Posição próxima ao botão de menu
        
        # Conectar sinais do menu
        self.menu_widget.settings_requested.connect(self._open_settings)
        self.menu_widget.history_requested.connect(self._open_history)
        self.menu_widget.exit_requested.connect(self._exit_app)
        
        self._apply_styles()
    
    def _apply_styles(self):
        """Aplicar estilos liquid glass."""
        # Estilos movidos para glassmorphism.qss
        pass
    
    def _toggle_menu(self):
        """Alternar visibilidade do menu."""
        if self.menu_widget.isVisible():
            self.menu_widget.hide()
        else:
            self.menu_widget.show()
            self.menu_widget.raise_()  # Trazer para frente
    
    def _start_analysis(self):
        """Emite o sinal para ir para a tela de análise."""
        self.analysis_requested.emit()
    
    def _open_settings(self):
        """Abrir configurações."""
        self.menu_widget.hide()
        # Implementar navegação para configurações
    
    def _open_history(self):
        """Abrir histórico.""" 
        self.menu_widget.hide()
        # Implementar navegação para histórico
    
    def _exit_app(self):
        """Sair da aplicação."""
        import sys
        sys.exit()

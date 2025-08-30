"""
Start Widget - Tela Inicial
===========================

Tela inicial da aplicação com o botão para iniciar a análise.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class StartWidget(QWidget):
    """Widget da tela inicial."""
    
    start_analysis_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar a interface do widget com splash screen."""
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
        
        # Logo/ícone placeholder (pode adicionar uma imagem depois)
        logo_label = QLabel("🚀")
        logo_font = QFont()
        logo_font.setPointSize(48)
        logo_label.setFont(logo_font)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedSize(250, 8)
        self.progress_bar.setTextVisible(False)
        
        # Status label
        self.status_label = QLabel("Carregando modelos de IA...")
        status_font = QFont()
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: rgba(175, 177, 240, 0.8);")
        
        card_layout.addWidget(logo_label)
        card_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_label)
        
        main_layout.addWidget(card)
        
        self._apply_styles()
        self._start_loading_sequence()

    def _apply_styles(self):
        """Aplicar estilos glassmorphism com nova paleta de cores."""
        style = """
        QWidget#startCard {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(175, 177, 240, 0.15), stop: 1 rgba(73, 65, 206, 0.12));
            border-radius: 25px;
            border: 1px solid rgba(175, 177, 240, 0.3);
        }
        
        QProgressBar {
            background: rgba(21, 21, 21, 0.4);
            border: 1px solid rgba(175, 177, 240, 0.2);
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(175, 177, 240, 0.9), stop: 1 rgba(93, 31, 176, 0.9));
            border-radius: 3px;
        }
        """
        self.setStyleSheet(style)
    
    def _start_loading_sequence(self):
        """Iniciar sequência de loading automática."""
        self.progress = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_progress)
        self.loading_timer.start(50)  # Atualizar a cada 50ms
        
        # Status simulados da inicialização
        self.loading_stages = [
            (20, "Inicializando NPU..."),
            (40, "Carregando Whisper..."),
            (60, "Carregando modelo de sentimento..."),
            (80, "Configurando pipeline..."),
            (100, "Pronto!")
        ]
        self.current_stage = 0
    
    def _update_progress(self):
        """Atualizar progresso do loading."""
        self.progress += 1
        self.progress_bar.setValue(self.progress)
        
        # Atualizar status baseado no progresso
        if self.current_stage < len(self.loading_stages):
            target_progress, status_text = self.loading_stages[self.current_stage]
            if self.progress >= target_progress:
                self.status_label.setText(status_text)
                self.current_stage += 1
        
        # Finalizar loading e navegar para análise
        if self.progress >= 100:
            self.loading_timer.stop()
            QTimer.singleShot(800, self.start_analysis_requested.emit)  # Aguardar 800ms e navegar
    
    def restart_loading(self):
        """Reiniciar sequência de loading (útil para F5)."""
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
        self._start_loading_sequence()


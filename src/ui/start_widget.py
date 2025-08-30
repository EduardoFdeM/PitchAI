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
        
        # Título principal
        title_label = QLabel("PitchAI")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.95);")
        
        # Subtítulo
        subtitle_label = QLabel("Inicializando NPU...")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_font.setWeight(QFont.Weight.Light)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        
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
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_label)
        
        main_layout.addWidget(card)
        
        self._apply_styles()
        self._start_loading_sequence()

    def _apply_styles(self):
        """Aplicar estilos glassmorphism ao card e progress bar."""
        style = """
        QWidget#startCard {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.15), stop: 1 rgba(255, 255, 255, 0.08));
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        QProgressBar {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(78, 205, 196, 0.8), stop: 1 rgba(85, 98, 112, 0.8));
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


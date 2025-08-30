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
        """Configurar interface liquid glass elegante."""
        # Layout principal sem margens para efeito fullscreen
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal com efeito liquid glass
        self.glass_container = QWidget()
        self.glass_container.setObjectName("liquidGlass")
        
        # Layout centralizado dentro do glass
        glass_layout = QVBoxLayout(self.glass_container)
        glass_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glass_layout.setContentsMargins(0, 0, 0, 0)
        glass_layout.setSpacing(50)
        
        # Logo central elegante
        logo_label = QLabel("🚀")
        logo_font = QFont()
        logo_font.setPointSize(64)
        logo_label.setFont(logo_font)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("color: rgba(175, 177, 240, 0.9); margin: 30px;")
        
        # Progress container com efeito glass
        progress_container = QWidget()
        progress_container.setObjectName("progressGlass")
        progress_container.setFixedSize(320, 80)
        
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.setSpacing(20)
        progress_layout.setContentsMargins(30, 20, 30, 20)
        
        # Barra de progresso liquid
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        
        # Status label minimalista
        self.status_label = QLabel("Inicializando...")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setWeight(QFont.Weight.Light)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: rgba(175, 177, 240, 0.7);")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        glass_layout.addWidget(logo_label)
        glass_layout.addWidget(progress_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(self.glass_container)
        
        self._apply_liquid_glass_styles()
        self._start_loading_sequence()

    def _apply_liquid_glass_styles(self):
        """Aplicar estilos liquid glass elegantes tipo Apple."""
        style = """
        QWidget#liquidGlass {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(175, 177, 240, 0.08), 
                stop: 0.3 rgba(73, 65, 206, 0.12),
                stop: 0.7 rgba(93, 31, 176, 0.08),
                stop: 1 rgba(17, 24, 102, 0.15));
            border: 1px solid rgba(175, 177, 240, 0.15);
            border-radius: 0px;
        }
        
        QWidget#progressGlass {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.12), 
                stop: 1 rgba(255, 255, 255, 0.04));
            border: 1px solid rgba(175, 177, 240, 0.25);
            border-radius: 20px;
            backdrop-filter: blur(20px);
        }
        
        QProgressBar {
            background: rgba(21, 21, 21, 0.2);
            border: 1px solid rgba(175, 177, 240, 0.15);
            border-radius: 3px;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(175, 177, 240, 0.8), 
                stop: 0.5 rgba(73, 65, 206, 0.9),
                stop: 1 rgba(93, 31, 176, 0.8));
            border-radius: 2px;
            border: none;
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


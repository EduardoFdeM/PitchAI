"""
Analysis Widget - Tela Principal de Análise
===========================================

Widget que agrega todos os componentes da tela de análise em tempo real.
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from .dashboard_widget import DashboardWidget
from .transcription_widget import TranscriptionWidget
from .suggestions_widget import SuggestionsWidget
from .controls_widget import ControlsWidget

class AnalysisWidget(QWidget):
    """Widget principal da tela de análise."""
    
    def __init__(self, config, app_instance, parent=None):
        super().__init__(parent)
        self.config = config
        self.app_instance = app_instance
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configurar o layout da interface para formato vertical (9:16)."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Dashboard de métricas (mais compacto)
        self.dashboard_widget = DashboardWidget(self.config)
        self.dashboard_widget.setMaximumHeight(80)  # Reduzir altura
        main_layout.addWidget(self.dashboard_widget)
        
        # Conteúdo principal em layout vertical
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Transcrição (parte superior)
        self.transcription_widget = TranscriptionWidget(self.config)
        content_layout.addWidget(self.transcription_widget, 3)  # 60% do espaço
        
        # Sugestões (parte inferior)
        self.suggestions_widget = SuggestionsWidget(self.config)
        content_layout.addWidget(self.suggestions_widget, 2)  # 40% do espaço
        
        main_layout.addWidget(content_widget, 1)  # Expandir
        
        # Controles (compactos)
        self.controls_widget = ControlsWidget(self.config)
        self.controls_widget.setMaximumHeight(60)  # Reduzir altura
        main_layout.addWidget(self.controls_widget)

    def _connect_signals(self):
        """Conectar sinais da aplicação com a UI."""
        # Conectar sinais do app_instance para os widgets filhos
        self.app_instance.transcription_ready.connect(
            self.transcription_widget.add_transcription
        )
        self.app_instance.sentiment_updated.connect(
            self.dashboard_widget.update_sentiment
        )
        self.app_instance.objection_detected.connect(
            self.suggestions_widget.add_suggestion
        )
        
        # Conectar controles para o app_instance
        self.controls_widget.start_recording.connect(self._start_demo)
        self.controls_widget.stop_recording.connect(self._stop_demo)

    def _start_demo(self):
        """Iniciar a simulação de análise."""
        self.app_instance.start_recording()
        self.dashboard_widget.start_demo()
        # Aqui poderíamos emitir um sinal para a MainWindow atualizar o status geral
        
    def _stop_demo(self):
        """Parar a simulação de análise."""
        self.app_instance.stop_recording()
        self.dashboard_widget.stop_demo()
        # Aqui poderíamos emitir um sinal para a MainWindow atualizar o status geral

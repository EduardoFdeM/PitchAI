"""
Analysis Widget - Tela Principal de Análise
===========================================

Widget que agrega todos os componentes da tela de análise em tempo real.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from .transcription_widget import TranscriptionWidget
from .objections_widget import ObjectionsWidget
from .opportunities_widget import OpportunitiesWidget
from .notes_widget import NotesWidget
from .sentiment_widget import SentimentWidget

class AnalysisWidget(QWidget):
    """Widget principal da tela de análise."""
    
    def __init__(self, config, app_instance, parent=None):
        super().__init__(parent)
        self.config = config
        self.app_instance = app_instance
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configurar o layout dinâmico da tela de análise."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Ordem dos widgets: Sentimento, Objeções, Oportunidades, Anotações, Transcrição
        
        # 1. Sentimento (Fixo)
        self.sentiment_widget = SentimentWidget()
        main_layout.addWidget(self.sentiment_widget)
        
        # 2. Objeções (Dinâmico)
        self.objections_widget = ObjectionsWidget()
        main_layout.addWidget(self.objections_widget)
        
        # 3. Oportunidades (Dinâmico)
        self.opportunities_widget = OpportunitiesWidget()
        main_layout.addWidget(self.opportunities_widget)
        
        # 4. Anotações (Dinâmico, mas vamos deixar visível por padrão)
        self.notes_widget = NotesWidget()
        self.notes_widget.show() # Diferente dos outros, começa visível
        main_layout.addWidget(self.notes_widget)
        
        # 5. Transcrição (Fixo)
        self.transcription_widget = TranscriptionWidget(self.config)
        main_layout.addWidget(self.transcription_widget, 1) # Ocupa espaço extra
        
        main_layout.addStretch()

    def _connect_signals(self):
        """Conectar sinais da aplicação com a UI."""
        # Sinais fixos
        self.app_instance.transcription_ready.connect(
            self.transcription_widget.add_transcription
        )
        self.app_instance.sentiment_updated.connect(
            self.sentiment_widget.update_sentiment
        )
        
        # Sinais dinâmicos
        self.app_instance.objection_detected.connect(
            self.objections_widget.set_objection
        )
        self.app_instance.opportunity_detected.connect(
            self.opportunities_widget.set_opportunity
        )
        
        # Conexão de controle (ex: botão de parar gravação)
        # self.controls_widget.stop_recording.connect(self._stop_demo)

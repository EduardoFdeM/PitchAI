"""
Transcription Full Widget - Tela Completa de Transcrição
======================================================

Tela de transcrição em tela cheia para visualizar todo o conteúdo.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class TranscriptionFullWidget(QWidget):
    """Widget de transcrição em tela cheia."""
    
    # Sinais
    back_to_analysis_requested = pyqtSignal()
    
    def __init__(self, transcription_text="", parent=None):
        super().__init__(parent)
        self.transcription_text = transcription_text
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface da transcrição completa."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        
        # Botão voltar
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("backButton")
        back_button.setFixedSize(100, 40)
        back_button.clicked.connect(self.back_to_analysis_requested.emit)
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        
        # Título
        title_label = QLabel("📝 Transcrição Completa")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # ===== CONTEÚDO PRINCIPAL =====
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Área de transcrição
        self.transcription_area = QTextEdit()
        self.transcription_area.setObjectName("transcriptionArea")
        self.transcription_area.setReadOnly(True)
        self.transcription_area.setPlaceholderText("Transcrição aparecerá aqui...")
        
        # Definir texto inicial se fornecido
        if self.transcription_text:
            self.transcription_area.setText(self.transcription_text)
        
        content_layout.addWidget(self.transcription_area)
        
        main_layout.addWidget(content_frame)
        
        self._apply_styles()
    
    def update_transcription(self, text):
        """Atualizar texto da transcrição."""
        self.transcription_area.setText(text)
    
    def append_transcription(self, text):
        """Adicionar texto à transcrição."""
        current_text = self.transcription_area.toPlainText()
        if current_text:
            new_text = current_text + "\n\n" + text
        else:
            new_text = text
        self.transcription_area.setText(new_text)
        
        # Rolar para o final
        scrollbar = self.transcription_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _apply_styles(self):
        """Aplicar estilos da transcrição completa."""
        # Estilos movidos para glassmorphism.qss
        pass

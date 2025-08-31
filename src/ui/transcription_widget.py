"""
Transcription Widget - Transcrição em Tempo Real
================================================

Exibe a transcrição da conversa com identificação de falantes.
Integração com BD para armazenamento e geração de resumos pós-reunião.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QScrollArea, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSlot, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from typing import Optional, Dict, Any
import time
import logging


class TranscriptionWidget(QWidget):
    """Widget de transcrição em tempo real com integração BD."""

    # Sinais para integração
    transcription_saved = pyqtSignal(str)  # call_id
    summary_requested = pyqtSignal(str)    # call_id
    fullscreen_requested = pyqtSignal(str) # texto da transcrição

    def __init__(self, config, transcription_service=None, database_manager=None):
        super().__init__()
        self.config = config
        self.transcription_service = transcription_service
        self.database_manager = database_manager
        self.current_call_id: Optional[str] = None
        self.is_recording = False
        self.logger = logging.getLogger(__name__)

        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configurar interface de transcrição."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Transcrição em Tempo Real")
        header_label.setObjectName("sectionHeader")
        header_label.setStyleSheet("""
            QLabel#sectionHeader {
                color: #ECEFF4;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background: rgba(136, 192, 208, 0.2);
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Botão de salvar
        self.save_button = QPushButton("💾 Salvar")
        self.save_button.setObjectName("saveButton")
        self.save_button.setFixedSize(80, 30)
        self.save_button.clicked.connect(self._save_transcription)
        header_layout.addWidget(self.save_button)

        # Botão de resumo
        self.summary_button = QPushButton("📋 Resumo")
        self.summary_button.setObjectName("summaryButton")
        self.summary_button.setFixedSize(80, 30)
        self.summary_button.clicked.connect(self._generate_summary)
        header_layout.addWidget(self.summary_button)

        # Botão de expandir
        self.expand_button = QPushButton("⛶")
        self.expand_button.setObjectName("expandButton")
        self.expand_button.setFixedSize(30, 30)
        self.expand_button.setToolTip("Expandir para tela cheia")
        self.expand_button.clicked.connect(self._toggle_fullscreen)
        header_layout.addWidget(self.expand_button)

        layout.addLayout(header_layout)

        # Área de transcrição
        self.transcription_area = QTextEdit()
        self.transcription_area.setObjectName("transcriptionArea")
        self.transcription_area.setReadOnly(True)
        self.transcription_area.setStyleSheet("""
            QTextEdit#transcriptionArea {
                background: rgba(46, 52, 64, 0.8);
                border: 1px solid rgba(129, 161, 193, 0.3);
                border-radius: 8px;
                color: #ECEFF4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.4;
                padding: 15px;
            }
        """)
        layout.addWidget(self.transcription_area)
        
        # Adicionar conteúdo de exemplo
        self._add_example_content()
    
    def _add_example_content(self):
        """Adicionar conteúdo inicial vazio."""
        initial_content = """
<div style='color: #88C0D0; font-weight: bold; margin-bottom: 10px;'>
    Aguardando transcrição...
</div>
<div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
    A transcrição aparecerá aqui quando você começar a falar.
</div>
        """
        self.transcription_area.setHtml(initial_content)
    
    def load_real_transcription(self, call_id: str):
        """Carregar transcrição real do banco de dados."""
        try:
            from data.database import DatabaseManager
            
            # Conectar ao banco
            db_path = "data/pitchai.db"
            db = DatabaseManager(db_path)
            
            # Buscar transcrição real
            cursor = db.connection.execute("""
                SELECT speaker_id, text, timestamp 
                FROM transcription 
                WHERE call_id = ? 
                ORDER BY timestamp ASC
            """, (call_id,))
            
            transcriptions = cursor.fetchall()
            
            if transcriptions:
                content = ""
                for trans in transcriptions:
                    timestamp = trans['timestamp']
                    speaker = "Vendedor" if trans['speaker_id'] == "vendor" else "Cliente"
                    text = trans['text']
                    
                    content += f"""
<div style='color: #88C0D0; font-weight: bold; margin-bottom: 10px;'>
    [{timestamp}] {speaker}
</div>
<div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
    {text}
</div>
                    """
                
                self.transcription_area.setHtml(content)
            else:
                self._add_example_content()
                
        except Exception as e:
            print(f"❌ Erro ao carregar transcrição: {e}")
            self._add_example_content()
    
    @pyqtSlot(str, str)
    def add_transcription(self, text: str, speaker_id: str):
        """Adicionar nova transcrição."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Determinar cor e nome do falante
        if speaker_id == "vendor":
            color = "#88C0D0"
            name = "Vendedor"
        else:
            color = "#D08770" 
            name = "Cliente"
        
        # Criar HTML para nova transcrição
        html_content = f"""
        <div style='color: {color}; font-weight: bold; margin-bottom: 10px; margin-top: 15px;'>
            [{timestamp}] {name}
        </div>
        <div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
            {text}
        </div>
        """
        
        # Adicionar ao final
        cursor = self.transcription_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_content)
        
        # Scroll para o final
        self.transcription_area.ensureCursorVisible()
    
    def clear_transcription(self):
        """Limpar toda a transcrição."""
        self.transcription_area.clear()
    
    def export_transcription(self) -> str:
        """Exportar transcrição como texto."""
        return self.transcription_area.toPlainText()

    def add_transcription_chunk(self, html_content: str):
        """Adicionar chunk de HTML à transcrição."""
        cursor = self.transcription_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_content)
        self.transcription_area.ensureCursorVisible()

    def _connect_signals(self):
        """Conectar sinais do serviço de transcrição."""
        if self.transcription_service:
            self.transcription_service.transcript_chunk_ready.connect(self._on_transcript_chunk)
            self.transcription_service.transcription_started.connect(self._on_transcription_started)
            self.transcription_service.transcription_stopped.connect(self._on_transcription_stopped)
            self.transcription_service.error_occurred.connect(self._on_transcription_error)

    @pyqtSlot(object)
    def _on_transcript_chunk(self, chunk):
        """Receber chunk de transcrição."""
        try:
            # Determinar cor baseada na fonte
            if chunk.source == "mic":
                speaker = "👤 Vendedor"
                color = "#88C0D0"  # Azul claro
            else:
                speaker = "🎯 Cliente"
                color = "#A3BE8C"  # Verde claro

            # Formatar timestamp
            import time
            timestamp = time.strftime("%H:%M:%S", time.localtime(chunk.ts_start_ms / 1000))

            # Criar HTML para o chunk
            html_content = f"""
            <div style="margin: 5px 0;">
                <span style="color: {color}; font-weight: bold;">[{timestamp}] {speaker}:</span>
                <span style="color: #ECEFF4;"> {chunk.text}</span>
                <span style="color: #888888; font-size: 10px;"> (conf: {chunk.confidence:.2f})</span>
            </div>
            """

            # Adicionar à transcrição
            self.add_transcription_chunk(html_content)

        except Exception as e:
            print(f"Erro ao processar chunk de transcrição: {e}")

    @pyqtSlot(str)
    def _on_transcription_started(self, call_id):
        """Transcrição iniciada."""
        self.clear_transcription()
        start_html = f"""
        <div style="margin: 10px 0; padding: 10px; background: rgba(163, 190, 140, 0.2); border-radius: 5px;">
            <span style="color: #A3BE8C; font-weight: bold;">🎤 Transcrição iniciada - Call ID: {call_id}</span>
        </div>
        """
        self.add_transcription_chunk(start_html)

    @pyqtSlot(str)
    def _on_transcription_stopped(self, call_id):
        """Transcrição parada."""
        stop_html = f"""
        <div style="margin: 10px 0; padding: 10px; background: rgba(191, 97, 106, 0.2); border-radius: 5px;">
            <span style="color: #BF616A; font-weight: bold;">⏹️ Transcrição parada - Call ID: {call_id}</span>
        </div>
        """
        self.add_transcription_chunk(stop_html)

    @pyqtSlot(str)
    def _on_transcription_error(self, error_msg):
        """Erro na transcrição."""
        error_html = f"""
        <div style="margin: 10px 0; padding: 10px; background: rgba(235, 203, 139, 0.2); border-radius: 5px;">
            <span style="color: #EBCB8B; font-weight: bold;">⚠️ Erro na transcrição: {error_msg}</span>
        </div>
        """
        self.add_transcription_chunk(error_html)

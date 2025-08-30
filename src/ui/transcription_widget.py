"""
Transcription Widget - Transcrição em Tempo Real
================================================

Exibe a transcrição da conversa com identificação de falantes.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, 
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot, QDateTime
from PyQt6.QtGui import QFont, QTextCursor


class TranscriptionWidget(QWidget):
    """Widget de transcrição em tempo real."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar interface de transcrição."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("🎤 Transcrição em Tempo Real")
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
        layout.addWidget(header_label)
        
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
        """Adicionar conteúdo de exemplo."""
        example_content = """
<div style='color: #88C0D0; font-weight: bold; margin-bottom: 10px;'>
    [15:30:12] 🔵 Vendedor
</div>
<div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
    Olá! Obrigado por aceitar nossa reunião hoje. Como posso ajudá-lo com a solução de CRM?
</div>

<div style='color: #D08770; font-weight: bold; margin-bottom: 10px;'>
    [15:30:45] 🟠 Cliente
</div>
<div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
    Olá! Estamos avaliando opções, mas estou preocupado com o preço...
    <span style='color: #BF616A; font-weight: bold;'>[💡 OBJEÇÃO DETECTADA]</span>
</div>

<div style='color: #88C0D0; font-weight: bold; margin-bottom: 10px;'>
    [15:31:02] 🔵 Vendedor
</div>
<div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
    Entendo perfeitamente sua preocupação. Vamos falar sobre o ROI que nossos clientes têm visto...
</div>
        """
        self.transcription_area.setHtml(example_content)
    
    @pyqtSlot(str, str)
    def add_transcription(self, text: str, speaker_id: str):
        """Adicionar nova transcrição."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Determinar cor e ícone do falante
        if speaker_id == "vendor":
            color = "#88C0D0"
            icon = "🔵"
            name = "Vendedor"
        else:
            color = "#D08770" 
            icon = "🟠"
            name = "Cliente"
        
        # Criar HTML para nova transcrição
        html_content = f"""
        <div style='color: {color}; font-weight: bold; margin-bottom: 10px; margin-top: 15px;'>
            [{timestamp}] {icon} {name}
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

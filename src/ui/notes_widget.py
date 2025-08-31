"""
Notes Widget - Anotações do Usuário
====================================

Widget para o usuário fazer anotações durante a reunião.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtGui import QFont

class NotesWidget(QWidget):
    """Widget de anotações."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notesWidget")
        self._setup_ui()
        self.hide() # Inicia oculto por padrão

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("📝 Anotações")
        font = QFont()
        font.setPointSize(14)
        font.setWeight(QFont.Weight.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #D8DEE9;")
        
        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText("Digite suas anotações aqui...")
        
        layout.addWidget(title_label)
        layout.addWidget(self.notes_editor)
        
        # Estilos movidos para glassmorphism.qss
        
    def show_notes(self):
        self.show()

    def hide_notes(self):
        self.hide()

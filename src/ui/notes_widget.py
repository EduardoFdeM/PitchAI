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
        
        self.setStyleSheet("""
            QWidget#notesWidget {
                background: rgba(46, 52, 64, 0.7);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QTextEdit {
                background: rgba(30, 35, 45, 0.8);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #ECEFF4;
                padding: 10px;
            }
        """)
        
    def show_notes(self):
        self.show()

    def hide_notes(self):
        self.hide()

"""
Objection Widget - Cards de Objeções
===================================

Widget para exibir objeções detectadas pela IA.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class ObjectionCard(QWidget):
    """Card de objeção detectada."""
    
    clicked = pyqtSignal(dict)  # Emite dados da objeção
    
    def __init__(self, objection_data, parent=None):
        super().__init__(parent)
        self.objection_data = objection_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface do card."""
        self.setObjectName("objectionCard")
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Conteúdo da objeção
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        
        # Título
        title_label = QLabel("OBJEÇÕES")
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        
        # Texto da objeção
        text_label = QLabel(self.objection_data.get('text', 'Objeção identificada'))
        text_label.setStyleSheet("color: white; font-size: 16px;")
        text_label.setWordWrap(True)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(text_label)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
        self._apply_styles()
        
    def _apply_styles(self):
        """Aplicar estilos do card."""
        # Estilos movidos para glassmorphism.qss
        pass
    
    def mousePressEvent(self, event):
        """Detectar clique no card."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.objection_data)


class ObjectionWidget(QWidget):
    """Widget para gerenciar objeções."""
    
    objection_clicked = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.objections = []
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Container para os cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        layout.addWidget(self.cards_container)
        
        # Inicialmente oculto
        self.hide()
    
    def add_objection(self, objection_data):
        """Adicionar nova objeção."""
        card = ObjectionCard(objection_data)
        card.clicked.connect(self.objection_clicked.emit)
        
        self.objections.append(card)
        self.cards_layout.addWidget(card)
        
        # Mostrar widget se estava oculto
        if not self.isVisible():
            self.show()
    
    def clear_objections(self):
        """Limpar todas as objeções."""
        for card in self.objections:
            card.deleteLater()
        self.objections.clear()
        self.hide()

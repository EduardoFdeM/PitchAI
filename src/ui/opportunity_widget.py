"""
Opportunity Widget - Cards de Oportunidades
==========================================

Widget para exibir oportunidades detectadas pela IA.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class OpportunityCard(QWidget):
    """Card de oportunidade detectada."""
    
    clicked = pyqtSignal(dict)  # Emite dados da oportunidade
    
    def __init__(self, opportunity_data, parent=None):
        super().__init__(parent)
        self.opportunity_data = opportunity_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface do card."""
        self.setObjectName("opportunityCard")
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Ícone de oportunidade (campainha)
        icon_label = QLabel("🔔")
        icon_label.setStyleSheet("font-size: 20px;")
        
        # Conteúdo da oportunidade
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        
        # Título
        title_label = QLabel("OPORTUNIDADES")
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        
        # Texto da oportunidade
        text_label = QLabel(self.opportunity_data.get('text', 'Oportunidade identificada'))
        text_label.setStyleSheet("color: white; font-size: 16px;")
        text_label.setWordWrap(True)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(text_label)
        
        layout.addWidget(icon_label)
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
            self.clicked.emit(self.opportunity_data)


class OpportunityWidget(QWidget):
    """Widget para gerenciar oportunidades."""
    
    opportunity_clicked = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opportunities = []
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
    
    def add_opportunity(self, opportunity_data):
        """Adicionar nova oportunidade."""
        card = OpportunityCard(opportunity_data)
        card.clicked.connect(self.opportunity_clicked.emit)
        
        self.opportunities.append(card)
        self.cards_layout.addWidget(card)
        
        # Mostrar widget se estava oculto
        if not self.isVisible():
            self.show()
    
    def clear_opportunities(self):
        """Limpar todas as oportunidades."""
        for card in self.opportunities:
            card.deleteLater()
        self.opportunities.clear()
        self.hide()

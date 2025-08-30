"""
Suggestions Widget - Sugestões de IA
====================================

Exibe sugestões inteligentes baseadas em objeções detectadas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, 
    QFrame, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont


class SuggestionCard(QFrame):
    """Card individual para uma sugestão."""
    
    def __init__(self, suggestion_text: str, confidence: float, category: str):
        super().__init__()
        self.suggestion_text = suggestion_text
        self.confidence = confidence
        self.category = category
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar UI do card."""
        self.setObjectName("suggestionCard")
        self.setStyleSheet("""
            QFrame#suggestionCard {
                background: rgba(163, 190, 140, 0.15);
                border: 1px solid rgba(163, 190, 140, 0.3);
                border-radius: 8px;
                margin: 5px;
                padding: 15px;
            }
            QFrame#suggestionCard:hover {
                background: rgba(163, 190, 140, 0.25);
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header com categoria e confiança
        header_layout = QHBoxLayout()
        
        category_label = QLabel(f"💡 {self.category}")
        category_label.setStyleSheet("color: #A3BE8C; font-weight: bold; font-size: 12px;")
        
        confidence_label = QLabel(f"{self.confidence:.0%}")
        confidence_label.setStyleSheet("color: #88C0D0; font-weight: bold; font-size: 12px;")
        
        header_layout.addWidget(category_label)
        header_layout.addStretch()
        header_layout.addWidget(confidence_label)
        
        # Texto da sugestão
        suggestion_label = QLabel(self.suggestion_text)
        suggestion_label.setWordWrap(True)
        suggestion_label.setStyleSheet("""
            color: #ECEFF4;
            font-size: 14px;
            line-height: 1.4;
            margin: 10px 0px;
        """)
        
        # Botão de ação
        action_layout = QHBoxLayout()
        copy_btn = QPushButton("📋 Copiar")
        copy_btn.setObjectName("actionButton")
        copy_btn.setStyleSheet("""
            QPushButton#actionButton {
                background: rgba(136, 192, 208, 0.3);
                border: 1px solid rgba(136, 192, 208, 0.5);
                border-radius: 4px;
                color: #ECEFF4;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton#actionButton:hover {
                background: rgba(136, 192, 208, 0.5);
            }
        """)
        
        action_layout.addStretch()
        action_layout.addWidget(copy_btn)
        
        layout.addLayout(header_layout)
        layout.addWidget(suggestion_label)
        layout.addLayout(action_layout)


class SuggestionsWidget(QWidget):
    """Widget de sugestões inteligentes."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._setup_ui()
        self._add_example_suggestions()
    
    def _setup_ui(self):
        """Configurar interface de sugestões."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("💡 Sugestões Inteligentes")
        header_label.setObjectName("sectionHeader")
        header_label.setStyleSheet("""
            QLabel#sectionHeader {
                color: #ECEFF4;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background: rgba(163, 190, 140, 0.2);
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header_label)
        
        # Área de scroll para sugestões
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Container para as sugestões
        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.suggestions_container)
        layout.addWidget(scroll_area)
    
    def _add_example_suggestions(self):
        """Adicionar sugestões de exemplo."""
        example_suggestions = [
            {
                "text": "Entendo sua preocupação com o preço. Vamos falar sobre o ROI que nossos clientes têm visto nos primeiros 6 meses...",
                "confidence": 0.92,
                "category": "Objeção de Preço"
            },
            {
                "text": "Posso mostrar um case de sucesso de uma empresa similar à sua que reduziu custos em 30%...",
                "confidence": 0.87,
                "category": "Prova Social"
            },
            {
                "text": "Que tal fazer uma análise gratuita para mostrar o potencial de economia específico para sua empresa?",
                "confidence": 0.83,
                "category": "Próximo Passo"
            }
        ]
        
        for suggestion in example_suggestions:
            self.add_suggestion_card(
                suggestion["text"],
                suggestion["confidence"], 
                suggestion["category"]
            )
    
    @pyqtSlot(str, list)
    def add_suggestion(self, objection: str, suggestions: list):
        """Adicionar nova sugestão baseada em objeção detectada."""
        # Limpar sugestões antigas
        self.clear_suggestions()
        
        # Adicionar novas sugestões
        for suggestion in suggestions:
            self.add_suggestion_card(
                suggestion.get("text", ""),
                suggestion.get("confidence", 0.5),
                suggestion.get("category", "Geral")
            )
    
    def add_suggestion_card(self, text: str, confidence: float, category: str):
        """Adicionar um card de sugestão."""
        card = SuggestionCard(text, confidence, category)
        self.suggestions_layout.addWidget(card)
    
    def clear_suggestions(self):
        """Limpar todas as sugestões."""
        while self.suggestions_layout.count():
            child = self.suggestions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

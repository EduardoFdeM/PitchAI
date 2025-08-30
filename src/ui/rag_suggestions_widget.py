"""
RAG Suggestions Widget - Interface para Sugestões RAG
==================================================

Widget para exibir sugestões geradas pelo AnythingLLM em resposta
a objeções detectadas, com streaming de texto e informações sobre fontes.
"""

import time
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from ai.rag_service import RAGResult, Suggestion


class SuggestionCard(QFrame):
    """Card individual para uma sugestão."""
    
    copy_requested = pyqtSignal(str)  # texto da sugestão
    
    def __init__(self, suggestion: Suggestion, index: int):
        super().__init__()
        self.suggestion = suggestion
        self.index = index
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interface do card."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setMidLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(100, 150, 255, 0.3);
                border-radius: 12px;
                padding: 12px;
                margin: 4px;
            }
            QFrame:hover {
                border-color: rgba(100, 150, 255, 0.6);
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header com score e botão de copiar
        header_layout = QHBoxLayout()
        
        # Score
        score_label = QLabel(f"Relevância: {self.suggestion.score:.1%}")
        score_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        header_layout.addWidget(score_label)
        
        header_layout.addStretch()
        
        # Botão copiar
        copy_btn = QPushButton("📋 Copiar")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 150, 255, 0.2);
                border: 1px solid rgba(100, 150, 255, 0.4);
                border-radius: 6px;
                padding: 4px 8px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(100, 150, 255, 0.4);
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.suggestion.text))
        header_layout.addWidget(copy_btn)
        
        layout.addLayout(header_layout)
        
        # Texto da sugestão
        self.text_label = QLabel(self.suggestion.text)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                line-height: 1.4;
                padding: 8px;
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.text_label)
        
        # Fontes (se houver)
        if self.suggestion.sources:
            sources_layout = QVBoxLayout()
            sources_label = QLabel("📚 Fontes:")
            sources_label.setStyleSheet("color: #FFD700; font-size: 12px; font-weight: bold;")
            sources_layout.addWidget(sources_label)
            
            for source in self.suggestion.sources:
                source_text = f"• {source.get('title', source.get('id', 'Fonte'))}"
                source_label = QLabel(source_text)
                source_label.setStyleSheet("color: #B0C4DE; font-size: 11px; margin-left: 8px;")
                sources_layout.addWidget(source_label)
            
            layout.addLayout(sources_layout)
    
    def update_text(self, text: str):
        """Atualizar texto da sugestão (para streaming)."""
        self.text_label.setText(text)


class RAGSuggestionsWidget(QWidget):
    """Widget principal para exibir sugestões RAG."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_result: Optional[RAGResult] = None
        self.suggestion_cards: List[SuggestionCard] = []
        self.streaming_timer = QTimer()
        self.streaming_timer.timeout.connect(self._update_streaming)
        self.current_streaming_index = 0
        self.current_streaming_char = 0
    
    def setup_ui(self):
        """Configurar interface principal."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Título
        title_label = QLabel("🤖 Sugestões RAG")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        layout.addWidget(title_label)
        
        # Status do LLM
        self.status_label = QLabel("Status: Aguardando...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #B0C4DE;
                font-size: 12px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Barra de progresso para streaming
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(100, 150, 255, 0.3);
                border-radius: 8px;
                text-align: center;
                background-color: rgba(0, 0, 0, 0.2);
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #2196F3);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Área de scroll para as sugestões
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(100, 150, 255, 0.5);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(100, 150, 255, 0.7);
            }
        """)
        
        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.setSpacing(8)
        self.suggestions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.suggestions_container)
        layout.addWidget(scroll_area)
        
        # Informações de latência e modelo
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                color: #B0C4DE;
                font-size: 11px;
                padding: 4px;
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.info_label)
    
    def display_rag_result(self, result: RAGResult):
        """Exibir resultado do RAG."""
        self.current_result = result
        self.clear_suggestions()
        
        # Atualizar status
        self.status_label.setText("Status: Gerando sugestões...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                font-size: 12px;
                padding: 4px;
            }
        """)
        
        # Mostrar barra de progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(result.suggestions))
        self.progress_bar.setValue(0)
        
        # Criar cards vazios
        for i, suggestion in enumerate(result.suggestions):
            card = SuggestionCard(suggestion, i)
            card.copy_requested.connect(self._on_copy_requested)
            self.suggestion_cards.append(card)
            self.suggestions_layout.addWidget(card)
        
        # Iniciar streaming
        self.current_streaming_index = 0
        self.current_streaming_char = 0
        self.streaming_timer.start(50)  # 50ms entre caracteres
    
    def _update_streaming(self):
        """Atualizar streaming de texto."""
        if not self.current_result or not self.suggestion_cards:
            self.streaming_timer.stop()
            return
        
        if self.current_streaming_index >= len(self.suggestion_cards):
            # Streaming completo
            self.streaming_timer.stop()
            self._on_streaming_complete()
            return
        
        card = self.suggestion_cards[self.current_streaming_index]
        full_text = card.suggestion.text
        
        if self.current_streaming_char < len(full_text):
            # Adicionar próximo caractere
            current_text = full_text[:self.current_streaming_char + 1]
            card.update_text(current_text)
            self.current_streaming_char += 1
        else:
            # Próxima sugestão
            self.current_streaming_index += 1
            self.current_streaming_char = 0
            self.progress_bar.setValue(self.current_streaming_index)
    
    def _on_streaming_complete(self):
        """Callback quando streaming é completado."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Status: Sugestões prontas")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 12px;
                padding: 4px;
            }
        """)
        
        # Mostrar informações
        if self.current_result:
            model_info = self.current_result.model_info
            info_text = (
                f"⏱️ Latência: {self.current_result.latency_ms:.0f}ms | "
                f"🤖 Modelo: {model_info.get('model', 'N/A')} | "
                f"📊 Sugestões: {len(self.current_result.suggestions)}"
            )
            self.info_label.setText(info_text)
    
    def _on_copy_requested(self, text: str):
        """Callback quando usuário solicita copiar texto."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # Feedback visual
        self.status_label.setText("Status: Texto copiado!")
        QTimer.singleShot(2000, lambda: self.status_label.setText("Status: Sugestões prontas"))
    
    def clear_suggestions(self):
        """Limpar todas as sugestões."""
        for card in self.suggestion_cards:
            card.deleteLater()
        self.suggestion_cards.clear()
        
        # Limpar layout
        while self.suggestions_layout.count():
            child = self.suggestions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.progress_bar.setVisible(False)
        self.info_label.clear()
    
    def show_error(self, error_message: str):
        """Exibir erro."""
        self.clear_suggestions()
        self.status_label.setText(f"Status: Erro - {error_message}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-size: 12px;
                padding: 4px;
            }
        """)
    
    def set_llm_status(self, available: bool):
        """Atualizar status do LLM."""
        if available:
            self.status_label.setText("Status: LLM disponível")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 12px;
                    padding: 4px;
                }
            """)
        else:
            self.status_label.setText("Status: LLM não disponível (fallback)")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    font-size: 12px;
                    padding: 4px;
                }
            """) 
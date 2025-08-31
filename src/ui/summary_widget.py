"""
Summary Widget - Resumo da Reunião
====================================

Exibe o resumo gerado pela IA após o término da análise.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, 
    QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class SummaryWidget(QWidget):
    """Widget para exibir o resumo da reunião."""
    
    back_to_start_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Configurar a interface do widget."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Meeting Summary")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ECEFF4;")
        
        back_button = QPushButton("← Back")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_to_start_requested)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(back_button)
        
        main_layout.addLayout(header_layout)

        # Área de Scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("summaryScrollArea")
        
        container = QWidget()
        self.summary_layout = QVBoxLayout(container)
        self.summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(container)
        
        main_layout.addWidget(scroll_area)
        
        # Botões de Ação
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        export_pdf_button = QPushButton("📄 Export as PDF")
        export_pdf_button.setObjectName("actionButton")
        
        save_button = QPushButton("💾 Save to History")
        save_button.setObjectName("actionButton")
        
        action_layout.addWidget(export_pdf_button)
        action_layout.addWidget(save_button)
        
        main_layout.addLayout(action_layout)
        
        self._populate_with_example_data()
        self._apply_styles()

    def _populate_with_example_data(self):
        """Preencher com dados de exemplo."""
        # Action Items
        self.summary_layout.addWidget(self._create_section_header("Action Items"))
        action_items = [
            "Enviar proposta técnica (até 25/07)",
            "Agendar demo técnica com a equipe de TI",
            "Incluir case de sucesso da Empresa X na proposta",
        ]
        for item in action_items:
            self.summary_layout.addWidget(self._create_list_item(item, checked=True))
            
        # Key Topics
        self.summary_layout.addWidget(self._create_section_header("Key Topics"))
        key_topics = [
            "Preocupação principal: integração com sistema legado",
            "Budget aprovado: R$ 50-80k",
            "Timeline: implementação desejada para Q3",
            "Necessidade de suporte 24/7",
        ]
        for topic in key_topics:
            self.summary_layout.addWidget(self._create_list_item(topic, checked=False))
            
        self.summary_layout.addStretch()

    def _create_section_header(self, text: str) -> QLabel:
        """Cria um cabeçalho de seção."""
        label = QLabel(text)
        font = QFont()
        font.setPointSize(16)
        font.setWeight(QFont.Weight.Bold)
        label.setFont(font)
        label.setStyleSheet("color: #88C0D0; margin-top: 15px; margin-bottom: 5px;")
        return label

    def _create_list_item(self, text: str, checked: bool) -> QWidget:
        """Cria um item de lista (com ou sem check)."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        icon = "✅" if checked else "⚪"
        icon_label = QLabel(icon)
        
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #D8DEE9; font-size: 14px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label, 1)
        
        return widget

    def _apply_styles(self):
        """Aplicar estilos."""
        # Estilos movidos para glassmorphism.qss
        pass

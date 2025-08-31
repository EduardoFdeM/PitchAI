"""
Summary Widget - Resumo da Reunião
====================================

Exibe o resumo gerado pela IA após o término da análise.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, 
    QFrame, QHBoxLayout, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any

class SummaryWidget(QWidget):
    """Widget para exibir o resumo da reunião."""
    
    back_to_start_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_summary = None
        self._setup_ui()

    def _setup_ui(self):
        """Configurar a interface do widget."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Resumo da Reunião")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ECEFF4;")
        
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_to_start_requested)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(back_button)
        
        main_layout.addLayout(header_layout)

        # Área de Resumo
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: rgba(46, 52, 64, 0.8);
                border: 1px solid rgba(129, 161, 193, 0.3);
                border-radius: 8px;
                color: #ECEFF4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 15px;
            }
        """)
        main_layout.addWidget(self.summary_text)
        
        # Botões de Ação
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        export_pdf_button = QPushButton("Export as PDF")
        export_pdf_button.setObjectName("actionButton")
        
        save_button = QPushButton("Save to History")
        save_button.setObjectName("actionButton")
        
        action_layout.addWidget(export_pdf_button)
        action_layout.addWidget(save_button)
        
        main_layout.addLayout(action_layout)
        
        self._populate_with_example_data()
        self._apply_styles()

    def _populate_with_example_data(self):
        """Preencher com dados reais do banco de dados."""
        try:
            from data.database import DatabaseManager
            
            # Conectar ao banco
            db_path = "data/pitchai.db"
            db = DatabaseManager(db_path)
            
            # Buscar resumo real da chamada atual
            if hasattr(self, 'current_call_id') and self.current_call_id:
                cursor = db.connection.execute("""
                    SELECT summary, action_items, key_topics 
                    FROM call 
                    WHERE id = ?
                """, (self.current_call_id,))
                
                call_data = cursor.fetchone()
                
                if call_data and call_data['summary']:
                    # Action Items
                    self.summary_layout.addWidget(self._create_section_header("Action Items"))
                    if call_data['action_items']:
                        action_items = call_data['action_items'].split('|')
                        for item in action_items:
                            if item.strip():
                                self.summary_layout.addWidget(self._create_list_item(item.strip(), checked=True))
                    else:
                        self.summary_layout.addWidget(self._create_list_item("Nenhuma ação definida", checked=False))
                    
                    # Key Topics
                    self.summary_layout.addWidget(self._create_section_header("Key Topics"))
                    if call_data['key_topics']:
                        key_topics = call_data['key_topics'].split('|')
                        for topic in key_topics:
                            if topic.strip():
                                self.summary_layout.addWidget(self._create_list_item(topic.strip(), checked=False))
                    else:
                        self.summary_layout.addWidget(self._create_list_item("Nenhum tópico identificado", checked=False))
                else:
                    # Dados padrão se não houver resumo
                    self.summary_layout.addWidget(self._create_section_header("Action Items"))
                    self.summary_layout.addWidget(self._create_list_item("Aguardando análise da IA...", checked=False))
                    
                    self.summary_layout.addWidget(self._create_section_header("Key Topics"))
                    self.summary_layout.addWidget(self._create_list_item("Aguardando identificação de tópicos...", checked=False))
                    
        except Exception as e:
            print(f"❌ Erro ao carregar resumo: {e}")
            # Fallback para dados padrão
            self.summary_layout.addWidget(self._create_section_header("Action Items"))
            self.summary_layout.addWidget(self._create_list_item("Erro ao carregar dados", checked=False))
            
            self.summary_layout.addWidget(self._create_section_header("Key Topics"))
            self.summary_layout.addWidget(self._create_list_item("Erro ao carregar dados", checked=False))
            
        self.summary_layout.addStretch()

    def _create_section_header(self, text: str) -> QLabel:
        """Cria um cabeçalho de seção."""
        label = QLabel(text)
        font = QFont()
        font.setPointSize(16)
        font.setWeight(QFont.Weight.Bold)
        label.setFont(font)
        
        # Aplicar cor roxa para "Action Items" e "Key Topics", manter azul para outros
        if text in ["Action Items", "Key Topics"]:
            label.setStyleSheet("color: rgba(73, 65, 206, 0.8); margin-top: 15px; margin-bottom: 5px;")
        else:
            label.setStyleSheet("color: #88C0D0; margin-top: 15px; margin-bottom: 5px;")
        
        return label

    def _create_list_item(self, text: str, checked: bool) -> QWidget:
        """Cria um item de lista (com ou sem check)."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Remover emojis, usar apenas texto
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #D8DEE9; font-size: 14px;")
        
        layout.addWidget(text_label, 1)
        
        return widget

    def _apply_styles(self):
        """Aplicar estilos."""
        # Estilos movidos para glassmorphism.qss
        pass

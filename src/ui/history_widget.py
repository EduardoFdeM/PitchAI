"""
History Widget - Histórico de Gravações
=====================================

Widget para exibir histórico de gravações por data.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class HistoryItemCard(QWidget):
    """Card de item do histórico."""
    
    clicked = pyqtSignal(str)  # Emite o ID da sessão
    
    def __init__(self, session_id: str, title: str, date: str, duration: str, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self._setup_ui(title, date, duration)
        
    def _setup_ui(self, title: str, date: str, duration: str):
        """Configurar interface do card."""
        self.setObjectName("historyItemCard")
        self.setFixedHeight(80)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Ícone de sessão
        icon_label = QLabel("🎙️")
        icon_label.setStyleSheet("font-size: 24px;")
        
        # Informações da sessão
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        
        date_duration_layout = QHBoxLayout()
        date_label = QLabel(date)
        date_label.setStyleSheet("color: #888888; font-size: 12px;")
        
        duration_label = QLabel(f"• {duration}")
        duration_label.setStyleSheet("color: #888888; font-size: 12px;")
        
        date_duration_layout.addWidget(date_label)
        date_duration_layout.addWidget(duration_label)
        date_duration_layout.addStretch()
        
        info_layout.addWidget(title_label)
        info_layout.addLayout(date_duration_layout)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Tornar clicável
        self.mousePressEvent = lambda event: self.clicked.emit(self.session_id)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._apply_styles()
    
    def _apply_styles(self):
        """Aplicar estilos do card."""
        # Estilos movidos para glassmorphism.qss
        pass


class HistoryWidget(QWidget):
    """Widget do histórico de gravações."""
    
    # Sinais
    back_to_dashboard_requested = pyqtSignal()
    history_item_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_sample_history()
        
    def _setup_ui(self):
        """Configurar interface do histórico."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        
        # Botão voltar
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("backButton")
        back_button.setFixedSize(100, 40)
        back_button.clicked.connect(lambda: self.back_to_dashboard_requested.emit())
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        
        # Título
        title_label = QLabel("📋 Histórico de Gravações")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # ===== LISTA DE GRAVAÇÕES =====
        # Área de scroll para histórico
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Estilo movido para glassmorphism.qss
        
        # Container para os cards
        self.history_container = QWidget()
        self.history_container_layout = QVBoxLayout(self.history_container)
        self.history_container_layout.setContentsMargins(0, 0, 0, 0)
        self.history_container_layout.setSpacing(15)
        self.history_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.history_scroll.setWidget(self.history_container)
        main_layout.addWidget(self.history_scroll)
        
        self._apply_styles()
    
    def _load_sample_history(self):
        """Carregar histórico de exemplo."""
        # Adicionar alguns itens de exemplo organizados por data
        sample_items = [
            ("sessao_001", "New Hack Hackathon", "15 Jan 2025", "45:32"),
            ("sessao_002", "Reunião com Cliente ABC", "15 Jan 2025", "23:15"),
            ("sessao_003", "Apresentação Produto XYZ", "14 Jan 2025", "1:12:45"),
            ("sessao_004", "Demo para Equipe de Vendas", "14 Jan 2025", "38:20"),
            ("sessao_005", "Call com Prospect Premium", "13 Jan 2025", "52:10"),
            ("sessao_006", "Reunião de Planejamento", "13 Jan 2025", "1:05:30"),
            ("sessao_007", "Apresentação para Investidores", "12 Jan 2025", "1:25:15"),
            ("sessao_008", "Treinamento de Vendas", "12 Jan 2025", "2:10:45"),
        ]
        
        # Agrupar por data
        grouped_items = {}
        for session_id, title, date, duration in sample_items:
            if date not in grouped_items:
                grouped_items[date] = []
            grouped_items[date].append((session_id, title, duration))
        
        # Adicionar grupos por data
        for date in sorted(grouped_items.keys(), reverse=True):
            # Título da data
            date_label = QLabel(date)
            date_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
            self.history_container_layout.addWidget(date_label)
            
            # Cards da data
            for session_id, title, duration in grouped_items[date]:
                card = HistoryItemCard(session_id, title, date, duration)
                card.clicked.connect(self.history_item_clicked.emit)
                self.history_container_layout.addWidget(card)
        
        # Adicionar spacer para empurrar cards para cima
        self.history_container_layout.addStretch()
    
    def _apply_styles(self):
        """Aplicar estilos do histórico."""
        # Estilos movidos para glassmorphism.qss
        pass

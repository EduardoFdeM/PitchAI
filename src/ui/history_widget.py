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
        
        # Remover ícone de sessão - deixar apenas texto
        
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
        self._load_real_history()
        
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
        title_label = QLabel("Histórico de Gravações")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
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
    
    def _load_real_history(self):
        """Carregar histórico real do banco de dados."""
        try:
            # Importar database manager
            from data.database import DatabaseManager
            import sqlite3
            from datetime import datetime
            
            # Conectar ao banco
            db_path = "data/pitchai.db"
            db = DatabaseManager(db_path)
            
            # Buscar chamadas reais
            cursor = db.connection.execute("""
                SELECT 
                    id,
                    start_time,
                    end_time,
                    duration_seconds,
                    status,
                    summary
                FROM call 
                ORDER BY start_time DESC
                LIMIT 50
            """)
            
            calls = cursor.fetchall()
            
            if not calls:
                # Se não há dados, mostrar mensagem
                no_data_label = QLabel("Nenhuma gravação encontrada")
                no_data_label.setStyleSheet("color: #888888; font-size: 16px; text-align: center; padding: 40px;")
                self.history_container_layout.addWidget(no_data_label)
                return
            
            # Agrupar por data
            grouped_calls = {}
            for call in calls:
                start_time = datetime.fromisoformat(call['start_time'])
                date_str = start_time.strftime("%d %b %Y")
                
                if date_str not in grouped_calls:
                    grouped_calls[date_str] = []
                
                # Calcular duração
                if call['duration_seconds']:
                    duration = call['duration_seconds']
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    seconds = duration % 60
                    
                    if hours > 0:
                        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "00:00"
                
                # Título baseado no status ou resumo
                if call['summary']:
                    title = call['summary'][:50] + "..." if len(call['summary']) > 50 else call['summary']
                else:
                    title = f"Chamada {call['status'].title()}"
                
                grouped_calls[date_str].append({
                    'id': call['id'],
                    'title': title,
                    'duration': duration_str,
                    'status': call['status']
                })
            
            # Adicionar grupos por data
            for date in sorted(grouped_calls.keys(), reverse=True):
                # Título da data
                date_label = QLabel(date)
                date_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
                self.history_container_layout.addWidget(date_label)
                
                # Cards da data
                for call_data in grouped_calls[date]:
                    card = HistoryItemCard(
                        call_data['id'], 
                        call_data['title'], 
                        date, 
                        call_data['duration']
                    )
                    card.clicked.connect(self.history_item_clicked.emit)
                    self.history_container_layout.addWidget(card)
            
            # Adicionar spacer para empurrar cards para cima
            self.history_container_layout.addStretch()
            
        except Exception as e:
            print(f"❌ Erro ao carregar histórico: {e}")
            # Fallback para mensagem de erro
            error_label = QLabel("Erro ao carregar histórico")
            error_label.setStyleSheet("color: #BF616A; font-size: 16px; text-align: center; padding: 40px;")
            self.history_container_layout.addWidget(error_label)
    
    def _apply_styles(self):
        """Aplicar estilos do histórico."""
        # Estilos movidos para glassmorphism.qss
        pass

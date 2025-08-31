"""
Dashboard Widget - Tela Principal
================================

Tela principal com saudação, botão Start e histórico de chamadas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class HistoryCard(QWidget):
    """Card de item do histórico."""
    
    clicked = pyqtSignal(str)  # Emite o ID da sessão
    
    def __init__(self, session_id: str, title: str, date: str, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self._setup_ui(title, date)
        
    def _setup_ui(self, title: str, date: str):
        """Configurar interface do card."""
        self.setObjectName("historyCard")
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Ícone de sessão
        icon_label = QLabel("🎙️")
        icon_label.setStyleSheet("font-size: 20px;")
        
        # Informações da sessão
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        date_label = QLabel(date)
        date_label.setStyleSheet("color: #888888; font-size: 12px;")
        
        info_layout.addWidget(title_label)
        info_layout.addWidget(date_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Tornar clicável
        self.mousePressEvent = lambda event: self.clicked.emit(self.session_id)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._apply_styles()
    
    def _apply_styles(self):
        """Aplicar estilos do card."""
        style = """
        QWidget#historyCard {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 12px;
        }
        
        QWidget#historyCard:hover {
            background: rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.25);
        }
        """
        self.setStyleSheet(style)


class DashboardWidget(QWidget):
    """Widget da tela principal do dashboard."""
    
    # Sinais
    start_analysis_requested = pyqtSignal()
    history_item_clicked = pyqtSignal(str)
    menu_requested = pyqtSignal()
    
    def __init__(self, config, pitch_app, parent=None):
        super().__init__(parent)
        self.config = config
        self.pitch_app = pitch_app
        self.app_instance = pitch_app  # Para compatibilidade
        self.menu_button = None  # Referência ao botão de menu
        self._setup_ui()
        self._load_dashboard_data()
    
    def _setup_ui(self):
        """Configurar interface do dashboard."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 30)
        
        # Botão de menu (ícone 3x3)
        self.menu_button = QPushButton("☰")
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.clicked.connect(lambda: self.menu_requested.emit())
        
        header_layout.addWidget(self.menu_button)
        header_layout.addStretch()
        
        # Botão Start
        start_button = QPushButton("▶ Start")
        start_button.setObjectName("startButton")
        start_button.setFixedSize(120, 40)
        start_button.clicked.connect(self.start_analysis_requested.emit)
        
        header_layout.addWidget(start_button)
        
        main_layout.addLayout(header_layout)
        
        # ===== SAUDAÇÃO E EMPRESA LADO A LADO =====
        greeting_empresa_layout = QHBoxLayout()
        greeting_empresa_layout.setContentsMargins(0, 50, 0, 30)
        greeting_empresa_layout.setSpacing(30)
        
        # Lado esquerdo: Saudação
        self.greeting_widget = QWidget()
        greeting_layout = QVBoxLayout(self.greeting_widget)
        greeting_layout.setContentsMargins(0, 0, 0, 0)
        greeting_layout.setSpacing(5)
        greeting_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        hello_label = QLabel("Olá,")
        hello_label.setStyleSheet("color: white; font-size: 16px; font-weight: normal;")
        hello_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        name_label = QLabel("Giovanna")
        name_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        greeting_layout.addWidget(hello_label)
        greeting_layout.addWidget(name_label)
        
        # Lado direito: Card da empresa
        empresa_card = QFrame()
        empresa_card.setObjectName("metricFrame")
        empresa_card.setFixedSize(300, 70)
        
        empresa_inner_layout = QHBoxLayout(empresa_card)
        empresa_inner_layout.setContentsMargins(20, 15, 20, 15)
        empresa_inner_layout.setSpacing(15)
        
        # Ícone da empresa (prédio)
        empresa_icon = QLabel("🏢")
        empresa_icon.setStyleSheet("font-size: 24px;")
        
        # Nome da empresa
        empresa_nome = QLabel("SOMOS Educação")
        empresa_nome.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        empresa_inner_layout.addWidget(empresa_icon)
        empresa_inner_layout.addWidget(empresa_nome)
        empresa_inner_layout.addStretch()
        
        # Adicionar widgets ao layout horizontal
        greeting_empresa_layout.addWidget(self.greeting_widget)
        greeting_empresa_layout.addWidget(empresa_card)
        greeting_empresa_layout.addStretch()
        
        main_layout.addLayout(greeting_empresa_layout)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        # Estilo movido para glassmorphism.qss
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # ===== SEÇÃO METAS =====
        metas_label = QLabel("Metas")
        metas_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(metas_label)
        
        # Cards de metas
        metas_layout = QHBoxLayout()
        metas_layout.setSpacing(20)
        
        # Card 1: Vendas concluídas
        vendas_card = QFrame()
        vendas_card.setObjectName("metricFrame")
        vendas_card.setFixedSize(280, 140)
        
        vendas_layout = QVBoxLayout(vendas_card)
        vendas_layout.setContentsMargins(20, 20, 20, 20)
        
        vendas_title = QLabel("Vendas concluídas")
        vendas_title.setStyleSheet("color: white; font-size: 14px; font-weight: normal;")
        
        vendas_value_layout = QHBoxLayout()
        vendas_number = QLabel("8")
        vendas_number.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        vendas_of = QLabel("de 24")
        vendas_of.setStyleSheet("color: white; font-size: 14px; font-weight: normal;")
        
        vendas_value_layout.addWidget(vendas_number)
        vendas_value_layout.addWidget(vendas_of)
        vendas_value_layout.addStretch()
        
        vendas_layout.addWidget(vendas_title)
        vendas_layout.addLayout(vendas_value_layout)
        vendas_layout.addStretch()
        
        # Card 2: Ranking
        ranking_card = QFrame()
        ranking_card.setObjectName("metricFrame")
        ranking_card.setFixedSize(280, 140)
        
        ranking_layout = QVBoxLayout(ranking_card)
        ranking_layout.setContentsMargins(20, 20, 20, 20)
        
        ranking_title = QLabel("Ranking..")
        ranking_title.setStyleSheet("color: white; font-size: 14px; font-weight: normal;")
        
        ranking_value_layout = QHBoxLayout()
        ranking_number = QLabel("2°")
        ranking_number.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        ranking_icon = QLabel("▲")
        ranking_icon.setStyleSheet("color: #34C759; font-size: 16px; font-weight: bold;")
        
        ranking_value_layout.addWidget(ranking_number)
        ranking_value_layout.addWidget(ranking_icon)
        ranking_value_layout.addStretch()
        
        ranking_layout.addWidget(ranking_title)
        ranking_layout.addLayout(ranking_value_layout)
        ranking_layout.addStretch()
        
        metas_layout.addWidget(vendas_card)
        metas_layout.addWidget(ranking_card)
        metas_layout.addStretch()
        
        main_layout.addLayout(metas_layout)
        
        # ===== SEÇÃO PENDENTE =====
        pendente_label = QLabel("Pendente")
        pendente_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(pendente_label)
        
        # Card pendente
        pendente_card = QFrame()
        pendente_card.setObjectName("metricFrame")
        pendente_card.setFixedHeight(120)
        
        pendente_layout = QVBoxLayout(pendente_card)
        pendente_layout.setContentsMargins(20, 20, 20, 20)
        
        pendente_title = QLabel("Meta de Volume de Vendas (Unidades/Contratos)")
        pendente_title.setStyleSheet("color: white; font-size: 14px; font-weight: normal;")
        
        # Barra de progresso
        progress_layout = QHBoxLayout()
        progress_bar = QFrame()
        progress_bar.setObjectName("progressBar")
        progress_bar.setFixedHeight(10)
        # Estilos movidos para glassmorphism.qss
        
        # Barra preenchida
        progress_filled = QFrame()
        progress_filled.setFixedSize(180, 10)  # 45% de 400px
        # Estilos movidos para glassmorphism.qss
        
        progress_layout.addWidget(progress_filled)
        progress_layout.addStretch()
        
        progress_percent = QLabel("45%")
        progress_percent.setStyleSheet("color: white; font-size: 12px; font-weight: normal;")
        
        pendente_layout.addWidget(pendente_title)
        pendente_layout.addLayout(progress_layout)
        pendente_layout.addWidget(progress_percent)
        
        main_layout.addWidget(pendente_card)
        main_layout.addStretch()
        
        self._apply_styles()
    

    
    def _apply_styles(self):
        """Aplicar estilos do dashboard."""
        # Estilos movidos para glassmorphism.qss
        pass
    

    
    def hide_menu_button(self):
        """Ocultar botão de menu."""
        if self.menu_button:
            self.menu_button.hide()
    
    def show_menu_button(self):
        """Mostrar botão de menu."""
        if self.menu_button:
            self.menu_button.show()
    
    def _load_dashboard_data(self):
        """Carregar dados do dashboard do backend."""
        try:
            if hasattr(self.pitch_app, 'dashboard_service') and self.pitch_app.dashboard_service:
                dashboard_data = self.pitch_app.dashboard_service.get_dashboard_data("giovanna")
                self._update_dashboard_ui(dashboard_data)
            else:
                print("⚠️ DashboardService não disponível")
        except Exception as e:
            print(f"❌ Erro ao carregar dados do dashboard: {e}")
    
    def _update_dashboard_ui(self, data: dict):
        """Atualizar interface com dados do backend."""
        try:
            # Atualizar metas
            if 'goals' in data:
                goals = data['goals']
                
                # Atualizar vendas concluídas
                if 'units' in goals:
                    units_percent = goals['units']['percent']
                    # Aqui você atualizaria os labels da UI
                    print(f"📊 Vendas: {goals['units']['current']}/{goals['units']['target']} ({units_percent:.1f}%)")
                
                # Atualizar ranking
                if 'ranking' in data:
                    ranking = data['ranking']
                    position = ranking['current_position']
                    print(f"🏆 Ranking: {position}° lugar")
                
                # Atualizar progresso pendente
                if 'contracts' in goals:
                    contracts_percent = goals['contracts']['percent']
                    print(f"📈 Progresso: {contracts_percent:.1f}%")
            
            print("✅ Dashboard atualizado com dados do backend")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar dashboard: {e}")
    
    def refresh_dashboard(self):
        """Atualizar dashboard com dados mais recentes."""
        self._load_dashboard_data()

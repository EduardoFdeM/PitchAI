"""
PitchAI - Janela Principal
========================

Interface principal do PitchAI com design glassmorphism
e layout otimizado para vendas em tempo real.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QMouseEvent
from pathlib import Path

from .start_widget import StartWidget
from .dashboard_widget import DashboardWidget
from .analysis_widget import AnalysisWidget
from .chat_widget import ChatWidget
from .summary_widget import SummaryWidget
from .menu_widget import MenuWidget
from .transcription_full_widget import TranscriptionFullWidget
from .settings_widget import SettingsWidget
from .history_widget import HistoryWidget
 

class FloatingIcon(QWidget):
    """Ícone flutuante quando a aplicação está minimizada."""
    
    restore_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(50, 50)  # Ícone menor para iPhone
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Botão do ícone (sem capturar eventos de mouse)
        self.icon_button = QPushButton("P")
        self.icon_button.setObjectName("floatingIconButton")
        # Remover conexão de clique - será tratado no mouseReleaseEvent
        # self.icon_button.clicked.connect(self.restore_requested.emit)
        # Desabilitar captura de eventos de mouse pelo botão
        self.icon_button.setMouseTracking(False)
        self.icon_button.installEventFilter(self)
        layout.addWidget(self.icon_button)
        
        self._apply_styles()
        self._setup_dragging()
    
    def _apply_styles(self):
        """Aplicar estilos do ícone flutuante."""
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QPushButton#floatingIconButton {
                background: rgba(46, 52, 64, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 30px;
                color: white;
                font-size: 24px;
                font-weight: bold;
                min-width: 60px;
                min-height: 60px;
            }
            QPushButton#floatingIconButton:hover {
                background: rgba(46, 52, 64, 1.0);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """)
    
    def _setup_dragging(self):
        """Configurar arrastar o ícone."""
        self.dragging = False
        self.drag_position = QPoint()
        self.press_position = QPoint()
        self.drag_threshold = 5  # pixels para considerar como arrastar vs clique
    
    def mousePressEvent(self, event):
        """Detectar clique para arrastar."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False  # Reset no início
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.press_position = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Arrastar o ícone."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            current_pos = event.globalPosition().toPoint()
            distance = (current_pos - self.press_position).manhattanLength()
            
            # Se moveu mais que o threshold, considera como arrastar
            if distance > self.drag_threshold:
                self.dragging = True
            
            if self.dragging:
                new_pos = current_pos - self.drag_position
                # Garantir que o ícone não saia da tela
                screen = self.screen()
                screen_geometry = screen.geometry()
                
                # Limitar posição dentro da tela
                new_x = max(0, min(new_pos.x(), screen_geometry.width() - self.width()))
                new_y = max(0, min(new_pos.y(), screen_geometry.height() - self.height()))
                
                self.move(new_x, new_y)
                event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Parar de arrastar ou restaurar janela."""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.dragging:
                # Se não arrastou, restaurar janela
                self.restore_requested.emit()
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Mouse entrou no ícone."""
        self.setCursor(Qt.CursorShape.SizeAllCursor)
    
    def leaveEvent(self, event):
        """Mouse saiu do ícone."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def eventFilter(self, obj, event):
        """Filtrar eventos do botão para permitir arrastar o ícone."""
        if obj == self.icon_button:
            # Permitir que todos os eventos de mouse sejam processados pelo widget pai
            if event.type() in [event.Type.MouseButtonPress, event.Type.MouseMove, event.Type.MouseButtonRelease]:
                return False  # Não interceptar, deixar o widget pai processar
        return super().eventFilter(obj, event)

class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self, config, pitch_app):
        super().__init__()
        self.config = config
        self.pitch_app = pitch_app
        self.app_instance = pitch_app  # Para compatibilidade
        self.is_minimized = False
        self.floating_icon = None
        
        # Configurar janela
        self.setWindowTitle("PitchAI - Copiloto de Vendas")
        self.setFixedSize(self.config.window_width, self.config.window_height)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Centralizar na tela
        self._center_window()
        
        # Configurar UI
        self._setup_ui()
        self._load_styles()
        self._connect_signals()
        
        # Configurar arrastar janela
        self._setup_window_dragging()
        
        # Mostrar tela inicial
        self.stacked_widget.setCurrentIndex(0)
        
        print("🚀 MainWindow inicializada com sucesso")
    
    def _center_window(self):
        """Centralizar janela na tela."""
        screen = self.screen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        """Configurar interface principal."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal com ID para CSS
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # ===== TITLE BAR =====
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(35)  # Barra mais compacta para iPhone
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)  # Margens menores para iPhone
        title_layout.setSpacing(8)  # Espaçamento menor
        
        # Título
        title_label = QLabel("PitchAI")
        title_label.setObjectName("titleLabel")
        title_font = QFont()
        title_font.setPointSize(13)  # Fonte menor para iPhone
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        
        # Status ONNX
        self.onnx_status_label = QLabel("ONNX: Ativo")
        self.onnx_status_label.setObjectName("statusIndicator")
        
        # Indicador de gravação
        self.recording_indicator = QLabel("🔴")
        self.recording_indicator.setObjectName("statusIndicator")
        self.recording_indicator.hide()
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.onnx_status_label)
        title_layout.addWidget(self.recording_indicator)
        
        # Botões de controle da janela
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        
        # Botão minimizar
        minimize_btn = QPushButton("−")
        minimize_btn.setObjectName("windowControlBtn")
        minimize_btn.setFixedSize(26, 26)  # Botão menor para iPhone
        minimize_btn.setToolTip("Minimizar para ícone flutuante")
        minimize_btn.clicked.connect(self._minimize_to_icon)
        
        controls_layout.addWidget(minimize_btn)
        
        title_layout.addLayout(controls_layout)
        
        container_layout.addWidget(title_bar)
        
        # ===== STACKED WIDGET =====
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("mainStackedWidget")
        
        # Adicionar widgets
        self.start_widget = StartWidget()
        self.dashboard_widget = DashboardWidget(self.config, self.app_instance)
        self.analysis_widget = AnalysisWidget(self.config, self.app_instance)
        self.chat_widget = ChatWidget()
        self.transcription_full_widget = TranscriptionFullWidget()
        self.settings_widget = SettingsWidget()
        self.history_widget = HistoryWidget()
        self.summary_widget = SummaryWidget()
        
        self.stacked_widget.addWidget(self.start_widget)
        self.stacked_widget.addWidget(self.dashboard_widget)
        self.stacked_widget.addWidget(self.analysis_widget)
        self.stacked_widget.addWidget(self.chat_widget)
        self.stacked_widget.addWidget(self.transcription_full_widget)
        self.stacked_widget.addWidget(self.settings_widget)
        self.stacked_widget.addWidget(self.history_widget)
        self.stacked_widget.addWidget(self.summary_widget)
        
        container_layout.addWidget(self.stacked_widget)
        
        # ===== MENU WIDGET =====
        self.menu_widget = MenuWidget(self)
        self.menu_widget.hide()
        # Posicionamento responsivo baseado no tamanho da janela
        menu_x = min(80, self.config.window_width - 120)
        self.menu_widget.move(menu_x, 30)
        
        # Adicionar apenas o container principal ao layout
        main_layout.addWidget(self.main_container)
        
        # O menu widget será posicionado dinamicamente e não afetará o layout
    
    def _setup_window_dragging(self):
        """Configurar arrastar a janela."""
        self.dragging = False
        self.drag_position = QPoint()
        
        # Configurar a barra de título para ser arrastável
        self.title_bar = self.findChild(QFrame, "titleBar")
        if self.title_bar:
            self.title_bar.mousePressEvent = self._title_bar_mouse_press
            self.title_bar.mouseMoveEvent = self._title_bar_mouse_move
            self.title_bar.mouseReleaseEvent = self._title_bar_mouse_release
            # Configurar cursor de arrastar na barra de título
            self.title_bar.setCursor(Qt.CursorShape.SizeAllCursor)
    
    def _title_bar_mouse_press(self, event):
        """Detectar clique na barra de título para arrastar janela."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def _title_bar_mouse_move(self, event):
        """Arrastar a janela quando mouse move na barra de título."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            event.accept()
    
    def _title_bar_mouse_release(self, event):
        """Parar de arrastar quando mouse solta na barra de título."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def mousePressEvent(self, event):
        """Detectar clique para arrastar janela de qualquer lugar."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Permitir arrastar de qualquer lugar da janela
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Arrastar a janela de qualquer lugar."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            
            # Garantir que a janela não saia completamente da tela
            screen = self.screen()
            screen_geometry = screen.geometry()
            
            # Permitir que parte da janela saia da tela, mas não completamente
            min_x = -self.width() + 100  # Deixar pelo menos 100px visível
            min_y = -self.height() + 100
            max_x = screen_geometry.width() - 100
            max_y = screen_geometry.height() - 100
            
            new_x = max(min_x, min(new_pos.x(), max_x))
            new_y = max(min_y, min(new_pos.y(), max_y))
            
            self.move(new_x, new_y)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Parar de arrastar."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def _minimize_to_icon(self):
        """Minimizar para ícone flutuante."""
        if not self.is_minimized:
            # Criar ícone flutuante
            self.floating_icon = FloatingIcon()
            self.floating_icon.restore_requested.connect(self._restore_from_icon)
            
            # Posicionar ícone próximo à posição da janela
            # Usar a posição atual da janela como referência
            window_pos = self.pos()
            screen = self.screen()
            screen_geometry = screen.geometry()
            
            # Posicionar o ícone no canto inferior direito da tela
            # ou próximo à posição da janela se estiver visível
            icon_x = min(window_pos.x() + 50, screen_geometry.width() - 80)
            icon_y = min(window_pos.y() + 50, screen_geometry.height() - 80)
            
            # Garantir que o ícone não saia da tela
            icon_x = max(20, min(icon_x, screen_geometry.width() - 70))
            icon_y = max(20, min(icon_y, screen_geometry.height() - 70))
            
            self.floating_icon.move(icon_x, icon_y)
            self.floating_icon.show()
            self.floating_icon.raise_()
            self.floating_icon.activateWindow()
            
            # Ocultar janela principal
            self.hide()
            self.is_minimized = True
    
    def _restore_from_icon(self):
        """Restaurar da janela do ícone flutuante."""
        if self.is_minimized and self.floating_icon:
            # Mostrar janela principal
            self.show()
            self.raise_()
            self.activateWindow()
            
            # Ocultar e destruir ícone flutuante
            self.floating_icon.hide()
            self.floating_icon.deleteLater()
            self.floating_icon = None
            
            self.is_minimized = False
    
    def closeEvent(self, event):
        """Evento de fechar aplicação."""
        # Se estiver minimizado, restaurar primeiro
        if self.is_minimized and self.floating_icon:
            self.floating_icon.hide()
            self.floating_icon.deleteLater()
            self.floating_icon = None
        
        # Fechar aplicação
        self.app_instance.shutdown()
        event.accept()
    
    def _load_styles(self):
        """Carregar estilos responsivos para iPhone."""
        try:
            # Tentar diferentes caminhos para o arquivo de estilos responsivos
            possible_paths = [
                self.config.app_dir / "src" / "ui" / "styles" / "responsive.qss",
                Path(__file__).parent / "styles" / "responsive.qss",
                Path.cwd() / "src" / "ui" / "styles" / "responsive.qss",
                # Fallback para glassmorphism se responsive não existir
                self.config.app_dir / "src" / "ui" / "styles" / "glassmorphism.qss",
                Path(__file__).parent / "styles" / "glassmorphism.qss",
                Path.cwd() / "src" / "ui" / "styles" / "glassmorphism.qss"
            ]
            
            styles_path = None
            for path in possible_paths:
                if path.exists():
                    styles_path = path
                    break
            
            if styles_path:
                with open(styles_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
                print(f"✅ Estilos responsivos carregados de: {styles_path}")
            else:
                print("⚠️ Arquivo de estilos não encontrado")
                print(f"Procurou em: {[str(p) for p in possible_paths]}")
        except Exception as e:
            print(f"❌ Erro ao carregar estilos: {e}")
    
    def _connect_signals(self):
        """Conectar sinais da aplicação com a UI."""
        # Conectar navegação do StartWidget para Dashboard
        self.start_widget.start_analysis_requested.connect(self._go_to_dashboard)
        
        # Conectar navegação do DashboardWidget
        self.dashboard_widget.start_analysis_requested.connect(self._start_and_go_to_analysis)
        self.dashboard_widget.history_item_clicked.connect(self._open_history_item)
        self.dashboard_widget.menu_requested.connect(self._show_menu)
        
        # Conectar navegação do AnalysisWidget
        self.analysis_widget.stop_recording_requested.connect(self._stop_and_go_to_summary)
        self.analysis_widget.chat_requested.connect(self._open_chat)
        self.analysis_widget.opportunity_chat_requested.connect(self._open_opportunity_chat)
        self.analysis_widget.objection_chat_requested.connect(self._open_objection_chat)
        self.analysis_widget.transcription_full_requested.connect(self._open_transcription_full)
        self.analysis_widget.back_to_dashboard_requested.connect(self._go_to_dashboard)
        
        # Conectar navegação do ChatWidget
        self.chat_widget.back_to_analysis_requested.connect(self._go_to_analysis)
        
        # Conectar navegação do TranscriptionFullWidget
        self.transcription_full_widget.back_to_analysis_requested.connect(self._go_to_analysis)
        
        # Conectar navegação do SettingsWidget
        self.settings_widget.back_to_dashboard_requested.connect(self._go_to_dashboard)
        
        # Conectar navegação do HistoryWidget
        self.history_widget.back_to_dashboard_requested.connect(self._go_to_dashboard)
        self.history_widget.history_item_clicked.connect(self._open_history_item)
        
        # Conectar navegação do SummaryWidget
        self.summary_widget.back_to_start_requested.connect(self._go_to_dashboard)
        
        # Conectar sinais do menu
        self.menu_widget.close_app_requested.connect(self._close_app_from_menu)
        self.menu_widget.history_requested.connect(self._open_history_from_menu)
        self.menu_widget.settings_requested.connect(self._open_settings_from_menu)
    
    def _go_to_dashboard(self):
        """Navegar para a tela principal (dashboard)."""
        self.stacked_widget.setCurrentIndex(1)
        self.dashboard_widget.show_menu_button()
    
    def _go_to_analysis(self):
        """Navegar para a tela de análise."""
        self.stacked_widget.setCurrentIndex(2)
    
    def _start_and_go_to_analysis(self):
        """Inicia a gravação e navega para a tela de análise."""
        self.stacked_widget.setCurrentIndex(2)
    
    def _stop_and_go_to_summary(self):
        """Para a gravação e navega para o resumo."""
        self.stacked_widget.setCurrentIndex(7)
    
    def _open_chat(self, sentiment_data):
        """Abrir tela de chat com IA."""
        self.chat_widget = ChatWidget(sentiment_data, "sentiment")
        self.chat_widget.back_to_analysis_requested.connect(self._go_to_analysis)
        old_widget = self.stacked_widget.widget(3)
        self.stacked_widget.removeWidget(old_widget)
        if old_widget:
            old_widget.deleteLater()
        self.stacked_widget.insertWidget(3, self.chat_widget)
        self.stacked_widget.setCurrentIndex(3)
    
    def _open_opportunity_chat(self, opportunity_data):
        """Abrir chat para oportunidade."""
        self.chat_widget = ChatWidget(opportunity_data, "opportunity")
        self.chat_widget.back_to_analysis_requested.connect(self._go_to_analysis)
        old_widget = self.stacked_widget.widget(3)
        self.stacked_widget.removeWidget(old_widget)
        if old_widget:
            old_widget.deleteLater()
        self.stacked_widget.insertWidget(3, self.chat_widget)
        self.stacked_widget.setCurrentIndex(3)
    
    def _open_objection_chat(self, objection_data):
        """Abrir chat para objeção."""
        self.chat_widget = ChatWidget(objection_data, "objection")
        self.chat_widget.back_to_analysis_requested.connect(self._go_to_analysis)
        old_widget = self.stacked_widget.widget(3)
        self.stacked_widget.removeWidget(old_widget)
        if old_widget:
            old_widget.deleteLater()
        self.stacked_widget.insertWidget(3, self.chat_widget)
        self.stacked_widget.setCurrentIndex(3)
    
    def _open_transcription_full(self, transcription_text):
        """Abrir tela de transcrição completa."""
        self.transcription_full_widget.update_transcription(transcription_text)
        self.stacked_widget.setCurrentIndex(4)
    
    def _open_history_item(self, session_id: str):
        """Abrir item do histórico."""
        print(f"📋 Abrindo histórico: {session_id}")
    
    def _show_menu(self):
        """Mostrar/ocultar menu lateral (toggle)."""
        if self.menu_widget.isVisible():
            # Fechar menu
            self.menu_widget.hide()
            # Mostrar botão de menu da tela atual
            current_index = self.stacked_widget.currentIndex()
            if current_index == 1:  # Dashboard
                self.dashboard_widget.show_menu_button()
        else:
            # Abrir menu
            # Posicionar o menu flutuando sobre o conteúdo, não afetando o layout
            self.menu_widget.move(80, 30)
            self.menu_widget.show()
            self.menu_widget.raise_()
            # Garantir que o menu fique acima de todos os outros widgets
            self.menu_widget.raise_()
    
    def _open_history_from_menu(self):
        """Abrir histórico a partir do menu."""
        self.menu_widget.hide()
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            self.dashboard_widget.show_menu_button()
        self.stacked_widget.setCurrentIndex(6)
    
    def _open_settings_from_menu(self):
        """Abrir configurações a partir do menu."""
        self.menu_widget.hide()
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            self.dashboard_widget.show_menu_button()
        self.stacked_widget.setCurrentIndex(5)
    
    def _close_app_from_menu(self):
        """Fechar aplicação a partir do menu."""
        self.menu_widget.hide()
        current_index = self.stacked_widget.currentIndex()
        if current_index == 1:
            self.dashboard_widget.show_menu_button()
        self.close()

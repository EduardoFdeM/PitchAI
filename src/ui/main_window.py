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
from PyQt6.QtCore import Qt, pyqtSlot, QPoint
from PyQt6.QtGui import QFont, QMouseEvent

from .start_widget import StartWidget
from .recording_widget import RecordingWidget
from .analysis_widget import AnalysisWidget
from .rag_suggestions_widget import RAGSuggestionsWidget
from .summary_widget import SummaryWidget
 

class MainWindow(QMainWindow):
    """Janela principal do PitchAI com design moderno e navegação entre telas."""
    
    def __init__(self, config, app_instance):
        super().__init__()
        self.config = config
        self.app_instance = app_instance
        
        # Configurar janela sem bordas (estilo moderno)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Responsividade baseada na resolução da tela
        screen = self.screen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Para resolução 1920x1200, usar altura ~1100px (91% da tela)
        # Manter proporção elegante baseada na resolução
        if screen_width >= 1920:  # Desktop/laptop moderno
            height = min(1100, int(screen_height * 0.91))
            width = int(height * 0.6)  # Proporção 3:5 para desktop
        else:  # Telas menores
            height = int(screen_height * 0.85)
            width = int(height * 0.6)
        
        # Centralizar na tela
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.setGeometry(x, y, width, height)
        self.setFixedSize(width, height)
        
        # Variáveis para arrastar janela
        self.drag_pos = QPoint()
        
        self._setup_ui()
        self._load_styles()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configurar layout da interface moderna."""
        # Container principal com borda arredondada
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        self.setCentralWidget(main_container)
        
        # Layout principal
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sem barra de título para efeito fullscreen liquid glass
        
        # ===== STACK DE TELAS =====
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Criar e adicionar as telas
        self.start_widget = StartWidget()
        self.recording_widget = RecordingWidget(self.config, self.app_instance)
        self.analysis_widget = AnalysisWidget(self.config, self.app_instance)
        self.rag_widget = RAGSuggestionsWidget()
        self.summary_widget = SummaryWidget()
        
        self.stacked_widget.addWidget(self.start_widget)      # Índice 0
        self.stacked_widget.addWidget(self.analysis_widget)   # Índice 1
        self.stacked_widget.addWidget(self.rag_widget)        # Índice 2
        self.stacked_widget.addWidget(self.summary_widget)    # Índice 3
        
        # Iniciar na tela de splash
        self.stacked_widget.setCurrentIndex(0)
    
    def _create_title_bar(self) -> QFrame:
        """Criar barra de título personalizada arrastável."""
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # Logo e título
        title_label = QLabel("🚀 PitchAI")
        title_label.setObjectName("titleLabel")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.Medium)
        title_label.setFont(title_font)
        
        # Status indicators (só mostrar na tela de análise)
        self.npu_status_label = QLabel("🔴 NPU")
        self.npu_status_label.setObjectName("statusIndicator")
        self.npu_status_label.setVisible(False)  # Oculto inicialmente
        
        self.recording_indicator = QLabel("⚫ Offline")
        self.recording_indicator.setObjectName("statusIndicator")
        self.recording_indicator.setVisible(False)  # Oculto inicialmente
        
        # Botões de controle da janela
        self.minimize_btn = QPushButton("🗕")
        self.minimize_btn.setObjectName("windowControlBtn")
        self.minimize_btn.setFixedSize(30, 25)
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(30, 25)
        self.close_btn.clicked.connect(self.close)
        
        # Layout
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.npu_status_label)
        layout.addWidget(self.recording_indicator)
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)
        
        return title_bar
    
    def _load_styles(self):
        """Carregar estilos glassmorphism."""
        try:
            styles_path = self.config.app_dir / "src" / "ui" / "styles" / "glassmorphism.qss"
            if styles_path.exists():
                with open(styles_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
            else:
                # Estilo básico como fallback
                self._apply_basic_styles()
        except Exception as e:
            print(f"⚠️ Erro ao carregar estilos: {e}")
            self._apply_basic_styles()
    
    def _apply_basic_styles(self):
        """Aplicar estilos glassmorphism moderno."""
        style = """
        QMainWindow {
            background-color: #151515;
            border-radius: 25px;
        }
        
        QWidget#mainContainer {
            background: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.8, 
                fx: 0.5, fy: 0.5,
                stop: 0 rgba(73, 65, 206, 0.4), 
                stop: 0.4 rgba(93, 31, 176, 0.3), 
                stop: 1 #151515);
            border-radius: 25px;
            border: 1px solid rgba(175, 177, 240, 0.2);
        }
        
        QFrame#titleBar {
            background: rgba(21, 21, 21, 0.8);
            border-radius: 25px 25px 0px 0px;
            border-bottom: 1px solid rgba(175, 177, 240, 0.2);
        }
        
        QLabel#titleLabel {
            color: rgba(175, 177, 240, 0.95);
            font-weight: bold;
        }
        
        QLabel#statusIndicator {
            color: rgba(175, 177, 240, 0.8);
            font-size: 11px;
            font-weight: bold;
        }
        
        QPushButton#windowControlBtn {
            background: rgba(73, 65, 206, 0.3);
            border: 1px solid rgba(175, 177, 240, 0.3);
            border-radius: 4px;
            color: rgba(175, 177, 240, 0.9);
            font-size: 12px;
        }
        
        QPushButton#windowControlBtn:hover {
            background: rgba(73, 65, 206, 0.5);
        }
        
        QPushButton#closeBtn {
            background: rgba(93, 31, 176, 0.5);
            border: 1px solid rgba(93, 31, 176, 0.7);
            border-radius: 4px;
            color: rgba(175, 177, 240, 0.95);
            font-size: 12px;
        }
        
        QPushButton#closeBtn:hover {
            background: rgba(93, 31, 176, 0.8);
        }
        """
        self.setStyleSheet(style)
        
        # O restante dos estilos para os widgets filhos continua o mesmo
        # para manter a consistência que já tínhamos.
        # Se quiser refinar mais algum elemento, me avise!
    
    def _connect_signals(self):
        """Conectar sinais da aplicação com a UI."""
        # Conectar navegação do StartWidget para RecordingWidget
        self.start_widget.start_analysis_requested.connect(self._go_to_recording)
        
        # Conectar navegação do SummaryWidget
        self.summary_widget.back_to_start_requested.connect(self._go_to_start)
        
        # Conectar sinais RAG
        if hasattr(self.app_instance, 'rag_suggestions_ready'):
            self.app_instance.rag_suggestions_ready.connect(self._on_rag_suggestions_ready)
        
        if hasattr(self.app_instance, 'rag_error'):
            self.app_instance.rag_error.connect(self._on_rag_error)
        
        # Os sinais do app_instance já estão conectados no AnalysisWidget
        # Não precisamos reconectá-los aqui
    
    def _go_to_analysis(self):
        """Navegar para a tela de análise."""
        self.stacked_widget.setCurrentIndex(1)
        
        # Mostrar indicadores de status na barra de título
        self.npu_status_label.setVisible(True)
        self.recording_indicator.setVisible(True)
        
        # Atualizar status
        self.update_npu_status("connected")
        
    def _go_to_summary(self):
        """Navegar para a tela de resumo."""
        self.stacked_widget.setCurrentIndex(3)
        
        # Manter indicadores de status ocultos
        self.npu_status_label.setVisible(False)
        self.recording_indicator.setVisible(False)
    
    def _go_to_rag(self):
        """Navegar para a tela de sugestões RAG."""
        self.stacked_widget.setCurrentIndex(2)
        
        # Manter indicadores de status ocultos
        self.npu_status_label.setVisible(False)
        self.recording_indicator.setVisible(False)
        
    def _go_to_start(self):
        """Navegar para a tela inicial."""
        self.stacked_widget.setCurrentIndex(0)
        
        # Ocultar indicadores de status
        self.npu_status_label.setVisible(False)
        self.recording_indicator.setVisible(False)
        
        # Reiniciar loading do StartWidget
        self.start_widget.restart_loading()
    
    def _go_to_recording(self):
        """Navegar para a tela de gravação (nova tela principal)."""
        self.stacked_widget.setCurrentIndex(1)
        
    def _start_and_go_to_analysis(self):
        """Inicia a gravação e navega para a tela de análise."""
        self.app_instance.start_recording()
        self.stacked_widget.setCurrentIndex(2) # AnalysisWidget é o índice 2
    
    @pyqtSlot()
    def update_npu_status(self, status: str):
        """Atualizar status da NPU no header."""
        if status == "connected":
            self.npu_status_label.setText("🟢 NPU Conectada")
        elif status == "loading":
            self.npu_status_label.setText("🟡 NPU Carregando...")
        else:
            self.npu_status_label.setText("🔴 NPU Desconectada")
    
    @pyqtSlot(bool)
    def update_recording_status(self, is_recording: bool):
        """Atualizar status de gravação."""
        if is_recording:
            self.recording_indicator.setText("🔴 Gravando")
        else:
            self.recording_indicator.setText("⚫ Offline")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Detectar clique para arrastar janela."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Arrastar janela."""
        if hasattr(self, 'drag_pos') and not self.drag_pos.isNull():
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
                self.drag_pos = event.globalPosition().toPoint()
                event.accept()

    def keyPressEvent(self, event):
        """Atalhos de teclado."""
        if event.key() == Qt.Key.Key_F5:
            # F5 para voltar à tela inicial (restart rápido)
            self._go_to_start()
        elif event.key() == Qt.Key.Key_F6:
            # F6 para recarregar estilos
            self._load_styles()
        elif event.key() == Qt.Key.Key_F7:
            # F7 para ir ao resumo (para testes)
            self._go_to_summary()
        elif event.key() == Qt.Key.Key_F8:
            # F8 para ir às sugestões RAG (para testes)
            self._go_to_rag()
        elif event.key() == Qt.Key.Key_Escape:
            # ESC para voltar à tela inicial
            self._go_to_start()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Evento de fechamento da janela."""
        self.app_instance.shutdown()
        event.accept()
    
    @pyqtSlot(object)
    def _on_rag_suggestions_ready(self, result):
        """Callback quando sugestões RAG estão prontas."""
        # Navegar para a tela RAG e exibir resultado
        self._go_to_rag()
        self.rag_widget.display_rag_result(result)
    
    @pyqtSlot(str)
    def _on_rag_error(self, error_message):
        """Callback quando há erro no RAG."""
        # Navegar para a tela RAG e exibir erro
        self._go_to_rag()
        self.rag_widget.show_error(error_message)

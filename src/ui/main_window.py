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
from .analysis_widget import AnalysisWidget
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
        
        # ===== BARRA DE TÍTULO PERSONALIZADA =====
        self.title_bar = self._create_title_bar()
        layout.addWidget(self.title_bar)
        
        # ===== STACK DE TELAS =====
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Criar e adicionar as telas
        self.start_widget = StartWidget()
        self.analysis_widget = AnalysisWidget(self.config, self.app_instance)
        self.summary_widget = SummaryWidget()
        
        self.stacked_widget.addWidget(self.start_widget)      # Índice 0
        self.stacked_widget.addWidget(self.analysis_widget)   # Índice 1
        self.stacked_widget.addWidget(self.summary_widget)    # Índice 2
        
        # Iniciar na tela inicial
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
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(15, 76, 129, 0.7), stop: 0.5 rgba(26, 45, 107, 0.8), stop: 1 rgba(46, 52, 64, 0.9));
            border-radius: 25px;
        }
        
        QWidget#mainContainer {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(255, 255, 255, 0.1), stop: 1 rgba(255, 255, 255, 0.05));
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        }
        
        QFrame#titleBar {
            background: rgba(46, 52, 64, 0.8);
            border-radius: 25px 25px 0px 0px;
            border-bottom: 1px solid rgba(129, 161, 193, 0.2);
        }
        
        QLabel#titleLabel {
            color: #ECEFF4;
            font-weight: bold;
        }
        
        QLabel#statusIndicator {
            color: #D8DEE9;
            font-size: 11px;
            font-weight: bold;
        }
        
        QPushButton#windowControlBtn {
            background: rgba(76, 86, 106, 0.5);
            border: 1px solid rgba(129, 161, 193, 0.3);
            border-radius: 4px;
            color: #D8DEE9;
            font-size: 12px;
        }
        
        QPushButton#windowControlBtn:hover {
            background: rgba(136, 192, 208, 0.3);
        }
        
        QPushButton#closeBtn {
            background: rgba(191, 97, 106, 0.5);
            border: 1px solid rgba(191, 97, 106, 0.7);
            border-radius: 4px;
            color: #ECEFF4;
            font-size: 12px;
        }
        
        QPushButton#closeBtn:hover {
            background: rgba(191, 97, 106, 0.8);
        }
        """
        self.setStyleSheet(style)
    
    def _connect_signals(self):
        """Conectar sinais da aplicação com a UI."""
        # Conectar navegação do StartWidget
        self.start_widget.start_analysis_requested.connect(self._go_to_analysis)
        
        # Conectar navegação do SummaryWidget
        self.summary_widget.back_to_start_requested.connect(self._go_to_start)
        
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
    
    def _go_to_summary(self):
        """Navegar para a tela de resumo."""
        self.stacked_widget.setCurrentIndex(2)
        
        # Manter indicadores de status visíveis
        self.npu_status_label.setVisible(True)
        self.recording_indicator.setVisible(True)
        
        # Atualizar status para "concluído"
        self.update_recording_status(False)
    
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
        elif event.key() == Qt.Key.Key_Escape:
            # ESC para voltar à tela inicial
            self._go_to_start()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Evento de fechamento da janela."""
        self.app_instance.shutdown()
        event.accept()

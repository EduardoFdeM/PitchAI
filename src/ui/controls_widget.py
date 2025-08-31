"""
Controls Widget - Controles Principais
======================================

Botões e controles principais da aplicação.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QVBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ControlsWidget(QWidget):
    """Widget de controles principais."""
    
    # Sinais
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    pause_recording = pyqtSignal()
    generate_summary = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_recording = False
        self.setMaximumHeight(80)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar interface de controles."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        
        # ===== CONTROLES DE GRAVAÇÃO =====
        recording_frame = QFrame()
        recording_frame.setObjectName("controlFrame")
        recording_layout = QHBoxLayout(recording_frame)
        
        # Botão principal (Start/Stop)
        self.main_button = QPushButton("🎤 Iniciar Gravação")
        self.main_button.setObjectName("mainButton")
        self.main_button.clicked.connect(self._toggle_recording)
        
        # Botão de pausa
        self.pause_button = QPushButton("⏸️ Pausar")
        self.pause_button.setObjectName("secondaryButton")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_recording.emit)
        
        recording_layout.addWidget(self.main_button)
        recording_layout.addWidget(self.pause_button)
        
        # ===== AÇÕES SECUNDÁRIAS =====
        actions_frame = QFrame()
        actions_frame.setObjectName("controlFrame")
        actions_layout = QHBoxLayout(actions_frame)
        
        # Botão de resumo
        summary_button = QPushButton("📋 Gerar Resumo")
        summary_button.setObjectName("secondaryButton")
        summary_button.clicked.connect(self.generate_summary.emit)
        
        # Botão de configurações
        settings_button = QPushButton("⚙️ Configurações")
        settings_button.setObjectName("secondaryButton")
        
        # Botão de histórico
        history_button = QPushButton("📚 Histórico")
        history_button.setObjectName("secondaryButton")
        
        actions_layout.addWidget(summary_button)
        actions_layout.addWidget(settings_button)
        actions_layout.addWidget(history_button)
        
        # ===== STATUS =====
        status_frame = QFrame()
        status_frame.setObjectName("controlFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Pronto para gravação")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.time_label)
        
        # ===== LAYOUT FINAL =====
        main_layout.addWidget(recording_frame, 2)   # 40% 
        main_layout.addWidget(actions_frame, 3)     # 50%
        main_layout.addWidget(status_frame, 1)      # 10%
        
        self._apply_styles()
    
    def _apply_styles(self):
        """Aplicar estilos aos controles."""
        # Estilos movidos para glassmorphism.qss
        pass
    
    def _toggle_recording(self):
        """Alternar entre iniciar e parar gravação."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Iniciar gravação."""
        self.is_recording = True
        self.main_button.setText("⏹️ Parar Gravação")
        self.main_button.setProperty("recording", "true")
        self.main_button.style().polish(self.main_button)
        self.pause_button.setEnabled(True)
        self.status_label.setText("🔴 Gravando...")
        self.start_recording.emit()
    
    def _stop_recording(self):
        """Parar gravação."""
        self.is_recording = False
        self.main_button.setText("🎤 Iniciar Gravação") 
        self.main_button.setProperty("recording", "false")
        self.main_button.style().polish(self.main_button)
        self.pause_button.setEnabled(False)
        self.status_label.setText("Pronto para gravação")
        self.time_label.setText("00:00")
        self.stop_recording.emit()
    
    def update_recording_time(self, seconds: int):
        """Atualizar tempo de gravação."""
        minutes = seconds // 60
        secs = seconds % 60
        self.time_label.setText(f"{minutes:02d}:{secs:02d}")

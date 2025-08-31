"""
Settings Widget - Configurações de Áudio
=======================================

Widget para configurações e teste de áudio.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSlider, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import random

class SettingsWidget(QWidget):
    """Widget de configurações de áudio."""
    
    # Sinais
    back_to_dashboard_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_audio_simulation()
        
    def _setup_ui(self):
        """Configurar interface de configurações."""
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
        title_label = QLabel("⚙️ Configurações de Áudio")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # ===== CONFIGURAÇÕES DE ENTRADA =====
        input_frame = QFrame()
        input_frame.setObjectName("settingsFrame")
        
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)
        
        input_title = QLabel("🎤 Entrada de Áudio")
        input_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        # Seletor de dispositivo de entrada
        input_device_layout = QHBoxLayout()
        input_device_label = QLabel("Dispositivo:")
        input_device_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.input_device_combo = QComboBox()
        self.input_device_combo.setObjectName("deviceCombo")
        self.input_device_combo.addItems(["Microfone Padrão", "Microfone USB", "Microfone Bluetooth"])
        
        input_device_layout.addWidget(input_device_label)
        input_device_layout.addWidget(self.input_device_combo)
        input_device_layout.addStretch()
        
        # Controle de volume de entrada
        input_volume_layout = QHBoxLayout()
        input_volume_label = QLabel("Volume:")
        input_volume_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.input_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.input_volume_slider.setObjectName("volumeSlider")
        self.input_volume_slider.setRange(0, 100)
        self.input_volume_slider.setValue(80)
        
        self.input_volume_value = QLabel("80%")
        self.input_volume_value.setStyleSheet("color: white; font-size: 14px; min-width: 40px;")
        
        input_volume_layout.addWidget(input_volume_label)
        input_volume_layout.addWidget(self.input_volume_slider)
        input_volume_layout.addWidget(self.input_volume_value)
        
        # Conectar slider
        self.input_volume_slider.valueChanged.connect(
            lambda value: self.input_volume_value.setText(f"{value}%")
        )
        
        # Teste de entrada
        self.test_input_btn = QPushButton("🎤 Testar Entrada")
        self.test_input_btn.setObjectName("testButton")
        self.test_input_btn.clicked.connect(self._toggle_input_test)
        
        # Indicador de nível de entrada
        self.input_level_bar = QProgressBar()
        self.input_level_bar.setObjectName("levelBar")
        self.input_level_bar.setRange(0, 100)
        self.input_level_bar.setValue(0)
        
        input_layout.addWidget(input_title)
        input_layout.addLayout(input_device_layout)
        input_layout.addLayout(input_volume_layout)
        input_layout.addWidget(self.test_input_btn)
        input_layout.addWidget(self.input_level_bar)
        
        main_layout.addWidget(input_frame)
        
        # ===== CONFIGURAÇÕES DE SAÍDA =====
        output_frame = QFrame()
        output_frame.setObjectName("settingsFrame")
        
        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(15)
        
        output_title = QLabel("🔊 Saída de Áudio")
        output_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        # Seletor de dispositivo de saída
        output_device_layout = QHBoxLayout()
        output_device_label = QLabel("Dispositivo:")
        output_device_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.output_device_combo = QComboBox()
        self.output_device_combo.setObjectName("deviceCombo")
        self.output_device_combo.addItems(["Alto-falantes Padrão", "Fones de Ouvido", "Bluetooth"])
        
        output_device_layout.addWidget(output_device_label)
        output_device_layout.addWidget(self.output_device_combo)
        output_device_layout.addStretch()
        
        # Controle de volume de saída
        output_volume_layout = QHBoxLayout()
        output_volume_label = QLabel("Volume:")
        output_volume_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.output_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.output_volume_slider.setObjectName("volumeSlider")
        self.output_volume_slider.setRange(0, 100)
        self.output_volume_slider.setValue(70)
        
        self.output_volume_value = QLabel("70%")
        self.output_volume_value.setStyleSheet("color: white; font-size: 14px; min-width: 40px;")
        
        output_volume_layout.addWidget(output_volume_label)
        output_volume_layout.addWidget(self.output_volume_slider)
        output_volume_layout.addWidget(self.output_volume_value)
        
        # Conectar slider
        self.output_volume_slider.valueChanged.connect(
            lambda value: self.output_volume_value.setText(f"{value}%")
        )
        
        # Teste de saída
        self.test_output_btn = QPushButton("🔊 Testar Saída")
        self.test_output_btn.setObjectName("testButton")
        self.test_output_btn.clicked.connect(self._toggle_output_test)
        
        output_layout.addWidget(output_title)
        output_layout.addLayout(output_device_layout)
        output_layout.addLayout(output_volume_layout)
        output_layout.addWidget(self.test_output_btn)
        
        main_layout.addWidget(output_frame)
        
        # ===== STATUS =====
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 20, 20, 20)
        status_layout.setSpacing(10)
        
        status_title = QLabel("📊 Status do Sistema")
        status_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        self.status_label = QLabel("✅ Sistema de áudio funcionando corretamente")
        self.status_label.setStyleSheet("color: #34C759; font-size: 14px;")
        
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_frame)
        main_layout.addStretch()
        
        self._apply_styles()
        
        # Estado dos testes
        self.input_testing = False
        self.output_testing = False
        
    def _toggle_input_test(self):
        """Alternar teste de entrada."""
        if not self.input_testing:
            self.input_testing = True
            self.test_input_btn.setText("🛑 Parar Teste")
            self.test_input_btn.setStyleSheet("""
                QPushButton#testButton {
                    background: #FF3B30;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
            """)
        else:
            self.input_testing = False
            self.test_input_btn.setText("🎤 Testar Entrada")
            self.input_level_bar.setValue(0)
            self.test_input_btn.setStyleSheet("""
                QPushButton#testButton {
                    background: #007AFF;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
            """)
    
    def _toggle_output_test(self):
        """Alternar teste de saída."""
        if not self.output_testing:
            self.output_testing = True
            self.test_output_btn.setText("🛑 Parar Teste")
            self.test_output_btn.setStyleSheet("""
                QPushButton#testButton {
                    background: #FF3B30;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
            """)
        else:
            self.output_testing = False
            self.test_output_btn.setText("🔊 Testar Saída")
            self.test_output_btn.setStyleSheet("""
                QPushButton#testButton {
                    background: #007AFF;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
            """)
    
    def _start_audio_simulation(self):
        """Iniciar simulação de áudio."""
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self._update_audio_levels)
        self.audio_timer.start(100)  # Atualizar a cada 100ms
    
    def _update_audio_levels(self):
        """Atualizar níveis de áudio simulados."""
        if self.input_testing:
            # Simular nível de entrada variável
            level = random.randint(20, 90)
            self.input_level_bar.setValue(level)
    
    def _apply_styles(self):
        """Aplicar estilos das configurações."""
        # Estilos movidos para glassmorphism.qss
        pass

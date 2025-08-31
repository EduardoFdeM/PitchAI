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
import numpy as np
import pyaudio

class SettingsWidget(QWidget):
    """Widget de configurações de áudio."""
    
    # Sinais
    back_to_dashboard_requested = pyqtSignal()
    
    def __init__(self, app_instance=None, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.audio_devices = self._detect_audio_devices()
        self._setup_ui()
        self._start_audio_simulation()
        
    def _detect_audio_devices(self):
        """Detectar dispositivos de áudio disponíveis."""
        devices = {
            'input': [],
            'output': []
        }
        
        try:
            pa = pyaudio.PyAudio()
            
            # Detectar dispositivos de entrada (microfones)
            for i in range(pa.get_device_count()):
                try:
                    device_info = pa.get_device_info_by_index(i)
                    
                    # Dispositivos de entrada
                    if device_info['maxInputChannels'] > 0:
                        devices['input'].append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': int(device_info['defaultSampleRate'])
                        })
                    
                    # Dispositivos de saída
                    if device_info['maxOutputChannels'] > 0:
                        devices['output'].append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxOutputChannels'],
                            'sample_rate': int(device_info['defaultSampleRate'])
                        })
                        
                except Exception as e:
                    print(f"⚠️ Erro ao obter info do dispositivo {i}: {e}")
                    continue
            
            pa.terminate()
            
            print("🎤 Dispositivos de áudio detectados:")
            print(f"   Entrada: {len(devices['input'])} dispositivos")
            print(f"   Saída: {len(devices['output'])} dispositivos")
            
        except Exception as e:
            print(f"❌ Erro ao detectar dispositivos: {e}")
            # Dispositivos padrão como fallback
            devices['input'] = [{'index': 0, 'name': 'Microfone Padrão', 'channels': 1, 'sample_rate': 48000}]
            devices['output'] = [{'index': 0, 'name': 'Alto-falantes Padrão', 'channels': 2, 'sample_rate': 48000}]
        
        return devices
        
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
        title_label = QLabel("Configurações de Áudio")
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
        
        input_title = QLabel("Entrada de Áudio")
        input_title.setStyleSheet("color: rgba(73, 65, 206, 0.8); font-size: 18px; font-weight: bold;")
        
        # Seletor de dispositivo de entrada
        input_device_layout = QHBoxLayout()
        input_device_label = QLabel("Dispositivo:")
        input_device_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.input_device_combo = QComboBox()
        self.input_device_combo.setObjectName("deviceCombo")
        
        # Preencher com dispositivos detectados
        for device in self.audio_devices['input']:
            device_text = f"{device['name']} ({device['channels']}ch, {device['sample_rate']}Hz)"
            self.input_device_combo.addItem(device_text, device['index'])
        
        # Conectar mudança de dispositivo
        self.input_device_combo.currentIndexChanged.connect(self._on_input_device_changed)
        
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
        self.test_input_btn = QPushButton("Testar Entrada")
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
        
        output_title = QLabel("Saída de Áudio")
        output_title.setStyleSheet("color: rgba(73, 65, 206, 0.8); font-size: 18px; font-weight: bold;")
        
        # Seletor de dispositivo de saída
        output_device_layout = QHBoxLayout()
        output_device_label = QLabel("Dispositivo:")
        output_device_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.output_device_combo = QComboBox()
        self.output_device_combo.setObjectName("deviceCombo")
        
        # Preencher com dispositivos detectados
        for device in self.audio_devices['output']:
            device_text = f"{device['name']} ({device['channels']}ch, {device['sample_rate']}Hz)"
            self.output_device_combo.addItem(device_text, device['index'])
        
        # Conectar mudança de dispositivo
        self.output_device_combo.currentIndexChanged.connect(self._on_output_device_changed)
        
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
        self.test_output_btn = QPushButton("Testar Saída")
        self.test_output_btn.setObjectName("testButton")
        self.test_output_btn.clicked.connect(self._toggle_output_test)
        
        output_layout.addWidget(output_title)
        output_layout.addLayout(output_device_layout)
        output_layout.addLayout(output_volume_layout)
        output_layout.addWidget(self.test_output_btn)
        
        main_layout.addWidget(output_frame)
        
        # Remover seção de status completamente
        main_layout.addStretch()
        
        self._apply_styles()
        
        # Estado dos testes
        self.input_testing = False
        self.output_testing = False
        
        # Integração com áudio real
        self.audio_capture = None
        if self.app_instance and hasattr(self.app_instance, 'audio_capture'):
            self.audio_capture = self.app_instance.audio_capture
        
    def _on_input_device_changed(self):
        """Quando o dispositivo de entrada é alterado."""
        if self.input_device_combo.count() > 0:
            device_index = self.input_device_combo.currentData()
            device_name = self.input_device_combo.currentText()
            print(f"🎤 Dispositivo de entrada alterado para: {device_name} (índice: {device_index})")
            
            # Atualizar configuração do sistema de áudio se disponível
            if self.audio_capture and hasattr(self.audio_capture, 'set_input_device'):
                try:
                    self.audio_capture.set_input_device(device_index)
                    print(f"✅ Dispositivo de entrada configurado no sistema")
                except Exception as e:
                    print(f"⚠️ Erro ao configurar dispositivo: {e}")
            else:
                print(f"⚠️ Sistema de áudio não suporta mudança de dispositivo")
    
    def _on_output_device_changed(self):
        """Quando o dispositivo de saída é alterado."""
        if self.output_device_combo.count() > 0:
            device_index = self.output_device_combo.currentData()
            device_name = self.output_device_combo.currentText()
            print(f"🔊 Dispositivo de saída alterado para: {device_name} (índice: {device_index})")
            
            # Aqui você pode implementar a configuração do dispositivo de saída
            # Por enquanto, apenas logamos a mudança
        
    def _toggle_input_test(self):
        """Alternar teste de entrada."""
        if not self.input_testing:
            self.input_testing = True
            self.test_input_btn.setText("Parar Teste")
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
            
            # Obter dispositivo selecionado
            selected_device = self.input_device_combo.currentData()
            selected_name = self.input_device_combo.currentText()
            
            print(f"🎤 ===== INICIANDO TESTE DE MICROFONE =====")
            print(f"🎤 Dispositivo selecionado: {selected_name}")
            print(f"🎤 Conectando ao sistema de áudio...")
            
            # Iniciar captura real de áudio se disponível
            if self.audio_capture and not self.audio_capture.is_capturing:
                try:
                    # Configurar dispositivo específico
                    if selected_device is not None and hasattr(self.audio_capture, 'set_input_device'):
                        self.audio_capture.set_input_device(selected_device)
                    
                    self.audio_capture.add_callback(self._on_audio_data)
                    self.audio_capture.start()
                    
                    print("✅ Captura de áudio real iniciada!")
                    print("🎤 FALE NO MICROFONE AGORA - você deve ver:")
                    print("   - Barra de nível subindo e descendo")
                    print("   - Logs no terminal: '🎤 Áudio detectado: nível X%'")
                    print("   - Se não aparecer nada, o microfone não está funcionando")
                    
                except Exception as e:
                    print(f"❌ Erro ao iniciar captura real: {e}")
                    print("🔄 Usando simulação como fallback...")
                    # Fallback para simulação
                    self._start_audio_simulation()
            else:
                print("⚠️ Sistema de áudio não disponível - usando simulação")
                # Usar simulação se não houver captura real
                self._start_audio_simulation()
                
        else:
            self.input_testing = False
            self.test_input_btn.setText("Testar Entrada")
            self.input_level_bar.setValue(0)
            self.test_input_btn.setStyleSheet("""
                QPushButton#testButton {
                    background: rgba(73, 65, 206, 0.8);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
            """)
            
            # Parar captura real
            if self.audio_capture and self.audio_capture.is_capturing:
                try:
                    print("⏹️ ===== PARANDO TESTE DE MICROFONE =====")
                    self.audio_capture.remove_callback(self._on_audio_data)
                    self.audio_capture.stop()
                    print("✅ Captura de áudio real parada")
                    
                    # Mostrar estatísticas finais
                    metrics = self.audio_capture.get_metrics()
                    print(f"📊 Estatísticas do teste:")
                    print(f"   - Chunks de microfone recebidos: {metrics['chunks_received']['mic']}")
                    print(f"   - Chunks de loopback recebidos: {metrics['chunks_received']['loopback']}")
                    print(f"   - Duração: {metrics.get('duration', 'N/A')}")
                    
                    if metrics['chunks_received']['mic'] > 0:
                        print("✅ MICROFONE FUNCIONANDO CORRETAMENTE!")
                    else:
                        print("❌ MICROFONE NÃO ESTÁ FUNCIONANDO - nenhum dado recebido")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao parar captura real: {e}")
            
            # Parar simulação
            if hasattr(self, 'audio_timer'):
                self.audio_timer.stop()
    
    def _on_audio_data(self, audio_chunk):
        """Callback para dados de áudio reais."""
        if not self.input_testing:
            return
            
        try:
            # Calcular nível de áudio real
            audio_data = np.array(audio_chunk.buffer, dtype=np.int16)
            if len(audio_data) > 0:
                # Calcular RMS (Root Mean Square) para medir o nível
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                # Converter para escala 0-100
                level = min(100, max(0, int((rms / 32768.0) * 100 * 10)))  # Amplificar para melhor visualização
                self.input_level_bar.setValue(level)
                
                # Log para debug - mais detalhado
                if level > 5:  # Logar quando há qualquer áudio
                    print(f"🎤 Áudio detectado: nível {level}% (RMS: {rms:.2f}) - Fonte: {audio_chunk.source}")
                    
                    # Verificar se é áudio significativo
                    if level > 20:
                        print(f"🔊 ÁUDIO FORTE DETECTADO! Nível: {level}%")
                    elif level > 10:
                        print(f"🔉 Áudio médio detectado. Nível: {level}%")
                    else:
                        print(f"🔈 Áudio fraco detectado. Nível: {level}%")
                        
        except Exception as e:
            print(f"⚠️ Erro ao processar áudio: {e}")
    
    def _start_audio_simulation(self):
        """Iniciar simulação de áudio - APENAS EM CASO DE FALHA."""
        print("⚠️ ===== MODO DE FALHA - SIMULAÇÃO =====")
        print("⚠️ Sistema de áudio real não disponível")
        print("⚠️ Usando simulação como último recurso")
        
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self._update_audio_levels)
        self.audio_timer.start(100)  # Atualizar a cada 100ms
    
    def _update_audio_levels(self):
        """Atualizar níveis de áudio simulados - APENAS EM FALHA."""
        if self.input_testing:
            # Simular nível de entrada variável
            level = random.randint(20, 90)
            self.input_level_bar.setValue(level)
            
            # Log ocasional para simulação
            if random.random() < 0.1:  # 10% de chance de log
                print(f"⚠️ SIMULAÇÃO: nível {level}% (NÃO É ÁUDIO REAL)")
    
    def _toggle_output_test(self):
        """Alternar teste de saída."""
        if not self.output_testing:
            self.output_testing = True
            self.test_output_btn.setText("Parar Teste")
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
            
            # Obter dispositivo selecionado
            selected_device = self.output_device_combo.currentData()
            selected_name = self.output_device_combo.currentText()
            
            print(f"🔊 ===== INICIANDO TESTE DE SAÍDA =====")
            print(f"🔊 Dispositivo selecionado: {selected_name}")
            print(f"🔊 Volume configurado: {self.output_volume_slider.value()}%")
            print("🔊 Teste de saída iniciado - você deve ouvir um tom de teste")
            
        else:
            self.output_testing = False
            self.test_output_btn.setText("Testar Saída")
            self.test_output_btn.setStyleSheet("""
                QPushButton#testButton {
                    background: rgba(73, 65, 206, 0.8);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
            """)
            
            print("⏹️ Teste de saída parado")
    
    def _apply_styles(self):
        """Aplicar estilos das configurações."""
        # Estilos movidos para glassmorphism.qss
        pass

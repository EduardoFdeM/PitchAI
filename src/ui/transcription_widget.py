"""
Transcription Widget - Transcrição em Tempo Real
================================================

Exibe a transcrição da conversa com identificação de falantes.
Integração com BD para armazenamento e geração de resumos pós-reunião.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QScrollArea, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSlot, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from typing import Optional, Dict, Any
import time
import logging


class TranscriptionWidget(QWidget):
    """Widget de transcrição em tempo real com integração BD."""

    # Sinais para integração
    transcription_saved = pyqtSignal(str)  # call_id
    summary_requested = pyqtSignal(str)    # call_id
    fullscreen_requested = pyqtSignal(str) # texto da transcrição

    def __init__(self, config, transcription_service=None, database_manager=None):
        super().__init__()
        self.config = config
        self.transcription_service = transcription_service
        self.database_manager = database_manager
        self.current_call_id: Optional[str] = None
        self.is_recording = False
        self.logger = logging.getLogger(__name__)

        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configurar interface de transcrição."""
        layout = QVBoxLayout(self)

        # Header com controles
        header_layout = QHBoxLayout()

        header_label = QLabel("🎤 Transcrição em Tempo Real")
        header_label.setObjectName("sectionHeader")
        header_label.setStyleSheet("""
            QLabel#sectionHeader {
                color: #ECEFF4;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background: rgba(136, 192, 208, 0.2);
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Botão de salvar
        self.save_button = QPushButton("💾 Salvar")
        self.save_button.setObjectName("saveButton")
        self.save_button.setFixedSize(80, 30)
        self.save_button.clicked.connect(self._save_transcription)
        header_layout.addWidget(self.save_button)

        # Botão de resumo
        self.summary_button = QPushButton("📋 Resumo")
        self.summary_button.setObjectName("summaryButton")
        self.summary_button.setFixedSize(80, 30)
        self.summary_button.clicked.connect(self._generate_summary)
        header_layout.addWidget(self.summary_button)

        # Botão de expandir
        self.expand_button = QPushButton("⛶")
        self.expand_button.setObjectName("expandButton")
        self.expand_button.setFixedSize(30, 30)
        self.expand_button.setToolTip("Expandir para tela cheia")
        self.expand_button.clicked.connect(self._toggle_fullscreen)
        header_layout.addWidget(self.expand_button)

        layout.addLayout(header_layout)

        # Área de transcrição
        self.transcription_area = QTextEdit()
        self.transcription_area.setObjectName("transcriptionArea")
        self.transcription_area.setReadOnly(True)
        self.transcription_area.setStyleSheet("""
            QTextEdit#transcriptionArea {
                background: rgba(46, 52, 64, 0.8);
                border: 1px solid rgba(129, 161, 193, 0.3);
                border-radius: 8px;
                color: #ECEFF4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.4;
                padding: 15px;
            }
        """)
        layout.addWidget(self.transcription_area)

        # Status da transcrição
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px; padding: 5px;")
        layout.addWidget(self.status_label)

        # Modo tela cheia (inicialmente oculto)
        self.fullscreen_mode = False

        # Inicializar sem conteúdo de exemplo
        self.clear_transcription()
    
    def start_recording(self, call_id: str):
        """Iniciar gravação de nova chamada."""
        self.current_call_id = call_id
        self.is_recording = True
        self.clear_transcription()
        self._update_status("🎤 Gravação iniciada")
        self.save_button.setEnabled(True)
        self.summary_button.setEnabled(False)

    def stop_recording(self):
        """Parar gravação."""
        self.is_recording = False
        self._update_status("⏹️ Gravação parada")
        self.save_button.setEnabled(True)
        self.summary_button.setEnabled(True)

    def _update_status(self, message: str):
        """Atualizar mensagem de status."""
        self.status_label.setText(message)

    def _save_transcription(self):
        """Salvar transcrição no BD."""
        if not self.current_call_id or not self.database_manager:
            self._update_status("❌ Erro: Não foi possível salvar")
            return

        try:
            transcription_text = self.export_transcription()

            # Salvar no BD
            success = self.database_manager.save_transcription(
                call_id=self.current_call_id,
                text=transcription_text,
                speaker="combined",
                timestamp=time.time()
            )

            if success:
                self._update_status("✅ Transcrição salva com sucesso")
                self.transcription_saved.emit(self.current_call_id)
            else:
                self._update_status("❌ Erro ao salvar transcrição")

        except Exception as e:
            self.logger.error(f"Erro ao salvar transcrição: {e}")
            self._update_status(f"❌ Erro: {str(e)}")

    def _generate_summary(self):
        """Gerar resumo da reunião."""
        if not self.current_call_id:
            self._update_status("❌ Erro: Nenhum call_id disponível")
            return

        self._update_status("🤖 Gerando resumo...")
        self.summary_requested.emit(self.current_call_id)

    def set_summary_result(self, summary: Dict[str, Any]):
        """Receber e exibir resultado do resumo."""
        try:
            summary_text = f"""
📋 RESUMO DA REUNIÃO
===================

🎯 PONTOS PRINCIPAIS:
{chr(10).join(f"• {point}" for point in summary.get('key_points', []))}

🚨 OBJEÇÕES TRATADAS:
{chr(10).join(f"• {obj.get('type', 'N/A')}: {obj.get('handled', 'Não tratado')}" for obj in summary.get('objections', []))}

📝 PRÓXIMOS PASSOS:
{chr(10).join(f"• {step.get('desc', '')} (Prazo: {step.get('due', 'N/A')})" for step in summary.get('next_steps', []))}

📊 MÉTRICAS:
• Tempo vendedor: {summary.get('metrics', {}).get('talk_time_vendor_pct', 0):.1f}%
• Tempo cliente: {summary.get('metrics', {}).get('talk_time_client_pct', 0):.1f}%
• Sentimento médio: {summary.get('metrics', {}).get('sentiment_avg', 0):.2f}
• Sinais de compra: {summary.get('metrics', {}).get('buying_signals', 0)}

Gerado em: {time.strftime('%H:%M:%S', time.localtime())}
"""

            # Adicionar resumo à transcrição
            current_text = self.transcription_area.toPlainText()
            if current_text:
                new_text = current_text + "\n\n" + "="*50 + "\n" + summary_text
            else:
                new_text = summary_text

            self.transcription_area.setText(new_text)
            self._update_status("✅ Resumo gerado com sucesso")

            # Rolar para o final
            scrollbar = self.transcription_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            self.logger.error(f"Erro ao exibir resumo: {e}")
            self._update_status(f"❌ Erro ao exibir resumo: {str(e)}")

    def _toggle_fullscreen(self):
        """Alternar entre modo normal e tela cheia."""
        self.fullscreen_mode = not self.fullscreen_mode

        if self.fullscreen_mode:
            self._enter_fullscreen_mode()
        else:
            self._exit_fullscreen_mode()

    def _enter_fullscreen_mode(self):
        """Entrar no modo tela cheia."""
        # Atualizar botão
        self.expand_button.setText("⛶")  # Mesmo ícone, mas tooltip muda
        self.expand_button.setToolTip("Voltar ao modo normal")

        # Ocultar controles desnecessários no modo tela cheia
        self.save_button.hide()
        self.summary_button.hide()

        # Expandir área de transcrição
        self.transcription_area.setMaximumHeight(10000)  # Altura máxima

        # Atualizar header
        if hasattr(self, 'header_label'):
            self.header_label.setText("📝 Transcrição Completa")

        # Emitir sinal para MainWindow abrir em tela cheia
        transcription_text = self.export_transcription()
        self.fullscreen_requested.emit(transcription_text)

    def _exit_fullscreen_mode(self):
        """Sair do modo tela cheia."""
        # Atualizar botão
        self.expand_button.setText("⛶")
        self.expand_button.setToolTip("Expandir para tela cheia")

        # Mostrar controles novamente
        self.save_button.show()
        self.summary_button.show()

        # Restaurar altura normal
        self.transcription_area.setMaximumHeight(200)

        # Atualizar header
        if hasattr(self, 'header_label'):
            self.header_label.setText("🎤 Transcrição em Tempo Real")

    def enter_fullscreen_mode(self):
        """Método público para entrar em modo tela cheia."""
        if not self.fullscreen_mode:
            self._enter_fullscreen_mode()

    def exit_fullscreen_mode(self):
        """Método público para sair do modo tela cheia."""
        if self.fullscreen_mode:
            self._exit_fullscreen_mode()

    def is_fullscreen(self) -> bool:
        """Verificar se está em modo tela cheia."""
        return self.fullscreen_mode
    
    @pyqtSlot(str, str)
    def add_transcription(self, text: str, speaker_id: str):
        """Adicionar nova transcrição."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Determinar cor e ícone do falante
        if speaker_id == "vendor":
            color = "#88C0D0"
            icon = "🔵"
            name = "Vendedor"
        else:
            color = "#D08770" 
            icon = "🟠"
            name = "Cliente"
        
        # Criar HTML para nova transcrição
        html_content = f"""
        <div style='color: {color}; font-weight: bold; margin-bottom: 10px; margin-top: 15px;'>
            [{timestamp}] {icon} {name}
        </div>
        <div style='color: #ECEFF4; margin-bottom: 15px; margin-left: 20px;'>
            {text}
        </div>
        """
        
        # Adicionar ao final
        cursor = self.transcription_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_content)
        
        # Scroll para o final
        self.transcription_area.ensureCursorVisible()
    
    def clear_transcription(self):
        """Limpar toda a transcrição."""
        self.transcription_area.clear()
    
    def export_transcription(self) -> str:
        """Exportar transcrição como texto."""
        return self.transcription_area.toPlainText()

    def add_transcription_chunk(self, html_content: str):
        """Adicionar chunk de HTML à transcrição."""
        cursor = self.transcription_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html_content)
        self.transcription_area.ensureCursorVisible()

    def _connect_signals(self):
        """Conectar sinais do serviço de transcrição."""
        if self.transcription_service:
            self.transcription_service.transcript_chunk_ready.connect(self._on_transcript_chunk)
            self.transcription_service.transcription_started.connect(self._on_transcription_started)
            self.transcription_service.transcription_stopped.connect(self._on_transcription_stopped)
            self.transcription_service.error_occurred.connect(self._on_transcription_error)

    @pyqtSlot(object)
    def _on_transcript_chunk(self, chunk):
        """Receber chunk de transcrição."""
        try:
            # Determinar cor baseada na fonte
            if chunk.source == "mic":
                speaker = "👤 Vendedor"
                color = "#88C0D0"  # Azul claro
            else:
                speaker = "🎯 Cliente"
                color = "#A3BE8C"  # Verde claro

            # Formatar timestamp
            import time
            timestamp = time.strftime("%H:%M:%S", time.localtime(chunk.ts_start_ms / 1000))

            # Criar HTML para o chunk
            html_content = f"""
            <div style="margin: 5px 0;">
                <span style="color: {color}; font-weight: bold;">[{timestamp}] {speaker}:</span>
                <span style="color: #ECEFF4;"> {chunk.text}</span>
                <span style="color: #888888; font-size: 10px;"> (conf: {chunk.confidence:.2f})</span>
            </div>
            """

            # Adicionar à transcrição
            self.add_transcription_chunk(html_content)

        except Exception as e:
            print(f"Erro ao processar chunk de transcrição: {e}")

    @pyqtSlot(str)
    def _on_transcription_started(self, call_id):
        """Transcrição iniciada."""
        self.clear_transcription()
        start_html = f"""
        <div style="margin: 10px 0; padding: 10px; background: rgba(163, 190, 140, 0.2); border-radius: 5px;">
            <span style="color: #A3BE8C; font-weight: bold;">🎤 Transcrição iniciada - Call ID: {call_id}</span>
        </div>
        """
        self.add_transcription_chunk(start_html)

    @pyqtSlot(str)
    def _on_transcription_stopped(self, call_id):
        """Transcrição parada."""
        stop_html = f"""
        <div style="margin: 10px 0; padding: 10px; background: rgba(191, 97, 106, 0.2); border-radius: 5px;">
            <span style="color: #BF616A; font-weight: bold;">⏹️ Transcrição parada - Call ID: {call_id}</span>
        </div>
        """
        self.add_transcription_chunk(stop_html)

    @pyqtSlot(str)
    def _on_transcription_error(self, error_msg):
        """Erro na transcrição."""
        error_html = f"""
        <div style="margin: 10px 0; padding: 10px; background: rgba(235, 203, 139, 0.2); border-radius: 5px;">
            <span style="color: #EBCB8B; font-weight: bold;">⚠️ Erro na transcrição: {error_msg}</span>
        </div>
        """
        self.add_transcription_chunk(error_html)

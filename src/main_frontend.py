"""
PitchAI - Frontend Integrado com Backend Completo
===============================================

Integração completa do frontend com backend real, incluindo:
- Banco de dados SQLite
- Sistema de eventos
- Captura de áudio
- Processamento de IA
- Mentor Engine
"""

import sys
import os
import uuid
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))  # Para imports absolutos

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal, QTimer

# Tentar imports com fallback
try:
    # Tentativa 1: Import relativo (quando executado como módulo)
    from ui.main_window import MainWindow
    from core.config import create_config
    from core.application import PitchAIApp
except ImportError:
    try:
        # Tentativa 2: Import absoluto (quando executado como script)
        from src.ui.main_window import MainWindow
        from src.core.config import create_config
        from src.core.application import PitchAIApp
    except ImportError:
        # Tentativa 3: Import direto (último recurso)
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.ui.main_window import MainWindow
        from src.core.config import create_config
        from src.core.application import PitchAIApp


class IntegratedPitchAI(QObject):
    """Aplicação PitchAI integrada com backend completo."""
    
    def __init__(self):
        super().__init__()
        
        # Configuração
        self.config = create_config()
        
        # Aplicação principal
        self.pitch_app = None
        self.main_window = None
        
        # Estado
        self.is_initialized = False
    
    def initialize(self):
        """Inicializar aplicação completa."""
        try:
            print("🎨 Inicializando PitchAI Frontend + Backend Completo...")
            
            # Inicializar aplicação principal
            self.pitch_app = PitchAIApp(self.config)
            self.pitch_app.initialize()
            
            # Criar interface mantendo design original
            self.main_window = MainWindow(self.config, self.pitch_app)
            
            # Conectar sinais do backend para a UI
            self._connect_backend_signals()
            
            self.is_initialized = True
            print("✅ PitchAI Frontend + Backend inicializado com sucesso!")
            print("🚀 Interface PitchAI aberta!")
            print("✨ PitchAI funcionando com IA integrada!")
            print("🎤 Pronto para gravação e análise em tempo real")
            print("💾 Banco de dados SQLite ativo")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar PitchAI: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _connect_backend_signals(self):
        """Conectar sinais do backend para a UI."""
        if not self.pitch_app or not self.main_window:
            return

        # Usar o IntegrationController se disponível
        if hasattr(self.main_window, 'integration_controller') and self.main_window.integration_controller:
            integration_controller = self.main_window.integration_controller

            # Conectar sinais do IntegrationController para os widgets
            if hasattr(self.main_window, 'analysis_widget') and self.main_window.analysis_widget:
                analysis_widget = self.main_window.analysis_widget

                # Conectar transcrição
                integration_controller.transcription_updated.connect(
                    lambda chunk: self._on_transcript_chunk(chunk, analysis_widget)
                )

                # Conectar sentimento
                integration_controller.sentiment_updated.connect(
                    lambda sentiment: self._on_sentiment_updated(sentiment, analysis_widget)
                )

                # Conectar resumo
                integration_controller.summary_generated.connect(
                    lambda summary: self._on_summary_generated(summary, analysis_widget)
                )

                # Conectar erros
                integration_controller.error_occurred.connect(
                    lambda error: self._on_error_occurred(error, analysis_widget)
                )

                print("🔗 Sinais do IntegrationController conectados aos widgets")

        # Conectar sinais diretos do pitch_app (fallback)
        try:
            self.pitch_app.transcription_ready.connect(self._on_transcription_ready)
            self.pitch_app.sentiment_updated.connect(self._on_sentiment_updated)
            self.pitch_app.objection_detected.connect(self._on_objection_detected)
        except AttributeError:
            pass  # Sinais podem não existir

        print("🔗 Sinais do backend conectados à UI")
    
    def _on_transcription_ready(self, text: str, speaker_id: str):
        """Handler para transcrição pronta."""
        if self.main_window and hasattr(self.main_window, 'analysis_widget'):
            # Atualizar transcrição na UI
            self.main_window.analysis_widget.update_transcription(text, speaker_id)
    
    def _on_sentiment_updated(self, sentiment_data: dict):
        """Handler para atualização de sentimento."""
        if self.main_window and hasattr(self.main_window, 'analysis_widget'):
            # Atualizar sentimento na UI
            self.main_window.analysis_widget.update_sentiment(sentiment_data)
    
    def _on_objection_detected(self, objection: str, suggestions: list):
        """Handler para objeção detectada."""
        if self.main_window and hasattr(self.main_window, 'analysis_widget'):
            # Adicionar objeção na UI
            self.main_window.analysis_widget.add_objection(objection, suggestions)

    def _on_transcript_chunk(self, chunk, analysis_widget):
        """Handler para chunk de transcrição."""
        if analysis_widget and hasattr(analysis_widget, 'transcription_widget'):
            analysis_widget.transcription_widget.add_transcription_chunk(chunk)

    def _on_summary_generated(self, summary, analysis_widget):
        """Handler para resumo gerado."""
        if analysis_widget and hasattr(analysis_widget, 'transcription_widget'):
            analysis_widget.transcription_widget.set_summary_result(summary)

    def _on_error_occurred(self, error, analysis_widget):
        """Handler para erros."""
        if analysis_widget and hasattr(analysis_widget, 'status_label'):
            analysis_widget.status_label.setText(f"❌ Erro: {error}")
    
    def show(self):
        """Mostrar interface."""
        if self.main_window:
            self.main_window.show()
    
    def shutdown(self):
        """Encerrar aplicação."""
        print("🔄 Encerrando PitchAI...")
        
        if self.pitch_app:
            self.pitch_app.shutdown()
        
        print("✅ PitchAI encerrado com sucesso")


def main():
    """Função principal da aplicação integrada."""
    
    # Configurar aplicação Qt
    QCoreApplication.setOrganizationName("PitchAI")
    QCoreApplication.setOrganizationDomain("pitchai.com")
    QCoreApplication.setApplicationName("PitchAI")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Criar aplicação Qt
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(True)
    
    try:
        # Inicializar aplicação integrada
        pitch_ai = IntegratedPitchAI()
        
        if not pitch_ai.initialize():
            print("❌ Falha na inicialização")
            sys.exit(1)
        
        # Mostrar interface
        pitch_ai.show()
        
        # Executar aplicação
        sys.exit(qt_app.exec())
        
    except Exception as e:
        print(f"❌ Erro ao inicializar PitchAI: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()

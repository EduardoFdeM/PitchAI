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

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal, QTimer
from ui.main_window import MainWindow
from core.config import create_config
from core.application import PitchAIApp


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
        
        # Conectar sinais de transcrição
        self.pitch_app.transcription_ready.connect(self._on_transcription_ready)
        
        # Conectar sinais de sentimento
        self.pitch_app.sentiment_updated.connect(self._on_sentiment_updated)
        
        # Conectar sinais de objeções
        self.pitch_app.objection_detected.connect(self._on_objection_detected)
        
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

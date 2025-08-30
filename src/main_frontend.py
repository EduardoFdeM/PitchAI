"""
PitchAI - Frontend Principal
============================

Versão frontend-only que usa os widgets modulares existentes
com dados mockados para desenvolvimento e demonstração.
"""

import sys
import random
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal, QTimer

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow


class MockConfig:
    """Configuração mockada para frontend-only."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.ui = MockUIConfig()

class MockUIConfig:
    """Configurações de UI mockadas."""
    
    def __init__(self):
        self.window_width = 1400
        self.window_height = 900
        self.theme = "glassmorphism"


class FrontendApp(QObject):
    """Aplicação frontend-only com dados simulados."""
    
    # Sinais para comunicação com UI (mesmo que o backend real)
    transcription_ready = pyqtSignal(str, str)  # texto, speaker_id
    sentiment_updated = pyqtSignal(dict)        # métricas de sentimento
    objection_detected = pyqtSignal(str, list) # objeção, sugestões
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.main_window = None
        self.is_recording = False
        
        # Dados simulados
        self.transcript_lines = [
            ("Olá! Obrigado por aceitar nossa reunião hoje.", "vendor"),
            ("Como posso ajudá-lo com nossa solução de CRM?", "vendor"),
            ("Estamos avaliando opções, mas estou preocupado com o preço...", "client"),
            ("Entendo perfeitamente. Vamos falar sobre o ROI que nossos clientes têm visto.", "vendor"),
            ("Posso mostrar um case de sucesso de uma empresa similar à sua.", "vendor"),
            ("Isso parece interessante. Quanto tempo leva para implementar?", "client"),
            ("Normalmente entre 2-4 semanas, dependendo da complexidade.", "vendor"),
            ("E qual é o custo de manutenção mensal?", "client"),
            ("Vou detalhar nossa estrutura de pricing para você...", "vendor")
        ]
        self.current_line = 0
        
        # Timers para simulação
        self.transcript_timer = QTimer()
        self.transcript_timer.timeout.connect(self._simulate_transcription)
        
        self.sentiment_timer = QTimer()
        self.sentiment_timer.timeout.connect(self._simulate_sentiment)
        
        self.objection_timer = QTimer()
        self.objection_timer.timeout.connect(self._simulate_objections)
    
    def initialize(self):
        """Inicializar aplicação frontend."""
        print("🎨 Inicializando PitchAI Frontend...")
        
        # Criar janela principal
        self.main_window = MainWindow(self.config, self)
        
        print("✅ Frontend inicializado com sucesso!")
        return True
    
    def show(self):
        """Mostrar janela principal."""
        if self.main_window:
            self.main_window.show()
            print("🚀 Interface PitchAI aberta!")
    
    def start_recording(self):
        """Iniciar 'gravação' (simulação)."""
        if not self.is_recording:
            self.is_recording = True
            print("🎤 Iniciando simulação de gravação...")
            
            # Iniciar timers de simulação
            self.transcript_timer.start(4000)  # A cada 4 segundos
            self.sentiment_timer.start(3000)   # A cada 3 segundos
            self.objection_timer.start(8000)   # A cada 8 segundos
    
    def stop_recording(self):
        """Parar 'gravação' (simulação)."""
        if self.is_recording:
            self.is_recording = False
            print("⏹️ Parando simulação...")
            
            # Parar timers
            self.transcript_timer.stop()
            self.sentiment_timer.stop()
            self.objection_timer.stop()
    
    def _simulate_transcription(self):
        """Simular nova transcrição."""
        if self.current_line < len(self.transcript_lines):
            text, speaker = self.transcript_lines[self.current_line]
            self.transcription_ready.emit(text, speaker)
            self.current_line += 1
        else:
            # Reiniciar ciclo
            self.current_line = 0
    
    def _simulate_sentiment(self):
        """Simular atualização de sentimento."""
        sentiment_data = {
            'sentiment': random.uniform(0.2, 0.9),
            'engagement': random.uniform(0.6, 0.95),
            'confidence': random.uniform(0.7, 0.98),
            'emotion': random.choice(['positive', 'neutral', 'concerned', 'excited'])
        }
        self.sentiment_updated.emit(sentiment_data)
    
    def _simulate_objections(self):
        """Simular detecção de objeções."""
        objections = [
            ("preço", [
                {
                    "text": "Entendo sua preocupação com o investimento. Vamos falar sobre o ROI que nossos clientes têm visto nos primeiros 6 meses...",
                    "confidence": 0.92,
                    "category": "Objeção de Preço"
                },
                {
                    "text": "Posso mostrar um case de sucesso de uma empresa similar à sua que reduziu custos em 30%...",
                    "confidence": 0.87,
                    "category": "Prova Social"
                }
            ]),
            ("timing", [
                {
                    "text": "Que bom que você está sendo criterioso. Posso te ajudar com informações adicionais para facilitar sua análise?",
                    "confidence": 0.89,
                    "category": "Objeção de Timing"
                }
            ]),
            ("concorrente", [
                {
                    "text": "Ótimo que estejam avaliando opções! Posso destacar nossos diferenciais únicos que agregam valor específico para seu cenário?",
                    "confidence": 0.85,
                    "category": "Concorrência"
                }
            ])
        ]
        
        # Simular detecção ocasional
        if random.random() < 0.4:  # 40% chance
            objection, suggestions = random.choice(objections)
            self.objection_detected.emit(objection, suggestions)
    
    def shutdown(self):
        """Encerrar aplicação."""
        print("🔄 Encerrando PitchAI Frontend...")
        self.stop_recording()


def main():
    """Função principal do frontend."""
    
    # Configurar aplicação Qt
    QCoreApplication.setOrganizationName("PitchAI")
    QCoreApplication.setOrganizationDomain("pitchai.com")
    QCoreApplication.setApplicationName("PitchAI Frontend")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Criar aplicação Qt
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(True)
    
    # Configuração mockada
    config = MockConfig()
    
    try:
        # Inicializar frontend
        frontend_app = FrontendApp(config)
        
        if not frontend_app.initialize():
            print("❌ Erro na inicialização")
            sys.exit(1)
        
        frontend_app.show()
        
        print("")
        print("✨ PitchAI Frontend funcionando!")
        print("👋 Use os controles na interface para iniciar a simulação")
        print("📊 Clique em 'Iniciar Gravação' para ver dados em tempo real")
        print("")
        
        # Executar aplicação
        sys.exit(qt_app.exec())
        
    except Exception as e:
        print(f"❌ Erro ao inicializar PitchAI Frontend: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
PitchAI - Ponto de Entrada Principal
==================================

Inicializa a aplicação PitchAI com interface PyQt6
e pipeline de IA na NPU.
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from core.application import PitchAIApp
from core.config import create_config


def main():
    """Função principal da aplicação."""
    
    # Configurar aplicação Qt
    QCoreApplication.setOrganizationName("PitchAI")
    QCoreApplication.setOrganizationDomain("pitchai.com")
    QCoreApplication.setApplicationName("PitchAI")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Criar aplicação Qt
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(True)
    
    # Carregar configurações
    config = create_config()
    
    try:
        # Inicializar PitchAI
        pitch_app = PitchAIApp(config)
        pitch_app.initialize()
        pitch_app.show()
        
        # Executar aplicação
        sys.exit(qt_app.exec())
        
    except Exception as e:
        print(f"❌ Erro ao inicializar PitchAI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

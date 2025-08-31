#!/usr/bin/env python3
"""
Teste de Arrastar Janela - PitchAI
================================

Script simples para testar se a janela principal pode ser arrastada
e se o ícone flutuante funciona corretamente.
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from core.application import PitchAIApp
from core.config import create_config

def test_window_dragging():
    """Testar funcionalidade de arrastar janela."""
    print("🧪 Testando funcionalidade de arrastar janela...")
    
    # Configurar aplicação Qt
    QCoreApplication.setOrganizationName("PitchAI")
    QCoreApplication.setOrganizationDomain("pitchai.com")
    QCoreApplication.setApplicationName("PitchAI")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Criar aplicação Qt
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(True)
    
    try:
        # Carregar configurações
        config = create_config()
        
        # Inicializar PitchAI
        pitch_app = PitchAIApp(config)
        pitch_app.initialize()
        pitch_app.show()
        
        print("✅ Janela principal criada com sucesso!")
        print("📋 Instruções de teste:")
        print("   1. Clique e arraste a barra de título para mover a janela")
        print("   2. Clique e arraste qualquer lugar da janela para movê-la")
        print("   3. Clique no botão '−' para minimizar para ícone flutuante")
        print("   4. Arraste o ícone flutuante para qualquer lugar")
        print("   5. Clique no ícone flutuante para restaurar a janela")
        print("   6. Feche a aplicação para sair")
        
        # Executar aplicação
        sys.exit(qt_app.exec())
        
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_window_dragging()

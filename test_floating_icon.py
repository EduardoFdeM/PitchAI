#!/usr/bin/env python3
"""
Teste do Ícone Flutuante - PitchAI
================================

Teste específico para verificar se o ícone flutuante pode ser arrastado.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.main_window import FloatingIcon

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teste Ícone Flutuante")
        self.setGeometry(100, 100, 400, 300)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Botão para criar ícone flutuante
        self.create_icon_btn = QPushButton("Criar Ícone Flutuante")
        self.create_icon_btn.clicked.connect(self.create_floating_icon)
        layout.addWidget(self.create_icon_btn)
        
        # Botão para minimizar
        self.minimize_btn = QPushButton("Minimizar Janela")
        self.minimize_btn.clicked.connect(self.hide)
        layout.addWidget(self.minimize_btn)
        
        self.floating_icon = None
    
    def create_floating_icon(self):
        """Criar ícone flutuante de teste."""
        if not self.floating_icon:
            self.floating_icon = FloatingIcon()
            self.floating_icon.restore_requested.connect(self.restore_window)
            self.floating_icon.show()
            print("✅ Ícone flutuante criado!")
            print("📋 Instruções:")
            print("   - Clique e arraste o ícone para movê-lo")
            print("   - Clique simples no ícone para restaurar a janela")
        else:
            print("⚠️ Ícone flutuante já existe!")
    
    def restore_window(self):
        """Restaurar janela principal."""
        self.show()
        self.raise_()
        self.activateWindow()
        if self.floating_icon:
            self.floating_icon.hide()
            self.floating_icon.deleteLater()
            self.floating_icon = None
        print("✅ Janela restaurada!")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("🧪 Teste do Ícone Flutuante")
    print("📋 Instruções:")
    print("   1. Clique em 'Criar Ícone Flutuante'")
    print("   2. Arraste o ícone para qualquer lugar")
    print("   3. Clique no ícone para restaurar")
    print("   4. Use 'Minimizar Janela' para testar minimização")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script simples para executar o PitchAI
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    try:
        from main_frontend import main
        main()
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Certifique-se de que todas as dependências estão instaladas:")
        print("pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Erro ao executar PitchAI: {e}")
        import traceback
        traceback.print_exc()

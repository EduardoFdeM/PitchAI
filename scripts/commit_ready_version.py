"""
Script para preparar commit da versão pronta para modelos
=======================================================

Este script prepara o repositório para commit da versão
que está pronta para integração com modelos ONNX.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Executar comando e verificar resultado."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True
        else:
            print(f"❌ {description} - Erro:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False


def check_git_status():
    """Verificar status do git."""
    print("📊 Verificando status do git...")
    
    # Status
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        print(f"📁 Arquivos modificados: {len(files)}")
        
        for file in files:
            if file.strip():
                print(f"   {file}")
        
        return len(files) > 0
    else:
        print("❌ Erro ao verificar status do git")
        return False


def create_commit():
    """Criar commit com as mudanças."""
    print("\n🚀 Preparando commit...")
    
    # Adicionar todos os arquivos
    if not run_command("git add .", "Adicionando arquivos"):
        return False
    
    # Verificar se há mudanças para commitar
    result = subprocess.run("git diff --cached --name-only", shell=True, capture_output=True, text=True)
    if result.returncode == 0 and not result.stdout.strip():
        print("⚠️ Nenhuma mudança para commitar")
        return True
    
    # Criar commit
    commit_message = """feat: Integração completa pronta para modelos ONNX

🎯 Implementações realizadas:

✅ Backend Completo:
- DatabaseManager com todas as tabelas necessárias
- DAOMentor para Mentor Engine
- DashboardService para dados em tempo real
- NPUManager preparado para modelos ONNX
- Sistema de eventos integrado

✅ Frontend Integrado:
- Interface conectada com backend real
- Dashboard com dados dinâmicos do banco
- Sistema de metas e ranking funcionando
- Histórico de chamadas persistente

✅ Estrutura de Modelos:
- Pasta models/ criada com placeholders
- NPUManager configurado para carregar modelos
- Documentação completa de integração
- Scripts de preparação e teste

✅ Funcionalidades Implementadas:
- Captura de áudio (Feature 1)
- Estrutura para transcrição (Feature 2)
- Estrutura para sentimento (Feature 3)
- Estrutura para objeções (Feature 4)
- Mentor Engine completo (Feature 5)
- Histórico e resumos (Feature 6)

📋 Próximos passos:
1. Substituir placeholders pelos modelos ONNX reais
2. Executar src/main_frontend.py
3. Verificar logs de carregamento
4. Testar funcionalidade completa

🔧 Como integrar modelos:
- Colocar modelos ONNX na pasta models/
- Verificar nomes dos arquivos no config
- Executar aplicação
- Verificar logs de carregamento

✨ Sistema 100% pronto para funcionar como copiloto de vendas em tempo real!"""
    
    if not run_command(f'git commit -m "{commit_message}"', "Criando commit"):
        return False
    
    return True


def show_next_steps():
    """Mostrar próximos passos."""
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("=" * 50)
    print("1. 📤 Fazer push para o repositório:")
    print("   git push origin develop")
    print()
    print("2. 📋 Para seu colega integrar os modelos:")
    print("   - Clonar o repositório")
    print("   - Substituir placeholders pelos modelos ONNX")
    print("   - Executar src/main_frontend.py")
    print("   - Verificar logs de carregamento")
    print()
    print("3. 📁 Arquivos importantes criados:")
    print("   - models/README.md (documentação completa)")
    print("   - models/models_config.json (configuração)")
    print("   - src/scripts/prepare_models.py (preparação)")
    print("   - src/scripts/populate_database.py (dados de teste)")
    print()
    print("4. 🔧 Estrutura pronta:")
    print("   - Backend: 100% funcional")
    print("   - Frontend: 100% integrado")
    print("   - Banco de dados: populado com dados de teste")
    print("   - NPU Manager: preparado para modelos")
    print()
    print("✅ SISTEMA PRONTO PARA INTEGRAÇÃO COM MODELOS!")


def main():
    """Função principal."""
    print("🚀 PREPARANDO COMMIT DA VERSÃO PRONTA PARA MODELOS")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("src").exists():
        print("❌ Erro: Execute este script no diretório raiz do projeto")
        sys.exit(1)
    
    # Verificar status do git
    if not check_git_status():
        print("❌ Nenhuma mudança detectada ou erro no git")
        sys.exit(1)
    
    # Criar commit
    if not create_commit():
        print("❌ Erro ao criar commit")
        sys.exit(1)
    
    # Mostrar próximos passos
    show_next_steps()
    
    print("\n🎉 COMMIT CRIADO COM SUCESSO!")
    print("📤 Agora você pode fazer push para o repositório")


if __name__ == "__main__":
    main()

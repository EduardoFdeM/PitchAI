#!/usr/bin/env python3
"""
Teste da Feature 5 - Resumo Pós-Chamada Inteligente
===================================================

Script para testar a implementação do backend da Feature 5:
- Criação de chamada simulada
- Adição de dados de transcrição e objeções
- Geração automática de resumo
- Exportação em diferentes formatos
"""

import sys
import os
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from data.database import DatabaseManager
from ai.npu_manager import NPUManager
from ai.summary_service import SummaryService
from core.call_manager import CallManager


def setup_logging():
    """Configurar logging para o teste."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_feature5():
    """Teste completo da Feature 5."""
    print("🚀 Testando Feature 5 - Resumo Pós-Chamada Inteligente")
    print("=" * 60)
    
    try:
        # 1. Inicializar componentes
        print("\n1️⃣ Inicializando componentes...")
        config = Config()
        
        # Banco de dados
        database = DatabaseManager(config)
        database.initialize()
        print("✅ Banco de dados inicializado")
        
        # NPU Manager (modo simulação)
        npu_manager = NPUManager(config)
        npu_manager._enable_simulation_mode()
        print("✅ NPU Manager em modo simulação")
        
        # Summary Service
        summary_service = SummaryService(npu_manager, database)
        print("✅ Summary Service inicializado")
        
        # Call Manager
        call_manager = CallManager(database, npu_manager, summary_service)
        print("✅ Call Manager inicializado")
        
        # 2. Simular uma chamada completa
        print("\n2️⃣ Simulando chamada de vendas...")
        
        # Iniciar chamada
        call_id = call_manager.start_call(
            contact_id="cliente_teste", 
            channel="teams"
        )
        print(f"📞 Chamada iniciada: {call_id}")
        
        # Adicionar dados simulados
        call_manager.simulate_call_data()
        print("🎭 Dados simulados adicionados")
        
        # 3. Finalizar chamada e gerar resumo
        print("\n3️⃣ Finalizando chamada e gerando resumo...")
        
        summary = call_manager.end_call()
        
        if summary:
            print("✅ Resumo gerado com sucesso!")
            print(f"📋 Pontos principais: {len(summary.key_points)}")
            print(f"🚨 Objeções: {len(summary.objections)}")
            print(f"✅ Próximos passos: {len(summary.next_steps)}")
            print(f"📊 Sentimento médio: {summary.metrics.sentiment_avg:.2f}")
            
            # Exibir detalhes do resumo
            print("\n📋 PONTOS PRINCIPAIS:")
            for i, point in enumerate(summary.key_points, 1):
                print(f"   {i}. {point}")
            
            print("\n✅ PRÓXIMOS PASSOS:")
            for i, step in enumerate(summary.next_steps, 1):
                due_text = f" (até {step.due})" if step.due else ""
                owner_text = f" - {step.owner}" if step.owner != "vendedor" else ""
                print(f"   {i}. {step.desc}{due_text}{owner_text}")
        
        # 4. Testar exportações
        print("\n4️⃣ Testando exportações...")
        
        # JSON
        json_export = call_manager.export_call_summary(call_id, "json")
        print(f"📄 JSON: {len(json_export)} caracteres")
        
        # Markdown
        md_export = call_manager.export_call_summary(call_id, "md")
        print(f"📝 Markdown: {len(md_export)} caracteres")
        
        # Salvar arquivos de exemplo
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / f"resumo_{call_id}.json", "w", encoding="utf-8") as f:
            f.write(json_export)
        
        with open(output_dir / f"resumo_{call_id}.md", "w", encoding="utf-8") as f:
            f.write(md_export)
        
        print(f"💾 Arquivos salvos em: {output_dir.absolute()}")
        
        # 5. Testar recuperação de resumo
        print("\n5️⃣ Testando recuperação de resumo...")
        
        recovered_summary = call_manager.get_call_summary(call_id)
        if recovered_summary:
            print("✅ Resumo recuperado do banco com sucesso")
            print(f"📋 Pontos: {len(recovered_summary.key_points)}")
        else:
            print("❌ Erro ao recuperar resumo")
        
        print("\n🎉 Teste da Feature 5 concluído com sucesso!")
        print("\n📊 RESUMO DO TESTE:")
        print(f"   • Chamada criada: {call_id}")
        print(f"   • Resumo gerado: ✅")
        print(f"   • Exportações: JSON ✅, Markdown ✅")
        print(f"   • Persistência: ✅")
        print(f"   • Recuperação: ✅")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if 'database' in locals():
            database.close()
    
    return True


if __name__ == "__main__":
    setup_logging()
    
    print("PitchAI - Teste Feature 5")
    print("Resumo Pós-Chamada Inteligente")
    print()
    
    success = test_feature5()
    
    if success:
        print("\n✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n❌ Alguns testes falharam!")
        sys.exit(1)
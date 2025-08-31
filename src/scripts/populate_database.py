"""
Script para popular o banco de dados com dados de exemplo
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import create_config
from data.database import DatabaseManager
from data.dao_mentor import DAOMentor
from core.dashboard_service import DashboardService


def populate_database():
    """Popular banco de dados com dados de exemplo."""
    
    print("🗄️ Populando banco de dados com dados de exemplo...")
    
    # Inicializar componentes diretamente
    config = create_config()
    database = DatabaseManager(config)
    database.initialize()
    
    dao_mentor = DAOMentor(database.connection)
    dashboard_service = DashboardService(database, dao_mentor)
    
    try:
        # Criar vendedores de exemplo
        sellers = ["giovanna", "joao", "maria", "pedro"]
        
        for seller_id in sellers:
            # Criar XP inicial
            dao_mentor.get_seller_xp(seller_id)
            
            # Adicionar XP aleatório
            xp = random.randint(50, 500)
            dao_mentor._update_seller_xp(seller_id, xp)
            
            print(f"👤 Vendedor {seller_id} criado com {xp} XP")
        
        # Criar chamadas de exemplo
        for i in range(20):
            seller_id = random.choice(sellers)
            
            # Data aleatória nos últimos 30 dias
            days_ago = random.randint(0, 30)
            start_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            end_time = start_time + timedelta(minutes=random.randint(10, 60))
            
            call_id = f"call_{seller_id}_{start_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Inserir chamada
            database.connection.execute("""
                INSERT INTO call 
                (id, start_time, end_time, duration_seconds, channel, sentiment_avg, 
                 objection_count, opportunity_count, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id,
                start_time,
                end_time,
                int((end_time - start_time).total_seconds()),
                seller_id,
                random.uniform(0.3, 0.9),
                random.randint(0, 5),
                random.randint(0, 3),
                f"Chamada de exemplo {i+1} - {seller_id}"
            ))
            
            # 30% de chance de ser uma venda
            if random.random() < 0.3:
                units = random.randint(1, 5)
                contract_value = random.uniform(1000, 10000)
                
                dashboard_service.record_sale(
                    seller_id=seller_id,
                    call_id=call_id,
                    units=units,
                    contract_value=contract_value
                )
                
                print(f"💰 Venda registrada: {seller_id} - {units} unidades")
        
        database.connection.commit()
        
        print("✅ Banco de dados populado com sucesso!")
        print("📊 Dados criados:")
        print("   - 4 vendedores com XP variado")
        print("   - 20 chamadas de exemplo")
        print("   - Vendas aleatórias")
        print("   - Metas automáticas criadas")
        
        # Mostrar estatísticas
        print("\n📈 Estatísticas:")
        for seller_id in sellers:
            dashboard_data = dashboard_service.get_dashboard_data(seller_id)
            seller = dashboard_data['seller']
            goals = dashboard_data['goals']
            ranking = dashboard_data['ranking']
            
            print(f"   {seller['name']}:")
            print(f"     - Nível: {seller['level']}")
            print(f"     - XP: {seller['total_xp']}")
            print(f"     - Vendas: {goals['units']['current']}/{goals['units']['target']}")
            print(f"     - Ranking: {ranking['current_position']}° lugar")
        
    except Exception as e:
        print(f"❌ Erro ao popular banco: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        database.connection.close()


if __name__ == "__main__":
    populate_database()

#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados reais de exemplo
==============================================================

Este script insere dados de exemplo realistas para testar a integração
entre frontend e backend.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import DatabaseManager

def populate_real_data():
    """Popular banco com dados reais de exemplo."""
    
    # Conectar ao banco
    db_path = "data/pitchai.db"
    db = DatabaseManager(db_path)
    
    print("🔄 Populando banco com dados reais...")
    
    try:
        # 1. Inserir vendedores
        sellers = [
            ("giovanna", "Giovanna Silva", "giovanna@techcorp.com", 1500, "senior"),
            ("joao", "João Santos", "joao@techcorp.com", 800, "pleno"),
            ("maria", "Maria Costa", "maria@techcorp.com", 1200, "senior"),
            ("pedro", "Pedro Oliveira", "pedro@techcorp.com", 400, "junior")
        ]
        
        for seller_id, name, email, xp, level in sellers:
            db.connection.execute("""
                INSERT OR REPLACE INTO sellers (id, name, email, xp, level)
                VALUES (?, ?, ?, ?, ?)
            """, (seller_id, name, email, xp, level))
        
        # 2. Inserir chamadas reais
        calls = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(20):
            call_id = str(uuid.uuid4())
            seller_id = sellers[i % len(sellers)][0]
            duration = 1800 + (i * 300)  # 30-60 minutos
            start_time = base_time + timedelta(days=i, hours=i % 8)
            end_time = start_time + timedelta(seconds=duration)
            
            calls.append({
                'id': call_id,
                'seller_id': seller_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'sentiment_avg': 0.7 + (i * 0.02),  # 0.7-1.1
                'objection_count': i % 3,
                'opportunity_count': (i % 4) + 1,
                'summary': f"Reunião com cliente {i+1} - Discussão sobre implementação de CRM",
                'action_items': "Enviar proposta|Agendar demo|Incluir case de sucesso",
                'key_topics': f"Budget R$ {50 + i*10}k|Timeline Q{i%4 + 1}|Integração com sistema legado",
                'status': 'completed'
            })
        
        for call in calls:
            db.connection.execute("""
                INSERT OR REPLACE INTO call 
                (id, seller_id, start_time, end_time, duration_seconds, sentiment_avg, 
                 objection_count, opportunity_count, summary, action_items, key_topics, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call['id'], call['seller_id'], call['start_time'], call['end_time'],
                call['duration_seconds'], call['sentiment_avg'], call['objection_count'],
                call['opportunity_count'], call['summary'], call['action_items'],
                call['key_topics'], call['status']
            ))
        
        # 3. Inserir transcrições reais
        for i, call in enumerate(calls):
            call_id = call['id']
            
            # Transcrições de exemplo
            transcriptions = [
                ("vendor", f"Olá! Obrigado por aceitar nossa reunião hoje. Como posso ajudá-lo com a solução de CRM?", "00:00:05"),
                ("client", f"Olá! Estamos avaliando opções, mas estou preocupado com o preço...", "00:00:15"),
                ("vendor", f"Entendo perfeitamente sua preocupação. Vamos falar sobre o ROI que nossos clientes têm visto...", "00:00:25"),
                ("client", f"Interessante. Como funciona a integração com nosso sistema atual?", "00:00:40"),
                ("vendor", f"Excelente pergunta! Nossa API permite integração completa...", "00:00:55")
            ]
            
            for speaker_id, text, timestamp in transcriptions:
                db.connection.execute("""
                    INSERT INTO transcription (call_id, speaker_id, text, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (call_id, speaker_id, text, timestamp))
        
        # 4. Inserir objeções reais
        objections = [
            "Preço muito alto para nosso orçamento",
            "Não temos tempo para implementação",
            "Preciso consultar minha equipe antes",
            "Já temos uma solução similar",
            "Não é prioridade no momento"
        ]
        
        for i, call in enumerate(calls):
            call_id = call['id']
            if i < len(objections):
                db.connection.execute("""
                    INSERT INTO objection (call_id, text, confidence, timestamp, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (call_id, objections[i % len(objections)], 0.85, "00:01:30", "price"))
        
        # 5. Inserir oportunidades reais
        opportunities = [
            "Crescimento da empresa planejado para Q3",
            "Problemas com sistema atual",
            "Interesse em automação",
            "Novo projeto de expansão",
            "Equipe insatisfeita com ferramentas atuais"
        ]
        
        for i, call in enumerate(calls):
            call_id = call['id']
            if i < len(opportunities):
                db.connection.execute("""
                    INSERT INTO opportunity (call_id, text, confidence, timestamp, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (call_id, opportunities[i % len(opportunities)], 0.90, "00:02:15", "growth"))
        
        # 6. Inserir vendas completadas
        for i, call in enumerate(calls[:10]):  # Primeiras 10 chamadas resultaram em vendas
            sale_id = str(uuid.uuid4())
            units = (i % 3) + 1
            contract_value = 50000 + (i * 10000)
            
            db.connection.execute("""
                INSERT INTO completed_sales (id, seller_id, call_id, units_sold, contract_value, sale_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, call['seller_id'], call['id'], units, contract_value, call['end_time']))
        
        # Commit das mudanças
        db.connection.commit()
        
        print("✅ Banco populado com sucesso!")
        print(f"📊 Dados inseridos:")
        print(f"   - {len(sellers)} vendedores")
        print(f"   - {len(calls)} chamadas")
        print(f"   - {len(calls) * 5} transcrições")
        print(f"   - {len(calls)} objeções")
        print(f"   - {len(calls)} oportunidades")
        print(f"   - {len(calls[:10])} vendas completadas")
        
    except Exception as e:
        print(f"❌ Erro ao popular banco: {e}")
        db.connection.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_real_data()

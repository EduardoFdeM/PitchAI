#!/usr/bin/env python3
"""
Rebuild Stats - Script Batch para Recalcular Estatísticas
=======================================================

Script para recalcular percentis e estatísticas de normalização:
- Features de vendedores (DISC)
- Scores de complexidade de clientes
- Percentis dinâmicos para tiers
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from analytics.stats_service import StatsService
from disc.extractor import DiscFeatureExtractor
from disc.scorer import DiscScorer
from data.dao_mentor import DAOMentor


def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/rebuild_stats.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def rebuild_seller_features(dao: DAOMentor, stats: StatsService, since_days: int = 90):
    """Recalcular estatísticas de features de vendedores."""
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 Recalculando features de vendedores (últimos {since_days} dias)")
    
    try:
        # Buscar todos os vendedores com dados
        sellers = dao.get_all_sellers()
        logger.info(f"📊 Encontrados {len(sellers)} vendedores")
        
        all_features = []
        extractor = DiscFeatureExtractor(dao)
        
        for seller in sellers:
            seller_id = seller['id']
            logger.info(f"📈 Processando vendedor: {seller_id}")
            
            try:
                # Extrair features
                features = extractor.from_calls(seller_id, since_days=since_days)
                if features:
                    all_features.extend(features)
                    logger.info(f"  ✅ {len(features)} features extraídas")
                else:
                    logger.warning(f"  ⚠️ Nenhuma feature encontrada")
                    
            except Exception as e:
                logger.error(f"  ❌ Erro ao processar {seller_id}: {e}")
        
        # Calcular estatísticas
        if all_features:
            logger.info(f"📊 Calculando estatísticas para {len(all_features)} features")
            seller_stats = stats.fit_seller_features(all_features)
            logger.info(f"✅ Estatísticas calculadas: {len(seller_stats)} features")
            
            # Mostrar algumas estatísticas
            for feature, stat in list(seller_stats.items())[:5]:
                logger.info(f"  {feature}: p25={stat['p25']:.3f}, p75={stat['p75']:.3f}, n={stat['n']}")
        else:
            logger.warning("⚠️ Nenhuma feature encontrada para calcular estatísticas")
            
    except Exception as e:
        logger.error(f"❌ Erro ao recalcular features: {e}")
        raise


def rebuild_client_complexity(dao: DAOMentor, stats: StatsService, since_days: int = 90):
    """Recalcular estatísticas de complexidade de clientes."""
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 Recalculando complexidade de clientes (últimos {since_days} dias)")
    
    try:
        # Buscar todos os clientes com dados
        clients = dao.get_all_clients()
        logger.info(f"📊 Encontrados {len(clients)} clientes")
        
        all_scores = []
        
        for client in clients:
            client_id = client['id']
            logger.info(f"📈 Processando cliente: {client_id}")
            
            try:
                # Buscar histórico de complexidade
                history = dao.get_client_history(client_id, limit=50)
                if history:
                    # Extrair scores de complexidade (se disponíveis)
                    scores = []
                    for record in history:
                        # Assumir que o score está no summary ou calcular a partir de métricas
                        if 'complexity_score' in record.get('summary', {}):
                            scores.append(record['summary']['complexity_score'])
                    
                    if scores:
                        all_scores.extend(scores)
                        logger.info(f"  ✅ {len(scores)} scores encontrados")
                    else:
                        logger.warning(f"  ⚠️ Nenhum score encontrado")
                        
            except Exception as e:
                logger.error(f"  ❌ Erro ao processar {client_id}: {e}")
        
        # Calcular estatísticas
        if all_scores:
            logger.info(f"📊 Calculando estatísticas para {len(all_scores)} scores")
            client_stats = stats.fit_client_complexity(all_scores)
            if client_stats:
                logger.info(f"✅ Estatísticas calculadas: p25={client_stats['p25']:.3f}, p75={client_stats['p75']:.3f}, n={client_stats['n']}")
        else:
            logger.warning("⚠️ Nenhum score encontrado para calcular estatísticas")
            
    except Exception as e:
        logger.error(f"❌ Erro ao recalcular complexidade: {e}")
        raise


def update_disc_profiles(dao: DAOMentor, stats: StatsService, since_days: int = 90):
    """Atualizar perfis DISC com normalização dinâmica."""
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 Atualizando perfis DISC (últimos {since_days} dias)")
    
    try:
        # Buscar todos os vendedores
        sellers = dao.get_all_sellers()
        logger.info(f"📊 Atualizando {len(sellers)} vendedores")
        
        extractor = DiscFeatureExtractor(dao)
        scorer = DiscScorer()
        
        updated_count = 0
        
        for seller in sellers:
            seller_id = seller['id']
            logger.info(f"📈 Atualizando DISC: {seller_id}")
            
            try:
                # Extrair features
                features = extractor.from_calls(seller_id, since_days=since_days)
                if not features:
                    logger.warning(f"  ⚠️ Nenhuma feature encontrada")
                    continue
                
                # Calcular scores com normalização
                scores = scorer.score_disc(features, normalizer=stats)
                
                # Salvar novo perfil
                profile_id = dao.insert_disc_profile({
                    'seller_id': seller_id,
                    'd_score': scores['D'],
                    'i_score': scores['I'],
                    's_score': scores['S'],
                    'c_score': scores['C'],
                    'confidence': scores['confidence'],
                    'sample_size': scores['n']
                })
                
                logger.info(f"  ✅ DISC atualizado: D={scores['D']:.2f}, I={scores['I']:.2f}, S={scores['S']:.2f}, C={scores['C']:.2f}")
                updated_count += 1
                
            except Exception as e:
                logger.error(f"  ❌ Erro ao atualizar {seller_id}: {e}")
        
        logger.info(f"✅ {updated_count} perfis DISC atualizados")
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar perfis DISC: {e}")
        raise


def main():
    """Executar rebuild completo."""
    logger = setup_logging()
    logger.info("🚀 Iniciando rebuild de estatísticas")
    
    try:
        # Conectar ao banco
        db_path = "data/pitchai.db"  # Ajustar conforme necessário
        conn = sqlite3.connect(db_path)
        dao = DAOMentor(conn)
        stats = StatsService(dao)
        
        # Verificar se a tabela analytics_stats existe
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analytics_stats'")
        if not cursor.fetchone():
            logger.error("❌ Tabela analytics_stats não encontrada. Execute a migração 0005_stats.sql primeiro.")
            return
        
        # Parâmetros
        since_days = 90  # Últimos 90 dias
        
        # 1. Rebuild features de vendedores
        rebuild_seller_features(dao, stats, since_days)
        
        # 2. Rebuild complexidade de clientes
        rebuild_client_complexity(dao, stats, since_days)
        
        # 3. Atualizar perfis DISC
        update_disc_profiles(dao, stats, since_days)
        
        # Resumo final
        summary = stats.get_stats_summary()
        logger.info(f"📋 Resumo final: {summary['total_features']} features, {summary['total_scores']} scores")
        
        logger.info("✅ Rebuild concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro no rebuild: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main() 
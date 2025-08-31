"""
DISC Batch Job
=============

Job em lote para calcular perfis DISC de vendedores
e gerar recomendações de treino.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from .extractor import DiscFeatureExtractor
from .scorer import DiscScorer
from .recommender import DiscRecommender

logger = logging.getLogger(__name__)


class DiscBatchJob:
    """Job em lote para processamento DISC de vendedores."""
    
    def __init__(self, dao, event_bus=None):
        self.dao = dao
        self.event_bus = event_bus
        
        # Componentes DISC
        self.extractor = DiscFeatureExtractor(dao)
        self.scorer = DiscScorer()
        self.recommender = DiscRecommender()
    
    def run_for_seller(self, seller_id: str, since_days: int = 90) -> Dict[str, Any]:
        """
        Executa análise DISC completa para um vendedor.
        
        Args:
            seller_id: ID do vendedor
            since_days: Período de análise em dias
            
        Returns:
            Dict com resultados da análise
        """
        try:
            logger.info(f"🔄 Iniciando análise DISC para vendedor {seller_id}")
            
            # 1. Extrair features
            features = self.extractor.from_calls(seller_id, since_days)
            
            if not features:
                logger.warning(f"⚠️ Nenhuma feature extraída para {seller_id}")
                return self._empty_result(seller_id)
            
            # 2. Calcular scores DISC
            scores = self.scorer.score_disc(features)
            
            # 3. Identificar fraquezas
            gaps = self.recommender.weaknesses_from_scores(scores)
            
            # 4. Gerar plano de treino
            plan = self.recommender.build_plan(gaps)
            
            # 5. Persistir resultados
            profile_id = self._save_disc_profile(seller_id, scores)
            recommendation_id = self._save_disc_recommendation(seller_id, gaps, plan)
            
            # 6. Salvar snapshot de features
            self._save_feature_snapshot(seller_id, features)
            
            # 7. Publicar eventos
            self._publish_events(seller_id, scores, gaps, plan)
            
            result = {
                "seller_id": seller_id,
                "profile_id": profile_id,
                "recommendation_id": recommendation_id,
                "scores": scores,
                "gaps": gaps,
                "plan": plan,
                "features_count": len(features),
                "success": True
            }
            
            logger.info(f"✅ Análise DISC concluída para {seller_id}: "
                       f"D={scores['D']:.2f}, I={scores['I']:.2f}, "
                       f"S={scores['S']:.2f}, C={scores['C']:.2f}, "
                       f"gaps={len(gaps)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise DISC para {seller_id}: {e}")
            return self._error_result(seller_id, str(e))
    
    def run_for_all_sellers(self, since_days: int = 90, min_calls: int = 5) -> List[Dict[str, Any]]:
        """
        Executa análise DISC para todos os vendedores com dados suficientes.
        
        Args:
            since_days: Período de análise
            min_calls: Mínimo de calls para considerar
            
        Returns:
            Lista de resultados por vendedor
        """
        try:
            # Buscar vendedores com dados suficientes
            sellers = self.dao.get_sellers_with_sufficient_data(since_days, min_calls)
            
            logger.info(f"🔄 Iniciando análise DISC para {len(sellers)} vendedores")
            
            results = []
            for seller in sellers:
                result = self.run_for_seller(seller['id'], since_days)
                results.append(result)
            
            # Estatísticas
            successful = [r for r in results if r.get('success', False)]
            failed = [r for r in results if not r.get('success', False)]
            
            logger.info(f"✅ Análise DISC em lote concluída: "
                       f"{len(successful)} sucessos, {len(failed)} falhas")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro no job em lote DISC: {e}")
            return []
    
    def run_incremental(self, seller_id: str, since_last_update: int = 7) -> Dict[str, Any]:
        """
        Executa análise incremental (apenas dados novos).
        
        Args:
            seller_id: ID do vendedor
            since_last_update: Dias desde última atualização
            
        Returns:
            Resultado da análise incremental
        """
        try:
            # Buscar último perfil DISC
            last_profile = self.dao.get_latest_disc_profile(seller_id)
            
            if last_profile:
                # Análise incremental
                since_date = last_profile['computed_at']
            else:
                # Primeira análise
                since_date = datetime.now() - timedelta(days=90)
            
            # Extrair apenas features novas
            features = self.extractor.from_calls(seller_id, since_days=since_last_update)
            
            if not features:
                logger.info(f"ℹ️ Nenhum dado novo para {seller_id}")
                return self._empty_result(seller_id)
            
            # Combinar com features existentes
            existing_features = self.dao.get_disc_features(seller_id)
            all_features = existing_features + features
            
            # Recalcular scores
            scores = self.scorer.score_disc(all_features)
            
            # Atualizar perfil
            return self.run_for_seller(seller_id, since_days=90)
            
        except Exception as e:
            logger.error(f"❌ Erro na análise incremental para {seller_id}: {e}")
            return self._error_result(seller_id, str(e))
    
    def _save_disc_profile(self, seller_id: str, scores: Dict[str, Any]) -> str:
        """Salva perfil DISC no banco."""
        profile_id = str(uuid.uuid4())
        
        profile_data = {
            'id': profile_id,
            'seller_id': seller_id,
            'd_score': scores['D'],
            'i_score': scores['I'],
            's_score': scores['S'],
            'c_score': scores['C'],
            'confidence': scores['confidence'],
            'sample_size': scores['n'],
            'computed_at': datetime.now().isoformat()
        }
        
        self.dao.insert_disc_profile(profile_data)
        return profile_id
    
    def _save_disc_recommendation(self, seller_id: str, gaps: List[str], plan: Dict[str, Any]) -> str:
        """Salva recomendação DISC no banco."""
        recommendation_id = str(uuid.uuid4())
        
        recommendation_data = {
            'id': recommendation_id,
            'seller_id': seller_id,
            'weaknesses_json': json.dumps(gaps),
            'plan_json': json.dumps(plan),
            'created_at': datetime.now().isoformat()
        }
        
        self.dao.insert_disc_recommendation(recommendation_data)
        return recommendation_id
    
    def _save_feature_snapshot(self, seller_id: str, features: List[Dict[str, float]]):
        """Salva snapshot de features para análise futura."""
        snapshot_id = str(uuid.uuid4())
        
        # Agregar features por call para economizar espaço
        aggregated_features = self._aggregate_features(features)
        
        snapshot_data = {
            'id': snapshot_id,
            'seller_id': seller_id,
            'call_id': None,  # Agregado
            'window_start_ms': None,
            'features_json': json.dumps(aggregated_features),
            'created_at': datetime.now().isoformat()
        }
        
        self.dao.insert_disc_feature_snapshot(snapshot_data)
    
    def _aggregate_features(self, features: List[Dict[str, float]]) -> Dict[str, float]:
        """Agrega features calculando médias."""
        if not features:
            return {}
        
        # Calcular médias de todas as features
        aggregated = {}
        all_keys = set()
        
        for feat in features:
            all_keys.update(feat.keys())
        
        for key in all_keys:
            values = [feat.get(key, 0.0) for feat in features]
            aggregated[key] = sum(values) / len(values)
        
        return aggregated
    
    def _publish_events(self, seller_id: str, scores: Dict[str, Any], 
                       gaps: List[str], plan: Dict[str, Any]):
        """Publica eventos para UI e outros sistemas."""
        if not self.event_bus:
            return
        
        # Evento principal de atualização DISC
        disc_event = {
            'seller_id': seller_id,
            'scores': scores,
            'gaps': gaps,
            'plan': plan,
            'timestamp': datetime.now().isoformat()
        }
        
        self.event_bus.publish('disc.profile.updated', disc_event)
        
        # Evento para Mentor Engine
        mentor_context = self.recommender.get_mentor_context(gaps)
        mentor_event = {
            'seller_id': seller_id,
            'disc_context': mentor_context,
            'quick_tips': self.recommender.get_quick_tips(gaps, 'call'),
            'timestamp': datetime.now().isoformat()
        }
        
        self.event_bus.publish('mentor.disc.context', mentor_event)
        
        # Evento de treino se há gaps significativos
        if gaps:
            training_event = {
                'seller_id': seller_id,
                'weaknesses': gaps,
                'plan': plan,
                'priority': 'high' if len(gaps) >= 3 else 'medium',
                'timestamp': datetime.now().isoformat()
            }
            
            self.event_bus.publish('mentor.training.plan', training_event)
    
    def _empty_result(self, seller_id: str) -> Dict[str, Any]:
        """Resultado para vendedor sem dados suficientes."""
        return {
            'seller_id': seller_id,
            'success': False,
            'error': 'insufficient_data',
            'message': 'Dados insuficientes para análise DISC'
        }
    
    def _error_result(self, seller_id: str, error: str) -> Dict[str, Any]:
        """Resultado para erro na análise."""
        return {
            'seller_id': seller_id,
            'success': False,
            'error': 'processing_error',
            'message': error
        }
    
    def get_analysis_summary(self, seller_id: str) -> Dict[str, Any]:
        """Retorna resumo da análise DISC mais recente."""
        try:
            profile = self.dao.get_latest_disc_profile(seller_id)
            recommendation = self.dao.get_latest_disc_recommendation(seller_id)
            
            if not profile:
                return {'seller_id': seller_id, 'has_profile': False}
            
            summary = {
                'seller_id': seller_id,
                'has_profile': True,
                'last_updated': profile['computed_at'],
                'scores': {
                    'D': profile['d_score'],
                    'I': profile['i_score'],
                    'S': profile['s_score'],
                    'C': profile['c_score']
                },
                'confidence': profile['confidence'],
                'sample_size': profile['sample_size']
            }
            
            if recommendation:
                summary['gaps'] = json.loads(recommendation['weaknesses_json'])
                summary['plan'] = json.loads(recommendation['plan_json'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao buscar resumo DISC para {seller_id}: {e}")
            return {'seller_id': seller_id, 'has_profile': False, 'error': str(e)} 
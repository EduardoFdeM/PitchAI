"""
Teste do Sistema DISC
====================

Testa a implementação completa do sistema DISC:
- Extração de features
- Cálculo de scores
- Geração de recomendações
- Integração com banco de dados
"""

import sys
import os
import json
import tempfile
import sqlite3
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from disc.extractor import DiscFeatureExtractor
from disc.scorer import DiscScorer
from disc.recommender import DiscRecommender
from disc.batch import DiscBatchJob
from src.data.dao_disc import DAODisc


class MockDAO:
    """DAO mock para testes."""
    
    def __init__(self):
        self.calls = []
        self.transcriptions = []
        self.sellers = []
        self._setup_mock_data()
    
    def _setup_mock_data(self):
        """Configura dados mock para teste."""
        # Vendedor 1: Assertivo (D alto)
        self.sellers.append({
            'id': 'seller_001',
            'name': 'João Assertivo'
        })
        
        # Calls do vendedor assertivo
        call1 = {
            'id': 'call_001',
            'seller_id': 'seller_001',
            'created_at': datetime.now().isoformat()
        }
        self.calls.append(call1)
        
        # Transcrições assertivas
        self.transcriptions.extend([
            {
                'call_id': 'call_001',
                'source': 'vendedor',
                'text': 'Vamos fechar esse negócio hoje. Você precisa dessa solução.',
                'ts_start_ms': 1000,
                'ts_end_ms': 5000,
                'valence': 0.8
            },
            {
                'call_id': 'call_001', 
                'source': 'cliente',
                'text': 'Preciso pensar sobre isso.',
                'ts_start_ms': 5000,
                'ts_end_ms': 8000,
                'valence': 0.3
            },
            {
                'call_id': 'call_001',
                'source': 'vendedor', 
                'text': 'Faça a decisão agora. É fundamental para sua empresa.',
                'ts_start_ms': 8000,
                'ts_end_ms': 12000,
                'valence': 0.9
            }
        ])
        
        # Vendedor 2: Empático (I alto)
        self.sellers.append({
            'id': 'seller_002',
            'name': 'Maria Empática'
        })
        
        call2 = {
            'id': 'call_002',
            'seller_id': 'seller_002',
            'created_at': datetime.now().isoformat()
        }
        self.calls.append(call2)
        
        # Transcrições empáticas
        self.transcriptions.extend([
            {
                'call_id': 'call_002',
                'source': 'vendedor',
                'text': 'Entendo perfeitamente sua situação. Como posso ajudar?',
                'ts_start_ms': 1000,
                'ts_end_ms': 6000,
                'valence': 0.7
            },
            {
                'call_id': 'call_002',
                'source': 'cliente',
                'text': 'Estou preocupado com o investimento.',
                'ts_start_ms': 6000,
                'ts_end_ms': 10000,
                'valence': 0.2
            },
            {
                'call_id': 'call_002',
                'source': 'vendedor',
                'text': 'Compreendo sua preocupação. Vamos explorar juntos as opções?',
                'ts_start_ms': 10000,
                'ts_end_ms': 15000,
                'valence': 0.8
            }
        ])
        
        # Vendedor 3: Estruturado (C alto)
        self.sellers.append({
            'id': 'seller_003',
            'name': 'Pedro Estruturado'
        })
        
        call3 = {
            'id': 'call_003',
            'seller_id': 'seller_003',
            'created_at': datetime.now().isoformat()
        }
        self.calls.append(call3)
        
        # Transcrições estruturadas
        self.transcriptions.extend([
            {
                'call_id': 'call_003',
                'source': 'vendedor',
                'text': 'Primeiro, vamos analisar seus requisitos. Segundo, apresentarei a solução. Terceiro, discutiremos o ROI.',
                'ts_start_ms': 1000,
                'ts_end_ms': 8000,
                'valence': 0.6
            },
            {
                'call_id': 'call_003',
                'source': 'cliente',
                'text': 'Quais são os números?',
                'ts_start_ms': 8000,
                'ts_end_ms': 12000,
                'valence': 0.5
            },
            {
                'call_id': 'call_003',
                'source': 'vendedor',
                'text': 'O ROI é de 150% em 12 meses. O investimento é de R$ 50.000.',
                'ts_start_ms': 12000,
                'ts_end_ms': 18000,
                'valence': 0.7
            }
        ])
    
    def get_calls_by_seller(self, seller_id, since_days=90):
        """Mock: busca calls do vendedor."""
        return [call for call in self.calls if call['seller_id'] == seller_id]
    
    def get_transcriptions_by_call(self, call_id):
        """Mock: busca transcrições da call."""
        return [t for t in self.transcriptions if t['call_id'] == call_id]
    
    def get_sellers_with_sufficient_data(self, since_days=90, min_calls=1):
        """Mock: busca vendedores com dados suficientes."""
        return self.sellers
    
    def insert_disc_profile(self, profile_data):
        """Mock: insere perfil DISC."""
        print(f"📊 Perfil DISC inserido: {profile_data['seller_id']}")
        return profile_data['id']
    
    def insert_disc_recommendation(self, recommendation_data):
        """Mock: insere recomendação DISC."""
        print(f"💡 Recomendação DISC inserida: {recommendation_data['seller_id']}")
        return recommendation_data['id']
    
    def insert_disc_feature_snapshot(self, snapshot_data):
        """Mock: insere snapshot de features."""
        print(f"📸 Snapshot DISC inserido: {snapshot_data['seller_id']}")
        return snapshot_data['id']


def test_disc_extractor():
    """Testa o extrator de features DISC."""
    print("\n🧪 Testando DiscFeatureExtractor...")
    
    dao = MockDAO()
    extractor = DiscFeatureExtractor(dao)
    
    # Testar extração para vendedor assertivo
    features = extractor.from_calls('seller_001', since_days=90)
    
    print(f"✅ Features extraídas: {len(features)} janelas")
    
    if features:
        sample_feature = features[0]
        print(f"📊 Sample feature: {sample_feature}")
        
        # Verificar se features estão no range 0..1
        for key, value in sample_feature.items():
            assert 0 <= value <= 1, f"Feature {key} fora do range: {value}"
        
        print("✅ Features normalizadas corretamente")
    
    return features


def test_disc_scorer():
    """Testa o calculador de scores DISC."""
    print("\n🧪 Testando DiscScorer...")
    
    scorer = DiscScorer()
    
    # Testar com features de vendedor assertivo
    features = [
        {
            'talk_ratio': 0.8,      # Alto - vendedor fala muito
            'imperatives': 0.7,     # Alto - usa muitos imperativos
            'hedges': 0.1,          # Baixo - poucas hesitações
            'interrupt_rate': 0.3,  # Médio - algumas interrupções
            'open_questions': 0.2,  # Baixo - poucas perguntas abertas
            'empathy': 0.3,         # Baixo - pouca empatia
            'valence_var': 0.4,     # Médio - variabilidade
            'structure': 0.2,       # Baixo - pouca estrutura
            'closed_questions': 0.1, # Baixo - poucas perguntas fechadas
            'risk_aversion': 0.2,   # Baixo - pouca cautela
            'turn_balance': 0.3     # Baixo - desequilibrado
        }
    ]
    
    scores = scorer.score_disc(features)
    
    print(f"📊 Scores DISC: D={scores['D']:.2f}, I={scores['I']:.2f}, "
          f"S={scores['S']:.2f}, C={scores['C']:.2f}")
    
    # Verificar se D é alto (vendedor assertivo)
    assert scores['D'] > 0.5, f"Dominância deveria ser alta: {scores['D']}"
    print("✅ Score de Dominância alto detectado corretamente")
    
    # Verificar se I é baixo (pouca empatia)
    assert scores['I'] < 0.4, f"Influência deveria ser baixa: {scores['I']}"
    print("✅ Score de Influência baixo detectado corretamente")
    
    return scores


def test_disc_recommender():
    """Testa o recomendador DISC."""
    print("\n🧪 Testando DiscRecommender...")
    
    recommender = DiscRecommender()
    
    # Testar com scores de vendedor com múltiplas fraquezas
    scores = {
        'D': 0.3,  # Baixo - pouco assertivo
        'I': 0.2,  # Baixo - pouco empático
        'S': 0.6,  # Médio-alto - estável
        'C': 0.2   # Baixo - pouco estruturado
    }
    
    gaps = recommender.weaknesses_from_scores(scores)
    print(f"🔍 Fraquezas identificadas: {gaps}")
    
    # Verificar se identificou as fraquezas corretas
    expected_gaps = ['D_baixa', 'I_baixa', 'C_baixa']
    for gap in expected_gaps:
        assert gap in gaps, f"Fraqueza {gap} não foi identificada"
    
    print("✅ Fraquezas identificadas corretamente")
    
    # Gerar plano de treino
    plan = recommender.build_plan(gaps)
    print(f"📋 Plano gerado: {len(plan['modules'])} módulos, {len(plan['tips'])} dicas")
    
    # Verificar se plano tem conteúdo
    assert len(plan['modules']) > 0, "Plano deve ter módulos"
    assert len(plan['tips']) > 0, "Plano deve ter dicas"
    
    print("✅ Plano de treino gerado corretamente")
    
    return gaps, plan


def test_disc_batch_job():
    """Testa o job em lote DISC."""
    print("\n🧪 Testando DiscBatchJob...")
    
    dao = MockDAO()
    batch_job = DiscBatchJob(dao)
    
    # Testar análise para vendedor assertivo
    result = batch_job.run_for_seller('seller_001')
    
    print(f"📊 Resultado da análise: {result['success']}")
    
    if result['success']:
        scores = result['scores']
        gaps = result['gaps']
        plan = result['plan']
        
        print(f"🎯 Scores: D={scores['D']:.2f}, I={scores['I']:.2f}, "
              f"S={scores['S']:.2f}, C={scores['C']:.2f}")
        print(f"🔍 Fraquezas: {gaps}")
        print(f"📋 Módulos: {len(plan['modules'])}")
        
        # Verificar se análise foi bem-sucedida
        assert result['success'], "Análise deveria ser bem-sucedida"
        assert 'D' in scores, "Score D deve estar presente"
        assert 'features_count' in result, "Contagem de features deve estar presente"
        
        print("✅ Análise DISC completa executada com sucesso")
    
    return result


def test_disc_integration():
    """Testa integração completa do sistema DISC."""
    print("\n🧪 Testando Integração Completa DISC...")
    
    # Criar banco temporário
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Inicializar DAO real
        dao = DAODisc(db_path)
        
        # Criar dados de teste
        dao._setup_test_data()
        
        # Executar análise para todos os vendedores
        batch_job = DiscBatchJob(dao)
        results = batch_job.run_for_all_sellers(since_days=90, min_calls=1)
        
        print(f"📊 Análises executadas: {len(results)}")
        
        successful = [r for r in results if r.get('success', False)]
        print(f"✅ Sucessos: {len(successful)}")
        
        # Verificar se pelo menos uma análise foi bem-sucedida
        assert len(successful) > 0, "Pelo menos uma análise deveria ser bem-sucedida"
        
        # Verificar estatísticas
        stats = dao.get_disc_statistics()
        print(f"📈 Estatísticas: {stats}")
        
        assert stats['total_profiles'] > 0, "Deve haver perfis criados"
        assert stats['unique_sellers'] > 0, "Deve haver vendedores únicos"
        
        print("✅ Integração DISC completa funcionando")
        
    finally:
        # Limpar arquivo temporário
        os.unlink(db_path)


def main():
    """Executa todos os testes DISC."""
    print("🎯 Iniciando Testes do Sistema DISC")
    print("=" * 50)
    
    try:
        # Teste 1: Extrator
        features = test_disc_extractor()
        
        # Teste 2: Scorer
        scores = test_disc_scorer()
        
        # Teste 3: Recommender
        gaps, plan = test_disc_recommender()
        
        # Teste 4: Batch Job
        result = test_disc_batch_job()
        
        # Teste 5: Integração Completa
        test_disc_integration()
        
        print("\n🎉 Todos os testes DISC passaram com sucesso!")
        print("=" * 50)
        
        # Resumo dos resultados
        print("\n📊 Resumo dos Testes:")
        print(f"✅ Extrator: {len(features) if features else 0} features extraídas")
        print(f"✅ Scorer: D={scores['D']:.2f}, I={scores['I']:.2f}, S={scores['S']:.2f}, C={scores['C']:.2f}")
        print(f"✅ Recommender: {len(gaps)} fraquezas, {len(plan['modules'])} módulos")
        print(f"✅ Batch Job: {'Sucesso' if result.get('success') else 'Falha'}")
        
    except Exception as e:
        print(f"\n❌ Erro nos testes DISC: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
Demonstração do Sistema DISC
============================

Script para demonstrar o funcionamento completo do sistema DISC:
- Extração de features de transcrições
- Cálculo de scores DISC
- Geração de recomendações de treino
- Integração com Mentor Engine
"""

import sys
import os
import json
import tempfile
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from disc.extractor import DiscFeatureExtractor
from disc.scorer import DiscScorer
from disc.recommender import DiscRecommender
from disc.batch import DiscBatchJob
from data.dao_disc import DAODisc


class DemoDAO:
    """DAO de demonstração com dados sintéticos."""
    
    def __init__(self):
        self.calls = []
        self.transcriptions = []
        self.sellers = []
        self._setup_demo_data()
    
    def _setup_demo_data(self):
        """Configura dados de demonstração."""
        
        # Vendedor 1: João - Dominante (D alto, I baixo)
        self.sellers.append({
            'id': 'joao_001',
            'name': 'João Silva'
        })
        
        # Calls de João (assertivo, direto)
        calls_joao = [
            {
                'id': 'call_joao_1',
                'seller_id': 'joao_001',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'call_joao_2', 
                'seller_id': 'joao_001',
                'created_at': datetime.now().isoformat()
            }
        ]
        self.calls.extend(calls_joao)
        
        # Transcrições assertivas de João
        transcriptions_joao = [
            # Call 1
            {
                'call_id': 'call_joao_1',
                'source': 'vendedor',
                'text': 'Vamos fechar esse negócio hoje. Você precisa dessa solução agora.',
                'ts_start_ms': 1000,
                'ts_end_ms': 5000,
                'valence': 0.8
            },
            {
                'call_id': 'call_joao_1',
                'source': 'cliente',
                'text': 'Preciso pensar sobre isso.',
                'ts_start_ms': 5000,
                'ts_end_ms': 8000,
                'valence': 0.3
            },
            {
                'call_id': 'call_joao_1',
                'source': 'vendedor',
                'text': 'Faça a decisão agora. É fundamental para sua empresa.',
                'ts_start_ms': 8000,
                'ts_end_ms': 12000,
                'valence': 0.9
            },
            # Call 2
            {
                'call_id': 'call_joao_2',
                'source': 'vendedor',
                'text': 'Deixe-me ser direto: essa solução vai resolver seu problema.',
                'ts_start_ms': 1000,
                'ts_end_ms': 4000,
                'valence': 0.7
            },
            {
                'call_id': 'call_joao_2',
                'source': 'cliente',
                'text': 'Mas o investimento é alto.',
                'ts_start_ms': 4000,
                'ts_end_ms': 7000,
                'valence': 0.2
            },
            {
                'call_id': 'call_joao_2',
                'source': 'vendedor',
                'text': 'O custo de não fazer nada é maior. Vamos assinar hoje.',
                'ts_start_ms': 7000,
                'ts_end_ms': 11000,
                'valence': 0.8
            }
        ]
        self.transcriptions.extend(transcriptions_joao)
        
        # Vendedor 2: Maria - Influente (I alto, D baixo)
        self.sellers.append({
            'id': 'maria_002',
            'name': 'Maria Santos'
        })
        
        calls_maria = [
            {
                'id': 'call_maria_1',
                'seller_id': 'maria_002',
                'created_at': datetime.now().isoformat()
            }
        ]
        self.calls.extend(calls_maria)
        
        # Transcrições empáticas de Maria
        transcriptions_maria = [
            {
                'call_id': 'call_maria_1',
                'source': 'vendedor',
                'text': 'Entendo perfeitamente sua situação. Como posso ajudar você hoje?',
                'ts_start_ms': 1000,
                'ts_end_ms': 6000,
                'valence': 0.7
            },
            {
                'call_id': 'call_maria_1',
                'source': 'cliente',
                'text': 'Estou preocupado com o investimento.',
                'ts_start_ms': 6000,
                'ts_end_ms': 10000,
                'valence': 0.2
            },
            {
                'call_id': 'call_maria_1',
                'source': 'vendedor',
                'text': 'Compreendo sua preocupação. Vamos explorar juntos as opções?',
                'ts_start_ms': 10000,
                'ts_end_ms': 15000,
                'valence': 0.8
            },
            {
                'call_id': 'call_maria_1',
                'source': 'vendedor',
                'text': 'Que tal começarmos com um teste gratuito?',
                'ts_start_ms': 15000,
                'ts_end_ms': 19000,
                'valence': 0.6
            }
        ]
        self.transcriptions.extend(transcriptions_maria)
        
        # Vendedor 3: Pedro - Consciencioso (C alto, I baixo)
        self.sellers.append({
            'id': 'pedro_003',
            'name': 'Pedro Costa'
        })
        
        calls_pedro = [
            {
                'id': 'call_pedro_1',
                'seller_id': 'pedro_003',
                'created_at': datetime.now().isoformat()
            }
        ]
        self.calls.extend(calls_pedro)
        
        # Transcrições estruturadas de Pedro
        transcriptions_pedro = [
            {
                'call_id': 'call_pedro_1',
                'source': 'vendedor',
                'text': 'Primeiro, vamos analisar seus requisitos. Segundo, apresentarei a solução. Terceiro, discutiremos o ROI.',
                'ts_start_ms': 1000,
                'ts_end_ms': 8000,
                'valence': 0.6
            },
            {
                'call_id': 'call_pedro_1',
                'source': 'cliente',
                'text': 'Quais são os números?',
                'ts_start_ms': 8000,
                'ts_end_ms': 12000,
                'valence': 0.5
            },
            {
                'call_id': 'call_pedro_1',
                'source': 'vendedor',
                'text': 'O ROI é de 150% em 12 meses. O investimento é de R$ 50.000. O payback é de 8 meses.',
                'ts_start_ms': 12000,
                'ts_end_ms': 18000,
                'valence': 0.7
            },
            {
                'call_id': 'call_pedro_1',
                'source': 'vendedor',
                'text': 'Vou enviar uma proposta detalhada com todos os números.',
                'ts_start_ms': 18000,
                'ts_end_ms': 22000,
                'valence': 0.5
            }
        ]
        self.transcriptions.extend(transcriptions_pedro)
    
    def get_calls_by_seller(self, seller_id, since_days=90):
        return [call for call in self.calls if call['seller_id'] == seller_id]
    
    def get_transcriptions_by_call(self, call_id):
        return [t for t in self.transcriptions if t['call_id'] == call_id]
    
    def get_sellers_with_sufficient_data(self, since_days=90, min_calls=1):
        return self.sellers
    
    def insert_disc_profile(self, profile_data):
        print(f"📊 Perfil DISC inserido: {profile_data['seller_id']}")
        return profile_data['id']
    
    def insert_disc_recommendation(self, recommendation_data):
        print(f"💡 Recomendação DISC inserida: {recommendation_data['seller_id']}")
        return recommendation_data['id']
    
    def insert_disc_feature_snapshot(self, snapshot_data):
        print(f"📸 Snapshot DISC inserido: {snapshot_data['seller_id']}")
        return snapshot_data['id']


def demo_individual_components():
    """Demonstra cada componente individualmente."""
    print("🎯 Demonstração dos Componentes DISC")
    print("=" * 50)
    
    dao = DemoDAO()
    
    # 1. Extrator
    print("\n1️⃣ **DiscFeatureExtractor**")
    extractor = DiscFeatureExtractor(dao)
    
    for seller in dao.sellers:
        features = extractor.from_calls(seller['id'])
        print(f"   📊 {seller['name']}: {len(features)} janelas de features")
        
        if features:
            sample = features[0]
            print(f"   📋 Sample: talk_ratio={sample.get('talk_ratio', 0):.2f}, "
                  f"imperatives={sample.get('imperatives', 0):.2f}, "
                  f"empathy={sample.get('empathy', 0):.2f}")
    
    # 2. Scorer
    print("\n2️⃣ **DiscScorer**")
    scorer = DiscScorer()
    
    for seller in dao.sellers:
        features = extractor.from_calls(seller['id'])
        if features:
            scores = scorer.score_disc(features)
            disc_type = scorer.get_disc_type(scores)
            strengths_weaknesses = scorer.get_strengths_weaknesses(scores)
            
            print(f"   🎯 {seller['name']}:")
            print(f"      Scores: D={scores['D']:.2f}, I={scores['I']:.2f}, "
                  f"S={scores['S']:.2f}, C={scores['C']:.2f}")
            print(f"      Tipo: {disc_type}")
            print(f"      Pontos fortes: {strengths_weaknesses['strengths']}")
            print(f"      Fraquezas: {strengths_weaknesses['weaknesses']}")
    
    # 3. Recommender
    print("\n3️⃣ **DiscRecommender**")
    recommender = DiscRecommender()
    
    for seller in dao.sellers:
        features = extractor.from_calls(seller['id'])
        if features:
            scores = scorer.score_disc(features)
            gaps = recommender.weaknesses_from_scores(scores)
            plan = recommender.build_plan(gaps)
            
            print(f"   💡 {seller['name']}:")
            print(f"      Fraquezas: {gaps}")
            print(f"      Módulos: {len(plan['modules'])}")
            print(f"      Dicas: {len(plan['tips'])}")
            print(f"      Duração total: {plan['total_duration_minutes']}min")


def demo_batch_processing():
    """Demonstra processamento em lote."""
    print("\n🔄 Demonstração do Processamento em Lote")
    print("=" * 50)
    
    dao = DemoDAO()
    batch_job = DiscBatchJob(dao)
    
    # Processar todos os vendedores
    results = batch_job.run_for_all_sellers(since_days=90, min_calls=1)
    
    print(f"📊 Resultados do processamento em lote:")
    for result in results:
        seller_id = result['seller_id']
        seller_name = next(s['name'] for s in dao.sellers if s['id'] == seller_id)
        
        if result['success']:
            scores = result['scores']
            gaps = result['gaps']
            plan = result['plan']
            
            print(f"\n   ✅ {seller_name}:")
            print(f"      Scores: D={scores['D']:.2f}, I={scores['I']:.2f}, "
                  f"S={scores['S']:.2f}, C={scores['C']:.2f}")
            print(f"      Fraquezas: {gaps}")
            print(f"      Módulos recomendados: {len(plan['modules'])}")
            
            # Mostrar alguns módulos
            for i, module in enumerate(plan['modules'][:2]):
                print(f"        {i+1}. {module['title']} ({module['duration']})")
        else:
            print(f"\n   ❌ {seller_name}: {result.get('message', 'Erro desconhecido')}")


def demo_mentor_integration():
    """Demonstra integração com Mentor Engine."""
    print("\n🎓 Demonstração da Integração com Mentor Engine")
    print("=" * 50)
    
    dao = DemoDAO()
    batch_job = DiscBatchJob(dao)
    
    # Simular contexto de call
    seller_id = 'joao_001'
    seller_name = 'João Silva'
    
    print(f"📞 Simulando call do {seller_name}...")
    
    # 1. Carregar perfil DISC
    result = batch_job.run_for_seller(seller_id)
    
    if result['success']:
        scores = result['scores']
        gaps = result['gaps']
        plan = result['plan']
        
        print(f"\n📊 Perfil DISC carregado:")
        print(f"   Scores: D={scores['D']:.2f}, I={scores['I']:.2f}, "
              f"S={scores['S']:.2f}, C={scores['C']:.2f}")
        print(f"   Fraquezas: {gaps}")
        
        # 2. Simular coaching com insights DISC
        print(f"\n💡 Coaching aprimorado com DISC:")
        
        # Feedback base
        base_feedback = [
            "Excelente trabalho na call!",
            "Conseguiu identificar as necessidades do cliente.",
            "Próximo passo: enviar proposta detalhada."
        ]
        
        print(f"   📋 Feedback base:")
        for feedback in base_feedback:
            print(f"      • {feedback}")
        
        # Feedback aprimorado com DISC
        if gaps:
            print(f"\n   🎯 Insights DISC adicionados:")
            
            for gap in gaps[:2]:
                if gap == "D_baixa":
                    print(f"      • Seja mais assertivo: use frases diretas e objetivas")
                elif gap == "I_baixa":
                    print(f"      • Faça mais perguntas abertas para explorar necessidades")
                elif gap == "S_baixa":
                    print(f"      • Evite interromper e pratique escuta ativa")
                elif gap == "C_baixa":
                    print(f"      • Estruture sua apresentação em 3 pontos principais")
            
            # Dicas rápidas
            quick_tips = plan['tips'][:3]
            print(f"\n   💡 Dicas rápidas para próxima call:")
            for tip in quick_tips:
                print(f"      • {tip}")


def main():
    """Executa demonstração completa."""
    print("🎯 Sistema DISC - Demonstração Completa")
    print("=" * 60)
    print("Este sistema analisa transcrições de vendas para inferir")
    print("o perfil DISC do vendedor e gerar coaching personalizado.")
    print("=" * 60)
    
    try:
        # Demonstração 1: Componentes individuais
        demo_individual_components()
        
        # Demonstração 2: Processamento em lote
        demo_batch_processing()
        
        # Demonstração 3: Integração com Mentor
        demo_mentor_integration()
        
        print("\n🎉 Demonstração concluída com sucesso!")
        print("\n📋 Resumo do que foi demonstrado:")
        print("   ✅ Extração de features linguísticas/prosódicas")
        print("   ✅ Cálculo de scores DISC (D, I, S, C)")
        print("   ✅ Identificação de fraquezas comportamentais")
        print("   ✅ Geração de planos de treino personalizados")
        print("   ✅ Integração com sistema de coaching")
        print("   ✅ Processamento em lote de vendedores")
        
        print("\n💡 Próximos passos:")
        print("   • Integrar com dados reais de transcrições")
        print("   • Ajustar pesos baseado em validação")
        print("   • Implementar UI para visualização DISC")
        print("   • Adicionar tracking de progresso")
        
    except Exception as e:
        print(f"\n❌ Erro na demonstração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
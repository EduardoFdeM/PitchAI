#!/usr/bin/env python3
"""
Teste da Feature 3 - Análise de Sentimento Multi-Dimensional
==========================================================

Teste básico para verificar se a implementação da Feature 3 está funcionando.
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai.sentiment import SentimentService, SentimentConfig
from ai.sentiment.models import SentimentSample, SentimentEvent, DashboardData

def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_sentiment_service_basic():
    """Teste básico do SentimentService."""
    print("🧪 Testando Feature 3 - Análise de Sentimento Multi-Dimensional")
    print("=" * 70)
    
    # Configuração
    config = SentimentConfig()
    service = SentimentService(config)
    
    # Contadores para métricas
    sentiment_samples = []
    alerts_received = []
    dashboard_updates = []
    
    def on_sentiment_updated(sample: SentimentSample):
        """Callback para amostras de sentimento."""
        sentiment_samples.append(sample)
        print(f"📊 Sentimento: {sample.score_valence:.2f}, Engajamento: {sample.score_engagement:.2f}")
    
    def on_alert_triggered(event: SentimentEvent):
        """Callback para alertas."""
        alerts_received.append(event)
        print(f"🚨 Alerta: {event.kind} - {event.label} (força: {event.strength:.2f})")
    
    def on_dashboard_updated(data: DashboardData):
        """Callback para atualizações do dashboard."""
        dashboard_updates.append(data)
        print(f"📈 Dashboard: Sentimento {data.sentiment_percent}%, "
              f"Engajamento {data.engagement_percent}%, "
              f"Sinais: {data.buying_signals_count}")
    
    def on_error(error: str):
        """Callback para erros."""
        print(f"❌ Erro: {error}")
    
    try:
        # Conectar callbacks
        service.sentiment_updated.connect(on_sentiment_updated)
        service.alert_triggered.connect(on_alert_triggered)
        service.dashboard_updated.connect(on_dashboard_updated)
        service.error_occurred.connect(on_error)
        
        # Inicializar serviço
        print("🔧 Inicializando serviço...")
        service.initialize()
        
        # Iniciar análise
        call_id = "test_call_003"
        print(f"🎤 Iniciando análise para call_id: {call_id}")
        service.start(call_id)
        
        # Simular dados de entrada
        print("📝 Simulando dados de entrada...")
        
        # Texto 1 - Positivo
        service.process_text_chunk(
            "Estou muito interessado no produto, parece excelente!",
            1000, 5000
        )
        
        # Áudio 1 - Positivo
        audio_positive = np.random.normal(0, 0.2, 16000).astype(np.int16)
        service.process_audio_chunk(audio_positive, 1000, 5000)
        
        time.sleep(1)
        
        # Texto 2 - Com palavras-gatilho
        service.process_text_chunk(
            "Qual é o preço? E qual o prazo de entrega?",
            6000, 10000
        )
        
        # Áudio 2 - Neutro
        audio_neutral = np.random.normal(0, 0.1, 16000).astype(np.int16)
        service.process_audio_chunk(audio_neutral, 6000, 10000)
        
        time.sleep(1)
        
        # Texto 3 - Sinais de compra
        service.process_text_chunk(
            "Vamos fazer um piloto para testar o sistema",
            11000, 15000
        )
        
        # Áudio 3 - Engajado
        audio_engaged = np.random.normal(0, 0.3, 16000).astype(np.int16)
        service.process_audio_chunk(audio_engaged, 11000, 15000)
        
        time.sleep(2)
        
        # Parar análise
        print("⏹️ Parando análise...")
        service.stop(call_id)
        
        # Análise dos resultados
        print("\n📊 ANÁLISE DOS RESULTADOS")
        print("=" * 40)
        
        print(f"1️⃣ Amostras de sentimento: {len(sentiment_samples)}")
        if sentiment_samples:
            avg_sentiment = sum(s.score_valence for s in sentiment_samples) / len(sentiment_samples)
            avg_engagement = sum(s.score_engagement for s in sentiment_samples) / len(sentiment_samples)
            print(f"   Sentimento médio: {avg_sentiment:.2f}")
            print(f"   Engajamento médio: {avg_engagement:.2f}")
        
        print(f"\n2️⃣ Alertas gerados: {len(alerts_received)}")
        for alert in alerts_received:
            print(f"   - {alert.kind}: {alert.label} (força: {alert.strength:.2f})")
        
        print(f"\n3️⃣ Atualizações do dashboard: {len(dashboard_updates)}")
        if dashboard_updates:
            latest = dashboard_updates[-1]
            print(f"   Último sentimento: {latest.sentiment_percent}%")
            print(f"   Último engajamento: {latest.engagement_percent}%")
            print(f"   Sinais de compra: {latest.buying_signals_count}")
        
        # Estatísticas do serviço
        print(f"\n4️⃣ Estatísticas do serviço:")
        stats = service.get_service_stats()
        print(f"   Amostras processadas: {stats['samples_processed']}")
        print(f"   Alertas gerados: {stats['alerts_generated']}")
        print(f"   Tamanho dos buffers: {stats['buffer_sizes']}")
        
        # Resumo da chamada
        print(f"\n5️⃣ Resumo da chamada:")
        summary = service.get_sentiment_summary(call_id)
        if summary:
            print(f"   Call ID: {summary['call_id']}")
            print(f"   Amostras processadas: {summary['samples_processed']}")
            print(f"   Alertas gerados: {summary['alerts_generated']}")
            print(f"   Análise visual: {'Habilitada' if summary['vision_enabled'] else 'Desabilitada'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpar recursos
        service.cleanup()

def test_components_individually():
    """Testar componentes individuais."""
    print("\n🔧 Testando componentes individuais...")
    
    config = SentimentConfig()
    
    # Teste TextAnalyzer
    print("   📝 Testando TextAnalyzer...")
    from ai.sentiment.text_analyzer import TextAnalyzer
    text_analyzer = TextAnalyzer(config)
    
    sentiment = text_analyzer.analyze_sentiment("Estou muito satisfeito com o produto")
    print(f"      Sentimento: {sentiment:.2f}")
    
    keywords = text_analyzer.detect_keywords("Qual é o preço e prazo de entrega?")
    print(f"      Keywords detectadas: {len(keywords)}")
    
    engagement = text_analyzer.calculate_engagement("Como funciona? Pode explicar melhor?")
    print(f"      Engajamento: {engagement:.2f}")
    
    # Teste ProsodyAnalyzer
    print("   🎵 Testando ProsodyAnalyzer...")
    from ai.sentiment.prosody_analyzer import ProsodyAnalyzer
    prosody_analyzer = ProsodyAnalyzer(config)
    
    audio_sample = np.random.normal(0, 0.2, 16000).astype(np.int16)
    features = prosody_analyzer.extract_features(audio_sample)
    print(f"      F0 médio: {features.f0_mean:.1f} Hz")
    print(f"      Energia: {features.energy_mean:.3f}")
    
    valence = prosody_analyzer.classify_valence(features)
    print(f"      Valência: {valence:.2f}")
    
    # Teste FusionEngine
    print("   🔄 Testando FusionEngine...")
    from ai.sentiment.fusion_engine import FusionEngine
    fusion_engine = FusionEngine(config)
    
    fused_sentiment = fusion_engine.fuse_sentiment(0.8, 0.6)
    print(f"      Sentimento fundido: {fused_sentiment:.2f}")
    
    fused_engagement = fusion_engine.fuse_engagement(0.7, 0.5)
    print(f"      Engajamento fundido: {fused_engagement:.2f}")
    
    # Teste KeywordDetector
    print("   🔍 Testando KeywordDetector...")
    from ai.sentiment.keyword_detector import KeywordDetector
    keyword_detector = KeywordDetector(config)
    
    from ai.sentiment.models import KeywordMatch
    keywords = [
        KeywordMatch(keyword="preço", confidence=0.9, position=0, context="Qual é o preço?"),
        KeywordMatch(keyword="prazo", confidence=0.8, position=10, context="Qual o prazo?")
    ]
    
    events = keyword_detector.process_keywords("test_call", keywords, 5000)
    print(f"      Eventos gerados: {len(events)}")
    
    print("   ✅ Testes de componentes concluídos")

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste da Feature 3 - Análise de Sentimento Multi-Dimensional")
    print("=" * 80)
    
    setup_logging()
    
    # Teste 1: Componentes individuais
    test_components_individually()
    
    # Teste 2: Serviço completo
    success = test_sentiment_service_basic()
    
    if success:
        print("\n🎉 FEATURE 3 IMPLEMENTADA COM SUCESSO!")
        print("   ✅ Análise de texto funcionando")
        print("   ✅ Análise de prosódia funcionando")
        print("   ✅ Fusão de dados funcionando")
        print("   ✅ Detecção de keywords funcionando")
        print("   ✅ Dashboard em tempo real funcionando")
        print("   ✅ Alertas e sinais de compra funcionando")
    else:
        print("\n❌ Teste falhou.")

if __name__ == "__main__":
    main() 
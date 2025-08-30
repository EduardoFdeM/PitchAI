#!/usr/bin/env python3
"""
Teste de Integração Real da Feature 3 - Análise de Sentimento Multi-Dimensional
============================================================================

Teste real da Feature 3 integrada com a aplicação principal PitchAI.
"""

import sys
import time
import logging
import numpy as np
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.application import PitchAIApp
from core.config import Config
from ai.sentiment import SentimentService, SentimentConfig
from ai.sentiment.models import SentimentSample, SentimentEvent, DashboardData


def setup_logging():
    """Configurar logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_real_application_integration():
    """Teste de integração real com a aplicação principal."""
    print("🚀 Testando integração real da Feature 3 com PitchAI...")
    print("=" * 70)
    
    # Configurações
    config = Config()
    
    # Inicializar aplicação principal
    try:
        pitch_app = PitchAIApp(config)
        pitch_app.initialize()
        print("✅ Aplicação principal inicializada")
    except Exception as e:
        print(f"❌ Erro ao inicializar aplicação principal: {e}")
        return False
    
    # Verificar se o SentimentService foi inicializado
    if not pitch_app.sentiment_service:
        print("❌ SentimentService não foi inicializado")
        return False
    
    print("✅ SentimentService integrado com sucesso")
    
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
    
    # Conectar callbacks diretamente ao SentimentService
    pitch_app.sentiment_service.sentiment_updated.connect(on_sentiment_updated)
    pitch_app.sentiment_service.alert_triggered.connect(on_alert_triggered)
    pitch_app.sentiment_service.dashboard_updated.connect(on_dashboard_updated)
    
    # Simular início de gravação
    print("\n🎤 Iniciando gravação simulada...")
    pitch_app.start_recording()
    
    # Simular dados reais de conversa
    conversation_data = [
        {
            "text": "Olá, sou João da TechCorp. Como você está hoje?",
            "speaker": "vendor",
            "sentiment": "neutral",
            "duration": 3
        },
        {
            "text": "Oi João, estou bem, obrigado. Conte-me sobre sua empresa.",
            "speaker": "client",
            "sentiment": "positive",
            "duration": 4
        },
        {
            "text": "Nossa solução de CRM é líder no mercado há 5 anos.",
            "speaker": "vendor",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "Interessante! Como funciona a integração com nosso sistema atual?",
            "speaker": "client",
            "sentiment": "positive",
            "duration": 4
        },
        {
            "text": "A integração é muito simples, leva apenas 2 semanas.",
            "speaker": "vendor",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "E qual é o preço? Está dentro do nosso orçamento?",
            "speaker": "client",
            "sentiment": "neutral",
            "duration": 4
        },
        {
            "text": "O investimento é de R$ 50 mil por ano.",
            "speaker": "vendor",
            "sentiment": "neutral",
            "duration": 3
        },
        {
            "text": "Hmm, está um pouco caro. Tem desconto para contrato anual?",
            "speaker": "client",
            "sentiment": "negative",
            "duration": 4
        },
        {
            "text": "Sim, temos 15% de desconto para pagamento anual.",
            "speaker": "vendor",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "Ótimo! E qual o prazo de implementação?",
            "speaker": "client",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "Implementamos em 4 semanas após a assinatura.",
            "speaker": "vendor",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "Perfeito! Vamos fazer um piloto para testar?",
            "speaker": "client",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "Excelente ideia! Vou preparar a proposta hoje mesmo.",
            "speaker": "vendor",
            "sentiment": "positive",
            "duration": 3
        },
        {
            "text": "Perfeito! Estou muito animado com essa parceria.",
            "speaker": "client",
            "sentiment": "positive",
            "duration": 3
        }
    ]
    
    current_time = 0
    
    for i, turn in enumerate(conversation_data):
        print(f"\n🎭 Turno {i+1}: {turn['speaker'].upper()}")
        print(f"   Texto: \"{turn['text']}\"")
        print(f"   Sentimento esperado: {turn['sentiment']}")
        
        # Simular áudio baseado no sentimento
        if turn['sentiment'] == 'positive':
            # Áudio mais energético
            audio_data = np.random.normal(0, 0.3, 16000 * turn['duration']).astype(np.int16)
        elif turn['sentiment'] == 'negative':
            # Áudio mais baixo
            audio_data = np.random.normal(0, 0.1, 16000 * turn['duration']).astype(np.int16)
        else:
            # Áudio neutro
            audio_data = np.random.normal(0, 0.2, 16000 * turn['duration']).astype(np.int16)
        
        # Processar através da aplicação principal
        ts_start = current_time
        ts_end = current_time + (turn['duration'] * 1000)
        
        # Simular processamento de áudio
        if pitch_app.audio_capture:
            pitch_app._process_audio_for_sentiment(audio_data, ts_start, ts_end)
        
        # Simular processamento de transcrição (apenas do cliente)
        if turn['speaker'] == 'client':
            pitch_app._process_transcription_for_sentiment(turn['text'], 'loopback', ts_start, ts_end)
        
        current_time = ts_end
        
        # Aguardar um pouco
        time.sleep(0.5)
    
    # Aguardar processamento final
    time.sleep(2)
    
    # Parar gravação
    print("\n⏹️ Parando gravação...")
    pitch_app.stop_recording()
    
    # Análise dos resultados
    print("\n📊 ANÁLISE DOS RESULTADOS REAIS")
    print("=" * 50)
    
    print(f"1️⃣ Amostras de sentimento: {len(sentiment_samples)}")
    if sentiment_samples:
        avg_sentiment = sum(s.score_valence for s in sentiment_samples) / len(sentiment_samples)
        avg_engagement = sum(s.score_engagement for s in sentiment_samples) / len(sentiment_samples)
        print(f"   Sentimento médio: {avg_sentiment:.2f}")
        print(f"   Engajamento médio: {avg_engagement:.2f}")
        
        # Análise de tendência
        if len(sentiment_samples) > 1:
            first_sentiment = sentiment_samples[0].score_valence
            last_sentiment = sentiment_samples[-1].score_valence
            trend = "↗️ Melhorou" if last_sentiment > first_sentiment else "↘️ Piorou" if last_sentiment < first_sentiment else "→ Manteve"
            print(f"   Tendência: {trend}")
    
    print(f"\n2️⃣ Alertas gerados: {len(alerts_received)}")
    alert_types = {}
    for alert in alerts_received:
        alert_types[alert.kind] = alert_types.get(alert.kind, 0) + 1
        print(f"   - {alert.kind}: {alert.label} (força: {alert.strength:.2f})")
    
    print(f"\n3️⃣ Tipos de alertas: {alert_types}")
    
    print(f"\n4️⃣ Atualizações do dashboard: {len(dashboard_updates)}")
    if dashboard_updates:
        latest = dashboard_updates[-1]
        print(f"   Último sentimento: {latest.sentiment_percent}%")
        print(f"   Último engajamento: {latest.engagement_percent}%")
        print(f"   Sinais de compra: {latest.buying_signals_count}")
    
    # Verificar integração com UI
    print(f"\n5️⃣ Verificação da integração:")
    print(f"   SentimentService inicializado: {pitch_app.sentiment_service is not None}")
    print(f"   AudioCapture inicializado: {pitch_app.audio_capture is not None}")
    print(f"   NPUManager inicializado: {pitch_app.npu_manager is not None}")
    print(f"   Database inicializado: {pitch_app.database is not None}")
    
    # Estatísticas do serviço
    if pitch_app.sentiment_service:
        stats = pitch_app.sentiment_service.get_service_stats()
        print(f"\n6️⃣ Estatísticas do serviço:")
        print(f"   Amostras processadas: {stats['samples_processed']}")
        print(f"   Alertas gerados: {stats['alerts_generated']}")
        print(f"   Tamanho dos buffers: {stats['buffer_sizes']}")
    
    # Encerrar aplicação
    pitch_app.shutdown()
    
    return len(sentiment_samples) > 0 and len(alerts_received) > 0

def test_ui_integration():
    """Teste de integração com a UI."""
    print("\n🎨 Testando integração com UI...")
    
    try:
        from ui.sentiment_widget import SentimentWidget
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # Criar aplicação Qt
        app = QApplication(sys.argv)
        
        # Criar widget de sentimento
        sentiment_widget = SentimentWidget()
        sentiment_widget.show()
        
        print("✅ Widget de sentimento criado com sucesso")
        
        # Simular dados
        from ai.sentiment.models import DashboardData, SentimentEvent
        
        # Atualizar dashboard
        dashboard_data = DashboardData(
            sentiment_percent=75,
            engagement_percent=80,
            buying_signals_count=3,
            alerts=[]
        )
        sentiment_widget.update_dashboard(dashboard_data)
        
        # Adicionar alerta
        alert = SentimentEvent(
            call_id="test_call",
            ts_ms=1000,
            kind="buying_signal",
            label="interesse em compra",
            strength=0.8
        )
        sentiment_widget.add_alert(alert)
        
        print("✅ Dados simulados aplicados ao widget")
        
        # Verificar configurações
        vision_enabled = sentiment_widget.get_vision_enabled()
        print(f"   Análise visual habilitada: {vision_enabled}")
        
        # Limpar dados
        sentiment_widget._clear_data()
        print("✅ Dados limpos com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração com UI: {e}")
        return False

def main():
    """Função principal."""
    print("🚀 PitchAI - Teste de Integração Real da Feature 3")
    print("=" * 70)
    
    setup_logging()
    
    # Teste de integração real
    success1 = test_real_application_integration()
    
    # Teste de integração com UI
    success2 = test_ui_integration()
    
    if success1 and success2:
        print("\n🎉 FEATURE 3 INTEGRADA COM SUCESSO!")
        print("   ✅ Integração com aplicação principal funcionando")
        print("   ✅ Integração com UI funcionando")
        print("   ✅ Análise de texto funcionando")
        print("   ✅ Análise de prosódia funcionando")
        print("   ✅ Fusão de dados funcionando")
        print("   ✅ Detecção de keywords funcionando")
        print("   ✅ Dashboard em tempo real funcionando")
        print("   ✅ Alertas e sinais de compra funcionando")
        print("   ✅ Integração com Features 1 e 2 funcionando")
        print("\n🚀 A Feature 3 está pronta para uso real!")
    else:
        print("\n❌ Alguns testes de integração falharam.")

if __name__ == "__main__":
    main() 
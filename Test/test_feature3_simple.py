#!/usr/bin/env python3
"""
Teste Simples da Feature 3 - Análise de Sentimento
================================================

Teste básico da Feature 3 sem dependências externas.
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

def test_sentiment_service():
    """Teste básico do serviço de sentimento."""
    print("🧠 Testando serviço de sentimento...")
    
    # Configurações
    config = SentimentConfig()
    sentiment_service = SentimentService(config)
    
    # Inicializar
    sentiment_service.initialize()
    
    # Contadores
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
        print(f"🚨 Alerta: {event.kind} - {event.label}")
    
    def on_dashboard_updated(data: DashboardData):
        """Callback para atualizações do dashboard."""
        dashboard_updates.append(data)
        print(f"📈 Dashboard: Sentimento {data.sentiment_percent}%, Engajamento {data.engagement_percent}%")
    
    # Conectar callbacks
    sentiment_service.sentiment_updated.connect(on_sentiment_updated)
    sentiment_service.alert_triggered.connect(on_alert_triggered)
    sentiment_service.dashboard_updated.connect(on_dashboard_updated)
    
    # Iniciar análise
    call_id = "test_call_001"
    sentiment_service.start(call_id)
    
    # Simular dados
    test_texts = [
        "Estou muito interessado no seu produto!",
        "O preço está um pouco alto...",
        "Perfeito! Vamos fechar o negócio!",
        "Preciso pensar melhor sobre isso.",
        "Excelente! Estou animado com essa parceria!"
    ]
    
    current_time = 0
    
    for i, text in enumerate(test_texts):
        print(f"\n📝 Processando texto {i+1}: \"{text}\"")
        
        # Simular áudio
        audio_data = np.random.normal(0, 0.2, 16000 * 3).astype(np.int16)
        
        # Processar
        ts_start = current_time
        ts_end = current_time + 3000
        
        sentiment_service.process_audio_chunk(audio_data, ts_start, ts_end)
        sentiment_service.process_text_chunk(text, ts_start, ts_end)
        
        current_time = ts_end
        time.sleep(1)
    
    # Aguardar processamento
    time.sleep(2)
    
    # Parar
    sentiment_service.stop(call_id)
    
    # Resultados
    print(f"\n📊 RESULTADOS:")
    print(f"   Amostras: {len(sentiment_samples)}")
    print(f"   Alertas: {len(alerts_received)}")
    print(f"   Dashboard updates: {len(dashboard_updates)}")
    
    # Estatísticas
    stats = sentiment_service.get_service_stats()
    print(f"   Estatísticas: {stats}")
    
    # Limpar
    sentiment_service.cleanup()
    
    return len(sentiment_samples) > 0

def main():
    """Função principal."""
    print("🚀 Teste Simples da Feature 3")
    print("=" * 40)
    
    setup_logging()
    
    success = test_sentiment_service()
    
    if success:
        print("\n✅ Feature 3 funcionando!")
    else:
        print("\n❌ Feature 3 falhou.")

if __name__ == "__main__":
    main() 
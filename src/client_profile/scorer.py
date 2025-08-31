"""
Scorer - Fórmulas de complexidade e stage do cliente
==================================================

Heurísticas para classificar clientes e determinar cadência de vendas.
"""

from typing import Dict, List, Any, Tuple


def complexity_score(metrics: Dict[str, Any], normalizer=None, history=None) -> Tuple[float, str]:
    """
    Calcular score de complexidade do cliente (0..1) e determinar tier.
    
    Args:
        metrics: Dict com keys: top_objections, objections_count, sentiment_avg, engagement,
                 first_objection_s?, distinct_objections?, buy_signals?
        normalizer: StatsService para normalização dinâmica
        history: Dict com histórico do cliente (repeated_sessions?)
        
    Returns:
        Tuple (score, tier) onde tier é 'facil', 'medio' ou 'dificil'
    """
    # 1. Dificuldade das objeções (peso: 35%)
    top_objections = metrics.get("top_objections", []) or []
    if "autoridade" in top_objections:
        diff_score = 1.0  # Mais difícil
    elif "preco" in top_objections:
        diff_score = 0.6  # Médio
    elif "timing" in top_objections:
        diff_score = 0.3  # Mais fácil
    else:
        diff_score = 0.1  # Sem objeções = fácil
    
    # 2. Frequência de objeções (peso: 15%)
    objections_count = metrics.get("objections_count", 0)
    freq_score = min(1.0, objections_count / 4.0)  # Normalizado para 0..1
    
    # 3. Negatividade (peso: 15%)
    sentiment_avg = metrics.get("sentiment_avg", 0.0)
    negativity_score = max(0.0, -float(sentiment_avg))  # [-1..1] -> [0..1]
    
    # 4. Baixa resposta/engajamento (peso: 10%)
    engagement = metrics.get("engagement", 0.0)
    low_response_score = 1.0 - float(engagement)  # [0..1] -> [0..1]
    
    # 5. Tempo até primeira objeção (peso: 10%) - NOVO
    first_objection_s = metrics.get("first_objection_s", 180.0)  # 3min padrão
    early_score = 1.0 - min(1.0, first_objection_s / 180.0)  # Objeção antes de 3min = mais difícil
    
    # 6. Diversidade de objeções (peso: 10%) - NOVO
    distinct_objections = metrics.get("distinct_objections", 1)
    diversity_score = min(1.0, distinct_objections / 4.0)  # Mais tipos = mais difícil
    
    # 7. Sinais de compra (peso: 5%) - NOVO
    buy_signals = metrics.get("buy_signals", 0)
    buy_buffer = max(0.0, 1.0 - 0.2 * buy_signals)  # Sinais de compra reduzem complexidade
    
    # 8. Histórico de persistência (peso: 5%) - NOVO
    hist_bonus = 0.0
    if history:
        repeated_sessions = history.get("repeated_sessions", 0)
        hist_bonus = min(0.2, 0.05 * repeated_sessions)  # Cliente que repete objeções = mais difícil
    
    # Cálculo final com novos sinais
    raw_score = (0.35 * diff_score + 
                 0.15 * freq_score + 
                 0.15 * negativity_score + 
                 0.10 * low_response_score +
                 0.10 * early_score + 
                 0.10 * diversity_score + 
                 0.05 * hist_bonus) * buy_buffer
    
    # Normalização dinâmica por empresa
    if normalizer:
        score = normalizer.normalize("client_score", "complexity", raw_score, method="minmax")
    else:
        score = raw_score
    
    # Tiers por percentil dinâmico
    tier = None
    if normalizer:
        st = normalizer.dao.get_stats("client_score", "complexity")
        if st:
            tier = "facil" if score < st["p25"] else ("medio" if score < st["p75"] else "dificil")
    
    # Fallback para tiers fixos
    if tier is None:
        if score < 0.34:
            tier = "facil"
        elif score < 0.66:
            tier = "medio"
        else:
            tier = "dificil"
    
    return float(max(0.0, min(1.0, score))), tier


def infer_stage(text: str) -> str:
    """
    Inferir stage (cadência) do cliente baseado no texto.
    
    Args:
        text: Texto do transcript ou resumo
        
    Returns:
        Stage: 'descoberta', 'avanco', 'proposta', 'negociacao', 'fechamento'
    """
    if not text:
        return "descoberta"
    
    text_lower = text.lower()
    
    # Fechamento (mais específico primeiro)
    if any(word in text_lower for word in ["fechar", "assinatura", "contrato", "fechamento", "acordo"]):
        return "fechamento"
    
    # Negociação
    if any(word in text_lower for word in ["preço", "preco", "termos", "aprovação", "aprovacao", "decisor", "negociação", "negociacao"]):
        return "negociacao"
    
    # Proposta
    if any(word in text_lower for word in ["proposta", "orçamento", "orcamento", "rfp", "quote", "cotação", "cotacao"]):
        return "proposta"
    
    # Avanço
    if any(word in text_lower for word in ["próxima", "proxima", "agenda", "seguinte", "próximo", "proximo", "reunião", "reuniao"]):
        return "avanco"
    
    # Descoberta (padrão)
    return "descoberta"


def extract_topics(text: str) -> List[str]:
    """
    Extrair tópicos principais do texto.
    
    Args:
        text: Texto para análise
        
    Returns:
        Lista de tópicos identificados
    """
    if not text:
        return []
    
    text_lower = text.lower()
    topics = []
    
    # Tópicos de objeções
    objection_keywords = {
        "preco": ["preço", "preco", "custo", "valor", "caro", "barato"],
        "autoridade": ["decisor", "chefe", "diretor", "presidente", "autoridade", "aprovação", "aprovacao"],
        "timing": ["tempo", "agora", "depois", "quando", "cronograma", "prazo"],
        "necessidade": ["preciso", "necessito", "problema", "solução", "solucao", "benefício", "beneficio"]
    }
    
    for topic, keywords in objection_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    # Tópicos de interesse
    interest_keywords = {
        "roi": ["retorno", "roi", "investimento", "economia"],
        "integração": ["integração", "integracao", "sistema", "api", "conexão", "conexao"],
        "suporte": ["suporte", "ajuda", "treinamento", "implementação", "implementacao"]
    }
    
    for topic, keywords in interest_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    return list(set(topics))  # Remove duplicatas


def calculate_engagement_metrics(transcript_chunks: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calcular métricas de engajamento baseadas no transcript.
    
    Args:
        transcript_chunks: Lista de chunks de transcrição com speaker_id
        
    Returns:
        Dict com métricas: client_talk_ratio, avg_response_time, etc.
    """
    if not transcript_chunks:
        return {"client_talk_ratio": 0.0, "avg_response_time": 0.0}
    
    # Contar palavras por speaker
    client_words = 0
    seller_words = 0
    
    for chunk in transcript_chunks:
        text = chunk.get("text", "")
        speaker = chunk.get("speaker_id", "")
        word_count = len(text.split())
        
        if speaker == "client":
            client_words += word_count
        elif speaker == "seller":
            seller_words += word_count
    
    total_words = client_words + seller_words
    client_talk_ratio = client_words / total_words if total_words > 0 else 0.0
    
    return {
        "client_talk_ratio": client_talk_ratio,
        "client_words": client_words,
        "seller_words": seller_words,
        "total_words": total_words
    } 
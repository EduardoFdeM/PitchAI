"""
XP Rules - Regras de XP e progressão de nível
===========================================

Cálculo de XP e determinação de níveis para gamificação.
"""

from typing import Dict, List, Any, Tuple


# Definição de níveis
LEVELS = [
    ("junior", 0),
    ("pleno", 100),
    ("senior", 500),
    ("mentor", 1500)
]


def compute_xp(call_metrics: Dict[str, Any], client_tier: str, 
              stage_before: str, stage_after: str) -> int:
    """
    Calcular XP ganho na call.
    
    Args:
        call_metrics: Métricas da call
        client_tier: Tier do cliente (facil|medio|dificil)
        stage_before: Stage antes da call
        stage_after: Stage após a call
        
    Returns:
        XP ganho na call
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validação de entrada
    if not call_metrics:
        logger.warning("⚠️ call_metrics vazio, retornando XP base")
        call_metrics = {}
    
    if not client_tier:
        logger.warning("⚠️ client_tier não fornecido, usando 'medio'")
        client_tier = "medio"
    
    # XP base por tier do cliente
    base_xp = {
        "facil": 10,
        "medio": 20,
        "dificil": 40
    }.get(client_tier.lower(), 10)
    
    xp = base_xp
    xp_breakdown = {
        "base": base_xp,
        "bonuses": []
    }
    
    # Bônus por resolver objeção dominante
    if call_metrics.get("resolved_dominant", False):
        bonus = 10
        xp += bonus
        xp_breakdown["bonuses"].append(("objeção_dominante", bonus))
    
    # Bônus por avançar stage
    if stage_after and stage_before and stage_after != stage_before:
        bonus = 15
        xp += bonus
        xp_breakdown["bonuses"].append(("avanço_stage", bonus))
    
    # Bônus por bom equilíbrio de fala (cliente fala ≥50%)
    client_talk_ratio = call_metrics.get("client_talk_ratio", 0.0)
    if client_talk_ratio >= 0.5:
        bonus = 5
        xp += bonus
        xp_breakdown["bonuses"].append(("equilíbrio_fala", bonus))
    
    # Bônus por reduzir complexidade do cliente
    complexity_delta = call_metrics.get("complexity_delta", 0.0)
    if complexity_delta >= 0.05:
        bonus = 10
        xp += bonus
        xp_breakdown["bonuses"].append(("redução_complexidade", bonus))
    
    # Bônus por engajamento alto
    engagement = call_metrics.get("engagement", 0.0)
    if engagement >= 0.8:
        bonus = 5
        xp += bonus
        xp_breakdown["bonuses"].append(("engajamento_alto", bonus))
    
    # Bônus por sentimento positivo
    sentiment_avg = call_metrics.get("sentiment_avg", 0.0)
    if sentiment_avg >= 0.3:
        bonus = 5
        xp += bonus
        xp_breakdown["bonuses"].append(("sentimento_positivo", bonus))
    
    final_xp = max(0, xp)  # XP nunca pode ser negativo
    
    # Log detalhado para debugging
    logger.debug(f"🎯 XP calculado: {final_xp} (base: {base_xp}, bônus: {len(xp_breakdown['bonuses'])})")
    if xp_breakdown["bonuses"]:
        logger.debug(f"   Bônus: {xp_breakdown['bonuses']}")
    
    return final_xp


def level_from_xp(total_xp: int) -> str:
    """
    Determinar nível baseado no XP total.
    
    Args:
        total_xp: XP total do vendedor
        
    Returns:
        Nível atual: junior, pleno, senior, mentor
    """
    current_level = "junior"
    
    for level_name, threshold in LEVELS:
        if total_xp >= threshold:
            current_level = level_name
    
    return current_level


def get_level_progress(total_xp: int) -> Dict[str, Any]:
    """
    Calcular progresso para o próximo nível.
    
    Args:
        total_xp: XP total do vendedor
        
    Returns:
        Dict com progresso: current_level, next_level, xp_current, xp_next, progress_percent
    """
    current_level = level_from_xp(total_xp)
    
    # Encontrar threshold atual e próximo
    current_threshold = 0
    next_threshold = 1500  # Máximo
    
    for level_name, threshold in LEVELS:
        if total_xp >= threshold:
            current_threshold = threshold
        else:
            next_threshold = threshold
            break
    
    # Calcular progresso
    xp_in_level = total_xp - current_threshold
    xp_needed = next_threshold - current_threshold
    progress_percent = (xp_in_level / xp_needed * 100) if xp_needed > 0 else 100
    
    return {
        "current_level": current_level,
        "next_level": "mentor" if current_level == "mentor" else _get_next_level(current_level),
        "xp_current": current_threshold,
        "xp_next": next_threshold,
        "xp_in_level": xp_in_level,
        "xp_needed": xp_needed,
        "progress_percent": min(100.0, progress_percent)
    }


def _get_next_level(current_level: str) -> str:
    """Obter próximo nível."""
    level_names = [level[0] for level in LEVELS]
    try:
        current_index = level_names.index(current_level)
        if current_index < len(level_names) - 1:
            return level_names[current_index + 1]
    except ValueError:
        pass
    return "mentor"


def get_xp_breakdown(call_metrics: Dict[str, Any], client_tier: str, 
                    stage_before: str, stage_after: str) -> Dict[str, Any]:
    """
    Obter breakdown detalhado do XP ganho.
    
    Args:
        call_metrics: Métricas da call
        client_tier: Tier do cliente
        stage_before: Stage antes da call
        stage_after: Stage após a call
        
    Returns:
        Dict com breakdown do XP
    """
    breakdown = {
        "base_xp": 0,
        "bonuses": [],
        "total": 0
    }
    
    # XP base
    base_xp = {
        "facil": 10,
        "medio": 20,
        "dificil": 40
    }.get(client_tier, 10)
    
    breakdown["base_xp"] = base_xp
    breakdown["total"] = base_xp
    
    # Bônus por resolver objeção dominante
    if call_metrics.get("resolved_dominant", False):
        breakdown["bonuses"].append({
            "reason": "Objeção dominante resolvida",
            "xp": 10
        })
        breakdown["total"] += 10
    
    # Bônus por avançar stage
    if stage_after != stage_before:
        breakdown["bonuses"].append({
            "reason": f"Stage avançou: {stage_before} → {stage_after}",
            "xp": 15
        })
        breakdown["total"] += 15
    
    # Bônus por bom equilíbrio de fala
    client_talk_ratio = call_metrics.get("client_talk_ratio", 0.0)
    if client_talk_ratio >= 0.5:
        breakdown["bonuses"].append({
            "reason": f"Cliente falou {client_talk_ratio:.1%} da conversa",
            "xp": 5
        })
        breakdown["total"] += 5
    
    # Bônus por reduzir complexidade
    complexity_delta = call_metrics.get("complexity_delta", 0.0)
    if complexity_delta >= 0.05:
        breakdown["bonuses"].append({
            "reason": f"Complexidade reduzida em {complexity_delta:.2f}",
            "xp": 10
        })
        breakdown["total"] += 10
    
    # Bônus por engajamento alto
    engagement = call_metrics.get("engagement", 0.0)
    if engagement >= 0.8:
        breakdown["bonuses"].append({
            "reason": f"Engajamento alto: {engagement:.1%}",
            "xp": 5
        })
        breakdown["total"] += 5
    
    # Bônus por sentimento positivo
    sentiment_avg = call_metrics.get("sentiment_avg", 0.0)
    if sentiment_avg >= 0.3:
        breakdown["bonuses"].append({
            "reason": f"Sentimento positivo: {sentiment_avg:.2f}",
            "xp": 5
        })
        breakdown["total"] += 5
    
    return breakdown


def get_level_requirements() -> List[Dict[str, Any]]:
    """
    Obter requisitos de XP para cada nível.
    
    Returns:
        Lista com requisitos de cada nível
    """
    requirements = []
    
    for i, (level_name, threshold) in enumerate(LEVELS):
        next_threshold = LEVELS[i + 1][1] if i < len(LEVELS) - 1 else None
        
        requirements.append({
            "level": level_name,
            "xp_required": threshold,
            "xp_to_next": next_threshold - threshold if next_threshold else 0,
            "is_max": i == len(LEVELS) - 1
        })
    
    return requirements 
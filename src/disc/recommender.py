"""
DISC Recommender
===============

Transforma fraquezas DISC em planos de treino personalizados
para evolução do vendedor.
"""

import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DiscRecommender:
    """Recomendador de treinos baseado em análise DISC."""
    
    def __init__(self):
        # Mapeamento de lacunas DISC para módulos de treino
        self.disc_gaps = {
            "D_baixa": {
                "symptoms": ["talk_ratio<0.35", "imperatives<0.3"],
                "description": "Vendedor pouco assertivo e direto",
                "modules": [
                    {
                        "id": "assertividade_basica",
                        "title": "Assertividade sem perder empatia",
                        "duration": "15m",
                        "description": "Aprenda a ser direto e objetivo mantendo a conexão emocional"
                    },
                    {
                        "id": "fechamento_claro",
                        "title": "Fechamento e próximos passos objetivos",
                        "duration": "10m", 
                        "description": "Defina claramente os próximos passos e prazos"
                    },
                    {
                        "id": "tom_de_voz",
                        "title": "Tom de voz assertivo e confiante",
                        "duration": "12m",
                        "description": "Desenvolva um tom de voz que transmita autoridade"
                    }
                ],
                "tips": [
                    "Troque 'talvez' por 'vamos'",
                    "Defina próximo passo com prazo específico",
                    "Use frases diretas e objetivas",
                    "Evite hesitações desnecessárias",
                    "Mantenha postura ereta durante a call"
                ]
            },
            "I_baixa": {
                "symptoms": ["open_questions<0.2", "empathy<0.25"],
                "description": "Vendedor pouco empático e questionador",
                "modules": [
                    {
                        "id": "perguntas_abertas",
                        "title": "Fazer perguntas abertas e explorar necessidades",
                        "duration": "15m",
                        "description": "Desenvolva a habilidade de fazer perguntas que geram insights"
                    },
                    {
                        "id": "empatia_ativa",
                        "title": "Empatia ativa e conexão emocional",
                        "duration": "18m",
                        "description": "Aprenda a conectar emocionalmente com o cliente"
                    },
                    {
                        "id": "storytelling",
                        "title": "Storytelling para engajamento",
                        "duration": "20m",
                        "description": "Use histórias para criar conexão e engajamento"
                    }
                ],
                "tips": [
                    "Faça 1 pergunta aberta antes de responder",
                    "Parafraseie para validar entendimento",
                    "Use 'entendo' e 'compreendo' genuinamente",
                    "Compartilhe experiências relevantes",
                    "Celebre pequenas conquistas do cliente"
                ]
            },
            "S_baixa": {
                "symptoms": ["interrupt_rate>0.3", "turn_balance<0.4"],
                "description": "Vendedor impaciente e interrompe muito",
                "modules": [
                    {
                        "id": "escuta_ativa",
                        "title": "Escuta ativa e ritmo da conversa",
                        "duration": "10m",
                        "description": "Desenvolva paciência e escuta genuína"
                    },
                    {
                        "id": "pausas_estrategicas",
                        "title": "Pausas estratégicas e timing",
                        "duration": "8m",
                        "description": "Aprenda quando falar e quando ouvir"
                    },
                    {
                        "id": "controle_emocional",
                        "title": "Controle emocional e paciência",
                        "duration": "12m",
                        "description": "Mantenha a calma mesmo em situações desafiadoras"
                    }
                ],
                "tips": [
                    "Evite interromper o cliente",
                    "Espere 1-2 segundos antes de responder",
                    "Faça anotações para não esquecer pontos",
                    "Respire fundo antes de falar",
                    "Conte até 3 antes de interromper"
                ]
            },
            "C_baixa": {
                "symptoms": ["structure<0.25", "closed_questions<0.2"],
                "description": "Vendedor desorganizado e pouco estruturado",
                "modules": [
                    {
                        "id": "estrutura_valor",
                        "title": "Estruturar argumento (3 passos) + números",
                        "duration": "15m",
                        "description": "Organize sua apresentação em 3 pontos principais"
                    },
                    {
                        "id": "dados_evidencias",
                        "title": "Usar dados e evidências",
                        "duration": "12m",
                        "description": "Suporte seus argumentos com números e fatos"
                    },
                    {
                        "id": "agenda_estruturada",
                        "title": "Agenda estruturada e follow-up",
                        "duration": "10m",
                        "description": "Mantenha controle da agenda e próximos passos"
                    }
                ],
                "tips": [
                    "Use 3 bullets com números específicos",
                    "Mostre ROI e evidências concretas",
                    "Prepare agenda antes da call",
                    "Faça resumo estruturado no final",
                    "Documente compromissos e prazos"
                ]
            }
        }
        
        # Módulos complementares para combinações específicas
        self.combination_modules = {
            "D_baixa_I_baixa": [
                {
                    "id": "presenca_executiva",
                    "title": "Presença executiva e liderança",
                    "duration": "25m",
                    "description": "Desenvolva presença e liderança em calls"
                }
            ],
            "S_baixa_C_baixa": [
                {
                    "id": "organizacao_eficiencia",
                    "title": "Organização e eficiência em vendas",
                    "duration": "20m",
                    "description": "Combine estrutura com paciência"
                }
            ]
        }
    
    def weaknesses_from_scores(self, scores: Dict[str, float]) -> List[str]:
        """
        Identifica fraquezas baseado nos scores DISC.
        
        Args:
            scores: Dict com scores D, I, S, C
            
        Returns:
            Lista de fraquezas identificadas
        """
        gaps = []
        
        # Limiares para identificar fraquezas
        weak_threshold = 0.4
        
        if scores.get('D', 0.5) < weak_threshold:
            gaps.append("D_baixa")
        if scores.get('I', 0.5) < weak_threshold:
            gaps.append("I_baixa")
        if scores.get('S', 0.5) < weak_threshold:
            gaps.append("S_baixa")
        if scores.get('C', 0.5) < weak_threshold:
            gaps.append("C_baixa")
        
        return gaps
    
    def build_plan(self, gaps: List[str]) -> Dict[str, Any]:
        """
        Constrói plano de treino baseado nas fraquezas identificadas.
        
        Args:
            gaps: Lista de fraquezas (ex: ["D_baixa", "C_baixa"])
            
        Returns:
            Dict com módulos e dicas de treino
        """
        modules = []
        tips = []
        
        # Adicionar módulos específicos para cada fraqueza
        for gap in gaps:
            if gap in self.disc_gaps:
                cfg = self.disc_gaps[gap]
                modules.extend(cfg["modules"])
                tips.extend(cfg["tips"])
        
        # Verificar combinações específicas
        gap_key = "_".join(sorted(gaps))
        if gap_key in self.combination_modules:
            modules.extend(self.combination_modules[gap_key])
        
        # Remover duplicatas e limitar
        unique_modules = []
        seen_ids = set()
        for module in modules:
            if module["id"] not in seen_ids:
                unique_modules.append(module)
                seen_ids.add(module["id"])
        
        # Limitar a 6 módulos principais
        unique_modules = unique_modules[:6]
        
        # Remover dicas duplicadas e limitar
        unique_tips = list(dict.fromkeys(tips))[:8]
        
        # Calcular duração total
        total_duration = sum(int(module["duration"].replace("m", "")) for module in unique_modules)
        
        plan = {
            "modules": unique_modules,
            "tips": unique_tips,
            "total_duration_minutes": total_duration,
            "estimated_weeks": max(1, total_duration // 60),  # 1h por semana
            "priority_gaps": gaps[:3]  # Top 3 fraquezas
        }
        
        logger.info(f"Plano de treino criado: {len(unique_modules)} módulos, "
                   f"{len(unique_tips)} dicas, {total_duration}min total")
        
        return plan
    
    def get_quick_tips(self, gaps: List[str], context: str = "call") -> List[str]:
        """
        Retorna dicas rápidas para uso durante calls.
        
        Args:
            gaps: Lista de fraquezas
            context: Contexto ("call", "prep", "followup")
            
        Returns:
            Lista de dicas rápidas
        """
        quick_tips = []
        
        for gap in gaps:
            if gap in self.disc_gaps:
                tips = self.disc_gaps[gap]["tips"]
                
                # Filtrar por contexto se necessário
                if context == "call":
                    # Dicas para usar durante a call
                    quick_tips.extend(tips[:2])  # Top 2 dicas
                elif context == "prep":
                    # Dicas para preparação
                    quick_tips.extend([f"Prepare-se para: {self.disc_gaps[gap]['description']}"])
        
        return list(dict.fromkeys(quick_tips))[:5]  # Máximo 5 dicas
    
    def get_progress_tracking(self, gaps: List[str]) -> Dict[str, Any]:
        """
        Define métricas para acompanhar progresso.
        
        Args:
            gaps: Lista de fraquezas
            
        Returns:
            Dict com métricas de acompanhamento
        """
        metrics = {}
        
        for gap in gaps:
            if gap == "D_baixa":
                metrics["assertiveness"] = {
                    "target": "Aumentar uso de imperativos em 30%",
                    "measure": "imperatives_score",
                    "baseline": 0.2,
                    "target_value": 0.5
                }
            elif gap == "I_baixa":
                metrics["empathy"] = {
                    "target": "Fazer 3+ perguntas abertas por call",
                    "measure": "open_questions_count",
                    "baseline": 1,
                    "target_value": 3
                }
            elif gap == "S_baixa":
                metrics["patience"] = {
                    "target": "Reduzir interrupções em 50%",
                    "measure": "interrupt_rate",
                    "baseline": 0.3,
                    "target_value": 0.15
                }
            elif gap == "C_baixa":
                metrics["structure"] = {
                    "target": "Usar estrutura em 80% das calls",
                    "measure": "structure_score",
                    "baseline": 0.25,
                    "target_value": 0.6
                }
        
        return metrics
    
    def get_mentor_context(self, gaps: List[str]) -> Dict[str, Any]:
        """
        Fornece contexto para o Mentor Engine usar nas dicas.
        
        Args:
            gaps: Lista de fraquezas
            
        Returns:
            Dict com contexto para coaching
        """
        context = {
            "disc_gaps": gaps,
            "focus_areas": [],
            "coaching_style": "supportive"
        }
        
        # Definir áreas de foco
        if "D_baixa" in gaps:
            context["focus_areas"].append("assertividade")
        if "I_baixa" in gaps:
            context["focus_areas"].append("empatia")
        if "S_baixa" in gaps:
            context["focus_areas"].append("paciência")
        if "C_baixa" in gaps:
            context["focus_areas"].append("estrutura")
        
        # Definir estilo de coaching
        if len(gaps) >= 3:
            context["coaching_style"] = "intensive"
        elif len(gaps) == 2:
            context["coaching_style"] = "balanced"
        else:
            context["coaching_style"] = "gentle"
        
        return context 
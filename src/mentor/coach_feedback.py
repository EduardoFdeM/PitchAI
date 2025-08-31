"""
Coach Feedback - Sistema de coaching e feedback aprimorado
=======================================================

Geração de tips em tempo real e feedback pós-call com IA.
"""

import logging
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta


# Tips estáticos por combinação (tier, stage, topic)
DEFAULT_TIPS = {
    # Cliente difícil
    ("dificil", "negociacao", "preco"): [
        "Ancore em ROI antes de discutir desconto",
        "Valide o decisor e proponha próximo passo com ele",
        "Foque no valor percebido, não no preço"
    ],
    ("dificil", "negociacao", "autoridade"): [
        "Identifique quem tem poder de decisão real",
        "Peça introdução ao decisor de forma natural",
        "Demonstre valor antes de pedir acesso ao decisor"
    ],
    ("dificil", "proposta", "preco"): [
        "Personalize proposta com benefícios específicos",
        "Inclua ROI calculado e casos de sucesso",
        "Ofereça opções de pagamento flexíveis"
    ],
    
    # Cliente médio
    ("medio", "negociacao", "preco"): [
        "Explique valor vs custo de forma clara",
        "Ofereça desconto pequeno se necessário",
        "Foque em benefícios que resolvem problemas"
    ],
    ("medio", "proposta", "timing"): [
        "Defina cronograma realista",
        "Explique por que a implementação é rápida",
        "Ofereça suporte durante transição"
    ],
    ("medio", "avanco", "necessidade"): [
        "Descubra necessidades não atendidas",
        "Conecte solução com problemas reais",
        "Agende demonstração personalizada"
    ],
    
    # Cliente fácil
    ("facil", "descoberta", "necessidade"): [
        "Mantenha conversa fluida e natural",
        "Descubra mais sobre o negócio",
        "Construa rapport antes de vender"
    ],
    ("facil", "avanco", "timing"): [
        "Agende próxima reunião rapidamente",
        "Mantenha momentum da conversa",
        "Envie follow-up personalizado"
    ],
    
    # Tips genéricos por stage
    ("descoberta",): [
        "Faça perguntas abertas para descobrir necessidades",
        "Escute atentamente e tome notas",
        "Conecte com benefícios relevantes"
    ],
    ("avanco",): [
        "Agende próxima reunião com agenda clara",
        "Envolva decisor na próxima conversa",
        "Envie resumo da reunião com próximos passos"
    ],
    ("proposta",): [
        "Personalize proposta com benefícios específicos",
        "Inclua casos de sucesso relevantes",
        "Defina cronograma claro de implementação"
    ],
    ("negociacao",): [
        "Negocie termos, não apenas preço",
        "Foque em valor percebido vs custo",
        "Peça o fechamento de forma direta"
    ],
    ("fechamento",): [
        "Peça o fechamento de forma clara",
        "Resolva objeções finais rapidamente",
        "Defina próximos passos pós-fechamento"
    ]
}


class CoachFeedback:
    """Sistema de coaching e feedback aprimorado."""
    
    def __init__(self, llm_client=None, dao_mentor=None, timeout_s: float = 2.0):
        self.llm = llm_client
        self.dao = dao_mentor
        self.timeout_s = timeout_s
        self.logger = logging.getLogger(__name__)
        
        # Cache de feedback personalizado
        self.personalized_cache = {}
        self.cache_ttl = 3600  # 1 hora
        
        # Cache de métricas de vendedor para otimização
        self.seller_metrics_cache = {}
        self.metrics_cache_ttl = 1800  # 30 minutos
        
        # Cache de padrões de sucesso
        self.success_patterns_cache = {}
        self.patterns_cache_ttl = 7200  # 2 horas
    
    def realtime_tips(self, tier: str, stage: str, topic: str, 
                     seller_id: str = None, client_id: str = None) -> List[str]:
        """
        Gerar tips em tempo real aprimorados.
        
        Args:
            tier: Tier do cliente (facil|medio|dificil)
            stage: Stage atual
            topic: Tópico principal (objeção ou interesse)
            seller_id: ID do vendedor para personalização
            client_id: ID do cliente para contexto
            
        Returns:
            Lista de tips personalizados
        """
        # Validação e sanitização de entrada
        if not tier or not stage or not topic:
            self.logger.warning("⚠️ Parâmetros inválidos para realtime_tips")
            return self._get_enhanced_generic_tips("medio", "descoberta", "geral")
        
        # Sanitizar valores
        tier = tier.lower().strip()
        stage = stage.lower().strip()
        topic = topic.lower().strip()
        
        # Validar valores permitidos
        valid_tiers = {"facil", "medio", "dificil"}
        valid_stages = {"descoberta", "avanco", "proposta", "negociacao", "fechamento"}
        
        if tier not in valid_tiers:
            self.logger.warning(f"⚠️ Tier inválido: {tier}, usando 'medio'")
            tier = "medio"
        
        if stage not in valid_stages:
            self.logger.warning(f"⚠️ Stage inválido: {stage}, usando 'descoberta'")
            stage = "descoberta"
        
        # 1. Tentar tips personalizados baseados em histórico
        if seller_id and self.dao:
            try:
                personalized_tips = self._get_personalized_tips(
                    seller_id, tier, stage, topic, client_id
                )
                if personalized_tips:
                    return personalized_tips
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao buscar tips personalizados: {e}")
        
        # 2. Tentar combinação específica
        specific_key = (tier, stage, topic)
        if specific_key in DEFAULT_TIPS:
            return DEFAULT_TIPS[specific_key]
        
        # 3. Tentar combinação tier + stage
        tier_stage_key = (tier, stage)
        for key, tips in DEFAULT_TIPS.items():
            if len(key) == 2 and key == tier_stage_key:
                return tips
        
        # 4. Tentar apenas stage
        stage_key = (stage,)
        if stage_key in DEFAULT_TIPS:
            return DEFAULT_TIPS[stage_key]
        
        # 5. Tips genéricos aprimorados
        return self._get_enhanced_generic_tips(tier, stage, topic)
    
    def _get_personalized_tips(self, seller_id: str, tier: str, stage: str, 
                              topic: str, client_id: str = None) -> List[str]:
        """Obter tips personalizados baseados no histórico do vendedor."""
        try:
            # Verificar cache
            cache_key = f"{seller_id}:{tier}:{stage}:{topic}"
            if cache_key in self.personalized_cache:
                cached_data = self.personalized_cache[cache_key]
                if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                    return cached_data["tips"]
            
            # Buscar histórico de sucesso do vendedor
            success_patterns = self._analyze_seller_success_patterns(seller_id, tier, stage)
            
            if success_patterns:
                tips = self._generate_tips_from_patterns(success_patterns, topic)
                
                # Cache
                self.personalized_cache[cache_key] = {
                    "tips": tips,
                    "timestamp": datetime.now().timestamp()
                }
                
                return tips
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao buscar tips personalizados: {e}")
        
        return []
    
    def _analyze_seller_success_patterns(self, seller_id: str, tier: str, stage: str) -> Dict[str, Any]:
        """Analisar padrões de sucesso do vendedor."""
        try:
            # Buscar calls bem-sucedidas do vendedor
            successful_calls = self.dao.get_seller_successful_calls(seller_id, tier, stage, limit=10)
            
            if not successful_calls:
                return {}
            
            # Analisar padrões comuns
            patterns = {
                "avg_engagement": 0.0,
                "avg_sentiment": 0.0,
                "common_topics": [],
                "avg_duration": 0,
                "objection_handling": []
            }
            
            total_engagement = 0
            total_sentiment = 0
            total_duration = 0
            topics_count = {}
            objections_handled = []
            
            for call in successful_calls:
                total_engagement += call.get("engagement", 0.0)
                total_sentiment += call.get("avg_valence", 0.0)
                total_duration += call.get("duration", 0)
                
                # Contar tópicos
                topics = call.get("topics", [])
                for topic in topics:
                    topics_count[topic] = topics_count.get(topic, 0) + 1
                
                # Objeções resolvidas
                if call.get("objections_resolved", 0) > 0:
                    objections_handled.append(call.get("objections_count", 0))
            
            if successful_calls:
                patterns["avg_engagement"] = total_engagement / len(successful_calls)
                patterns["avg_sentiment"] = total_sentiment / len(successful_calls)
                patterns["avg_duration"] = total_duration / len(successful_calls)
                patterns["common_topics"] = sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:3]
                patterns["objection_handling"] = objections_handled
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao analisar padrões: {e}")
            return {}
    
    def _generate_tips_from_patterns(self, patterns: Dict[str, Any], topic: str) -> List[str]:
        """Gerar tips baseados em padrões de sucesso."""
        tips = []
        
        # Tips baseados em engajamento
        if patterns.get("avg_engagement", 0) > 0.7:
            tips.append("🎯 Seu histórico mostra alto engajamento - mantenha o ritmo")
        
        # Tips baseados em sentimento
        if patterns.get("avg_sentiment", 0) > 0.3:
            tips.append("😊 Você tem histórico de manter sentimento positivo")
        
        # Tips baseados em tópicos comuns
        common_topics = patterns.get("common_topics", [])
        if common_topics:
            top_topic = common_topics[0][0]
            if top_topic == topic:
                tips.append(f"💡 {topic.title()} é seu tópico forte - aproveite")
        
        # Tips baseados em handling de objeções
        objection_handling = patterns.get("objection_handling", [])
        if objection_handling and len(objection_handling) > 2:
            tips.append("🛡️ Você tem histórico de resolver objeções - confie na sua técnica")
        
        return tips[:3]  # Limitar a 3 tips
    
    def _get_enhanced_generic_tips(self, tier: str, stage: str, topic: str) -> List[str]:
        """Obter tips genéricos aprimorados."""
        tips = [
            "Escute atentamente e faça perguntas abertas",
            "Conecte benefícios com necessidades do cliente",
            "Mantenha foco no valor, não apenas no preço"
        ]
        
        # Adicionar tips específicos por tier
        if tier == "dificil":
            tips.append("⏰ Seja paciente - clientes difíceis precisam de mais tempo")
        elif tier == "facil":
            tips.append("🚀 Aproveite o momentum - clientes fáceis respondem bem a urgência")
        
        # Adicionar tips por stage
        if stage == "descoberta":
            tips.append("🔍 Descubra problemas não mencionados")
        elif stage == "negociacao":
            tips.append("💰 Negocie valor, não apenas desconto")
        
        return tips[:4]  # Limitar a 4 tips
    
    def post_call_feedback(self, summary_text: str, tier: str, stage: str, 
                          topics: List[str], call_metrics: Dict[str, Any],
                          seller_id: str = None) -> Tuple[List[str], str]:
        """
        Gerar feedback pós-call aprimorado.
        
        Args:
            summary_text: Texto do resumo da call
            tier: Tier do cliente
            stage: Stage atual
            topics: Tópicos identificados
            call_metrics: Métricas da call
            seller_id: ID do vendedor para personalização
            
        Returns:
            Tuple (feedback_bullets, training_task)
        """
        try:
            # Tentar LLM se disponível
            if self.llm:
                return self._generate_llm_feedback(summary_text, tier, stage, topics, call_metrics, seller_id)
        except Exception as e:
            self.logger.warning(f"⚠️ LLM falhou, usando template: {e}")
        
        # Fallback para template aprimorado
        return self._generate_enhanced_template_feedback(tier, stage, topics, call_metrics, seller_id)
    
    def _generate_llm_feedback(self, summary_text: str, tier: str, stage: str,
                             topics: List[str], call_metrics: Dict[str, Any],
                             seller_id: str = None) -> Tuple[List[str], str]:
        """Gerar feedback usando LLM."""
        try:
            # Verificar se o LLM está disponível e é um AnythingLLMClient
            if not self.llm or not hasattr(self.llm, 'generate_objection_suggestions'):
                self.logger.warning("⚠️ LLM não disponível ou não é AnythingLLMClient")
                return self._generate_enhanced_template_feedback(tier, stage, topics, call_metrics, seller_id)
            
            # Preparar contexto para o LLM
            context = {
                "summary": summary_text[:1000],  # Limitar tamanho
                "tier": tier,
                "stage": stage,
                "topics": topics,
                "metrics": {
                    "sentiment": call_metrics.get("sentiment_avg", 0.0),
                    "engagement": call_metrics.get("engagement", 0.0),
                    "objections": call_metrics.get("objections_count", 0),
                    "talk_ratio": call_metrics.get("client_talk_ratio", 0.0),
                    "duration": call_metrics.get("duration", 0)
                }
            }
            
            # Buscar histórico do vendedor se disponível
            seller_context = ""
            if seller_id and self.dao:
                try:
                    seller_history = self.dao.get_seller_recent_performance(seller_id, limit=3)
                    if seller_history:
                        avg_xp = sum(h.get("xp_earned", 0) for h in seller_history) / len(seller_history)
                        avg_engagement = sum(h.get("engagement", 0) for h in seller_history) / len(seller_history)
                        seller_context = f"\nHistórico do vendedor (últimas 3 calls):\n- XP médio: {avg_xp:.1f}\n- Engajamento médio: {avg_engagement:.2f}"
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao buscar histórico: {e}")
            
            # Criar passagens para o RAG
            from ai.rag_service import RAGPassage
            
            # Passagens baseadas no contexto da call
            passages = [
                RAGPassage(
                    id="call_summary",
                    title="Resumo da Call",
                    snippet=context["summary"][:200] + "...",
                    score=1.0
                ),
                RAGPassage(
                    id="call_metrics",
                    title="Métricas da Call",
                    snippet=f"Tier: {tier}, Stage: {stage}, Sentimento: {context['metrics']['sentiment']:.2f}, Engajamento: {context['metrics']['engagement']:.2f}",
                    score=0.9
                )
            ]
            
            # Adicionar passagens específicas por tópico
            for topic in topics:
                passages.append(RAGPassage(
                    id=f"topic_{topic}",
                    title=f"Tópico: {topic}",
                    snippet=f"Tópico principal identificado: {topic}",
                    score=0.8
                ))
            
            # Prompt para o LLM
            objection_text = f"Call com cliente {tier} no stage {stage}. Tópicos: {', '.join(topics)}"
            
            # Gerar sugestões usando AnythingLLM
            rag_response = self.llm.generate_objection_suggestions(
                objection=objection_text,
                passages=passages,
                temperature=0.7
            )
            
            if rag_response and rag_response.suggestions:
                # Extrair feedback das sugestões
                feedback_bullets = []
                for suggestion in rag_response.suggestions[:3]:  # Top 3 sugestões
                    feedback_bullets.append(suggestion.text)
                
                # Gerar tarefa de treino baseada no contexto
                training_task = self._generate_llm_training_task(
                    context, seller_context, rag_response
                )
                
                return feedback_bullets, training_task
            
        except Exception as e:
            self.logger.error(f"❌ Erro no LLM feedback: {e}")
        
        # Fallback para template
        return self._generate_enhanced_template_feedback(tier, stage, topics, call_metrics, seller_id)
    
    def _generate_llm_training_task(self, context: Dict[str, Any], seller_context: str, 
                                  rag_response) -> str:
        """Gerar tarefa de treino usando insights do LLM."""
        try:
            # Analisar métricas para identificar área de foco
            metrics = context["metrics"]
            tier = context["tier"]
            
            # Identificar área de melhoria baseada nas métricas
            if metrics["sentiment"] < 0:
                focus_area = "rapport e empatia"
            elif metrics["engagement"] < 0.5:
                focus_area = "engajamento e perguntas abertas"
            elif metrics["objections"] > 2:
                focus_area = "handling de objeções"
            elif tier == "dificil":
                focus_area = "técnicas para clientes difíceis"
            else:
                focus_area = "avanço de stage"
            
            # Criar tarefa específica
            if rag_response and rag_response.suggestions:
                # Usar insights do LLM para personalizar a tarefa
                first_suggestion = rag_response.suggestions[0].text.lower()
                if "pergunta" in first_suggestion or "explorar" in first_suggestion:
                    return f"Praticar técnicas de {focus_area} com foco em perguntas abertas"
                elif "valor" in first_suggestion or "benefício" in first_suggestion:
                    return f"Trabalhar {focus_area} com ênfase em demonstração de valor"
                else:
                    return f"Focar em {focus_area} na próxima call"
            else:
                return f"Praticar técnicas de {focus_area}"
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao gerar tarefa LLM: {e}")
            return "Revisar técnicas de vendas gerais"
    
    def _generate_enhanced_template_feedback(self, tier: str, stage: str, topics: List[str],
                                           call_metrics: Dict[str, Any], seller_id: str = None) -> Tuple[List[str], str]:
        """Gerar feedback usando template aprimorado."""
        feedback_bullets = []
        training_task = ""
        
        # Análise de sentimento aprimorada
        sentiment_avg = call_metrics.get("sentiment_avg", 0.0)
        if sentiment_avg >= 0.3:
            feedback_bullets.append("✅ Sentimento positivo mantido durante a call")
        elif sentiment_avg <= -0.3:
            feedback_bullets.append("⚠️ Sentimento negativo - trabalhe rapport e empatia")
        else:
            feedback_bullets.append("📊 Sentimento neutro - busque mais engajamento emocional")
        
        # Engajamento com contexto
        engagement = call_metrics.get("engagement", 0.0)
        if engagement >= 0.7:
            feedback_bullets.append("✅ Alto engajamento do cliente - excelente interação")
        elif engagement <= 0.3:
            feedback_bullets.append("⚠️ Baixo engajamento - melhore perguntas e storytelling")
        else:
            feedback_bullets.append("📈 Engajamento médio - há espaço para melhorar")
        
        # Equilíbrio de fala com insights
        client_talk_ratio = call_metrics.get("client_talk_ratio", 0.0)
        if client_talk_ratio >= 0.5:
            feedback_bullets.append("✅ Bom equilíbrio - cliente falou adequadamente")
        elif client_talk_ratio >= 0.3:
            feedback_bullets.append("⚠️ Cliente falou pouco - faça mais perguntas abertas")
        else:
            feedback_bullets.append("🚨 Cliente muito quieto - verifique se está confortável")
        
        # Objeções com análise de qualidade
        objections_count = call_metrics.get("objections_count", 0)
        objections_resolved = call_metrics.get("objections_resolved", 0)
        
        if objections_count == 0:
            feedback_bullets.append("✅ Nenhuma objeção detectada - call fluida")
        elif objections_resolved >= objections_count:
            feedback_bullets.append(f"🎯 {objections_count} objeção(ões) - todas resolvidas com sucesso")
        else:
            feedback_bullets.append(f"⚠️ {objections_count} objeções - {objections_resolved} resolvidas")
        
        # Análise de duração da call
        call_duration = call_metrics.get("duration", 0)
        if call_duration > 0:
            if call_duration < 300:  # < 5 min
                feedback_bullets.append("⏱️ Call curta - considere explorar mais necessidades")
            elif call_duration > 1800:  # > 30 min
                feedback_bullets.append("⏱️ Call longa - mantenha foco nos objetivos principais")
        
        # Tarefa de treino personalizada
        training_task = self._generate_personalized_training_task(
            tier, stage, topics, call_metrics, seller_id
        )
        
        return feedback_bullets, training_task
    
    def _generate_personalized_training_task(self, tier: str, stage: str, topics: List[str],
                                           call_metrics: Dict[str, Any], seller_id: str = None) -> str:
        """Gerar tarefa de treino personalizada."""
        # Análise de fraquezas baseada em métricas
        weaknesses = []
        
        if call_metrics.get("sentiment_avg", 0) < 0:
            weaknesses.append("trabalhar rapport")
        
        if call_metrics.get("engagement", 0) < 0.5:
            weaknesses.append("melhorar engajamento")
        
        if call_metrics.get("client_talk_ratio", 0) < 0.4:
            weaknesses.append("fazer mais perguntas abertas")
        
        if call_metrics.get("objections_count", 0) > 3:
            weaknesses.append("técnicas de handling de objeções")
        
        # Tarefa baseada em fraquezas
        if weaknesses:
            if len(weaknesses) == 1:
                return f"Focar em {weaknesses[0]} na próxima call"
            else:
                return f"Praticar: {', '.join(weaknesses[:2])}"
        
        # Tarefa baseada no tier/stage
        if tier == "dificil":
            if "autoridade" in topics:
                return "Estudar técnicas de acesso ao decisor e cases de sucesso"
            elif "preco" in topics:
                return "Praticar anchoring de valor e ROI calculation"
            else:
                return "Rever playbook de clientes difíceis"
        elif tier == "medio":
            if "timing" in topics:
                return "Praticar técnicas de urgência e cronograma"
            else:
                return "Estudar técnicas de proposta personalizada"
        else:
            return "Manter momentum e técnicas de avanço rápido"
    
    def get_tips_for_objection(self, objection_category: str, tier: str, stage: str,
                              seller_id: str = None) -> List[str]:
        """
        Obter tips específicos para uma objeção.
        
        Args:
            objection_category: Categoria da objeção
            tier: Tier do cliente
            stage: Stage atual
            seller_id: ID do vendedor para personalização
            
        Returns:
            Lista de tips para a objeção
        """
        return self.realtime_tips(tier, stage, objection_category, seller_id)
    
    def get_stage_transition_tips(self, from_stage: str, to_stage: str,
                                seller_id: str = None) -> List[str]:
        """
        Obter tips para transição de stage.
        
        Args:
            from_stage: Stage anterior
            to_stage: Stage atual
            seller_id: ID do vendedor para personalização
            
        Returns:
            Lista de tips para a transição
        """
        transitions = {
            ("descoberta", "avanco"): [
                "Agende próxima reunião com agenda clara",
                "Envolva decisor na próxima conversa",
                "Envie resumo com próximos passos"
            ],
            ("avanco", "proposta"): [
                "Personalize proposta com necessidades identificadas",
                "Inclua casos de sucesso relevantes",
                "Defina cronograma de implementação"
            ],
            ("proposta", "negociacao"): [
                "Prepare-se para objeções de preço",
                "Tenha alternativas de termos prontas",
                "Foque em valor vs custo"
            ],
            ("negociacao", "fechamento"): [
                "Peça o fechamento de forma direta",
                "Resolva objeções finais rapidamente",
                "Defina próximos passos pós-fechamento"
            ]
        }
        
        base_tips = transitions.get((from_stage, to_stage), [
            "Mantenha momentum da conversa",
            "Foque nos próximos passos",
            "Documente progresso da oportunidade"
        ])
        
        # Adicionar personalização se disponível
        if seller_id and self.dao:
            seller_tips = self._get_seller_stage_transition_tips(seller_id, from_stage, to_stage)
            if seller_tips:
                base_tips.extend(seller_tips)
        
        return base_tips[:4]  # Limitar a 4 tips
    
    def _get_seller_stage_transition_tips(self, seller_id: str, from_stage: str, to_stage: str) -> List[str]:
        """Obter tips específicos do vendedor para transição de stage."""
        try:
            # Buscar histórico de transições bem-sucedidas
            successful_transitions = self.dao.get_seller_stage_transitions(
                seller_id, from_stage, to_stage, limit=5
            )
            
            if not successful_transitions:
                return []
            
            # Analisar padrões de sucesso
            tips = []
            
            # Verificar se há padrão de duração
            avg_duration = sum(t.get("duration", 0) for t in successful_transitions) / len(successful_transitions)
            if avg_duration > 1200:  # > 20 min
                tips.append("⏱️ Suas transições bem-sucedidas são mais longas - não tenha pressa")
            
            # Verificar se há padrão de objeções
            avg_objections = sum(t.get("objections_count", 0) for t in successful_transitions) / len(successful_transitions)
            if avg_objections > 2:
                tips.append("🛡️ Você tem histórico de lidar bem com objeções nesta transição")
            
            return tips
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao buscar tips de transição: {e}")
            return [] 
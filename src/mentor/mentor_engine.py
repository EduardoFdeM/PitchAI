"""
Mentor Engine - Orquestrador principal do sistema de mentoring
============================================================

Coordena classificação de clientes, coaching e gamificação.
"""

import uuid
import time
import logging
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.data.dao_mentor import DAOMentor
from src.client_profile.service import ClientProfileService
from .coach_feedback import CoachFeedback
from .xp_rules import compute_xp, level_from_xp


class MentorEngine(QObject):
    """Orquestrador principal do sistema de mentoring."""
    
    # Sinais para UI
    mentor_client_context = pyqtSignal(object)  # Dict com contexto do cliente
    mentor_update = pyqtSignal(object)          # Dict com insights em tempo real
    mentor_coaching = pyqtSignal(object)        # Dict com feedback pós-call
    xp_awarded = pyqtSignal(object)             # Dict com XP ganho
    leaderboard_updated = pyqtSignal(object)    # Dict com leaderboard
    
    def __init__(self, event_bus, dao: DAOMentor, client_profile_service: ClientProfileService, 
                 coach: CoachFeedback, disc_batch_job=None):
        super().__init__()
        self.event_bus = event_bus
        self.dao = dao
        self.cps = client_profile_service
        self.coach = coach
        self.disc_batch_job = disc_batch_job  # Integração DISC
        self.logger = logging.getLogger(__name__)
        
        # Estado atual por call_id
        self.current_calls: Dict[str, Dict[str, Any]] = {}
        
        # Métricas de performance
        self.performance_metrics = {
            "calls_processed": 0,
            "tips_generated": 0,
            "feedback_generated": 0,
            "xp_awarded": 0,
            "errors_count": 0,
            "avg_processing_time_ms": 0.0
        }
        
        # Conectar ao EventBus
        self._wire_to_event_bus()
        
        self.logger.info("✅ MentorEngine inicializado")
    
    def _wire_to_event_bus(self):
        """Conectar aos eventos do sistema."""
        # Eventos de call
        self.event_bus.subscribe("call.started", self.on_call_started)
        self.event_bus.subscribe("call.stopped", self.on_call_stopped)
        
        # Eventos de análise
        self.event_bus.subscribe("sentiment.update", self.on_sentiment_update)
        self.event_bus.subscribe("objection.detected", self.on_objection_detected)
        self.event_bus.subscribe("summary.ready", self.on_summary_ready)
        
        # Eventos DISC
        self.event_bus.subscribe("disc.profile.updated", self.on_disc_profile_updated)
        self.event_bus.subscribe("mentor.disc.context", self.on_disc_context)
        
        self.logger.info("🔗 MentorEngine conectado ao EventBus")
    
    def on_call_started(self, event: Dict[str, Any]):
        """Handler para início de call."""
        try:
            call_id = event.get("call_id")
            if not call_id:
                self.logger.error("❌ call_id não fornecido no evento call.started")
                return
                
            seller_id = event.get("seller_id", "default_seller")
            client_id = event.get("client_id", "unknown_client")
            client_name = event.get("client_name", "Cliente")
            
            self.logger.info(f"🎤 Call iniciada: {call_id} - {client_name}")
            
            # 1. Criar/buscar cliente com tratamento de erro
            try:
                self.cps.get_or_create(client_id, client_name)
            except Exception as e:
                self.logger.error(f"❌ Erro ao criar/buscar cliente {client_id}: {e}")
                # Continuar com cliente padrão
                client_id = "unknown_client"
                client_name = "Cliente"
            
            # 2. Buscar estado atual do cliente
            try:
                client_context = self.cps.get_client_context(client_id)
                stage_before = client_context.get("stage", "descoberta")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao buscar contexto do cliente {client_id}: {e}")
                client_context = {"tier": "medio", "stage": "descoberta", "topics": []}
                stage_before = "descoberta"
            
            # 3. Inicializar estado da call
            self.current_calls[call_id] = {
                "seller_id": seller_id,
                "client_id": client_id,
                "client_name": client_name,
                "stage_before": stage_before,
                "start_time": int(time.time() * 1000),
                "metrics": {
                    "top_objections": [],
                    "objections_count": 0,
                    "sentiment_avg": 0.0,
                    "engagement": 0.0,
                    "client_talk_ratio": 0.0,
                    "resolved_dominant": False,
                    "complexity_delta": 0.0
                },
                "summary_text": ""
            }
            
            # 4. Publicar contexto inicial para UI com tratamento de erro
            try:
                self.mentor_client_context.emit(client_context)
                self.event_bus.publish("mentor.client_context", client_context)
                self.logger.debug(f"📋 Contexto publicado: {client_id} -> {client_context['tier']}/{client_context['stage']}")
            except Exception as e:
                self.logger.error(f"❌ Erro ao publicar contexto: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro crítico no início da call: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def on_sentiment_update(self, event: Dict[str, Any]):
        """Handler para atualizações de sentimento."""
        try:
            call_id = event.get("call_id")
            if call_id not in self.current_calls:
                return
            
            # Usar dados do cliente (loopback) para métricas
            source = event.get("source", "")
            if source == "loopback":  # Cliente
                call_state = self.current_calls[call_id]
                metrics = call_state["metrics"]
                
                valence = float(event.get("valence", 0.0))
                engagement = float(event.get("engagement", 0.0))
                
                # Média móvel simples (alpha = 0.9)
                metrics["sentiment_avg"] = 0.9 * metrics.get("sentiment_avg", 0.0) + 0.1 * valence
                metrics["engagement"] = 0.9 * metrics.get("engagement", 0.0) + 0.1 * engagement
                
                self.logger.debug(f"📊 Sentimento cliente: {call_id} - val: {valence:.2f}, eng: {engagement:.2f}")
            
            # Também processar dados do vendedor (mic) se necessário
            elif source == "mic":  # Vendedor
                # Processar métricas do vendedor se necessário
                # Por exemplo, calcular client_talk_ratio
                pass
                
        except Exception as e:
            self.logger.error(f"❌ Erro no sentimento: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def on_objection_detected(self, event: Dict[str, Any]):
        """Handler para objeções detectadas."""
        try:
            call_id = event.get("call_id")
            if call_id not in self.current_calls:
                return
            
            objection_category = event.get("category", "unknown")
            ts_ms = event.get("ts_ms", int(time.time() * 1000))
            
            # Atualizar métricas
            call_state = self.current_calls[call_id]
            metrics = call_state["metrics"]
            
            metrics["objections_count"] += 1
            if objection_category not in metrics["top_objections"]:
                metrics["top_objections"].append(objection_category)
            
            # ✅ Implementar tracking de objeções resolvidas
            if "objections_tracking" not in call_state:
                call_state["objections_tracking"] = []
            
            objection_id = f"{call_id}_{len(call_state['objections_tracking'])}"
            objection_record = {
                "id": objection_id,
                "category": objection_category,
                "timestamp": ts_ms,
                "resolved": False,
                "resolution_time": None,
                "resolution_method": None
            }
            call_state["objections_tracking"].append(objection_record)
            
            # Gerar tips em tempo real aprimorados
            client_context = self.cps.get_client_context(call_state["client_id"])
            tips = self.coach.realtime_tips(
                client_context["tier"],
                client_context["stage"],
                objection_category,
                seller_id=call_state["seller_id"],  # ✅ Adicionar seller_id para personalização
                client_id=call_state["client_id"]
            )
            
            # Publicar insight para UI
            insight_event = {
                "call_id": call_id,
                "client_id": call_state["client_id"],
                "objection_id": objection_id,
                "window_ms": ts_ms,
                "insight": tips[0] if tips else "Objeção detectada - mantenha calma",
                "tips": tips
            }
            
            self.event_bus.publish("mentor.update", insight_event)
            
            self.logger.info(f"🚨 Objeção: {call_id} - {objection_category} (ID: {objection_id})")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na objeção: {e}")
    
    def mark_objection_resolved(self, call_id: str, objection_id: str, resolution_method: str = "manual"):
        """Marcar objeção como resolvida."""
        try:
            if call_id not in self.current_calls:
                self.logger.warning(f"Call {call_id} não encontrada para marcar objeção resolvida")
                return False
            
            call_state = self.current_calls[call_id]
            if "objections_tracking" not in call_state:
                self.logger.warning(f"Nenhum tracking de objeções para call {call_id}")
                return False
            
            # Encontrar e marcar objeção
            for objection in call_state["objections_tracking"]:
                if objection["id"] == objection_id:
                    objection["resolved"] = True
                    objection["resolution_time"] = int(time.time() * 1000)
                    objection["resolution_method"] = resolution_method
                    
                    # Atualizar métricas
                    metrics = call_state["metrics"]
                    if "objections_resolved" not in metrics:
                        metrics["objections_resolved"] = 0
                    metrics["objections_resolved"] += 1
                    
                    self.logger.info(f"✅ Objeção resolvida: {objection_id} via {resolution_method}")
                    return True
            
            self.logger.warning(f"Objeção {objection_id} não encontrada")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao marcar objeção resolvida: {e}")
            return False
    
    def get_objections_summary(self, call_id: str) -> Dict[str, Any]:
        """Obter resumo das objeções da call."""
        try:
            if call_id not in self.current_calls:
                return {"total": 0, "resolved": 0, "pending": 0, "details": []}
            
            call_state = self.current_calls[call_id]
            if "objections_tracking" not in call_state:
                return {"total": 0, "resolved": 0, "pending": 0, "details": []}
            
            objections = call_state["objections_tracking"]
            resolved_count = sum(1 for obj in objections if obj["resolved"])
            
            return {
                "total": len(objections),
                "resolved": resolved_count,
                "pending": len(objections) - resolved_count,
                "resolution_rate": resolved_count / len(objections) if objections else 0.0,
                "details": objections
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter resumo de objeções: {e}")
            return {"total": 0, "resolved": 0, "pending": 0, "details": []}
    
    def on_summary_ready(self, event: Dict[str, Any]):
        """Handler para resumo pronto."""
        try:
            call_id = event.get("call_id")
            if call_id not in self.current_calls:
                return
            
            # Guardar texto do resumo para pós-call
            summary_json = event.get("summary_json", {})
            summary_text = summary_json.get("full_text", "")
            
            self.current_calls[call_id]["summary_text"] = summary_text
            
            self.logger.debug(f"📋 Resumo guardado: {call_id} ({len(summary_text)} chars)")
            
        except Exception as e:
            self.logger.error(f"❌ Erro no resumo: {e}")
    
    def on_call_stopped(self, event: Dict[str, Any]):
        """Handler para fim de call."""
        try:
            call_id = event.get("call_id")
            if call_id not in self.current_calls:
                return
            
            call_state = self.current_calls.pop(call_id)
            self.logger.info(f"⏹️ Call finalizada: {call_id}")
            
            # 1. Atualizar perfil do cliente
            profile_update = self.cps.update_from_call(
                call_id=call_id,
                seller_id=call_state["seller_id"],
                client_id=call_state["client_id"],
                summary_text=call_state["summary_text"],
                call_metrics=call_state["metrics"]
            )
            
            # 2. Gerar feedback pós-call aprimorado
            feedback_bullets, training_task = self.coach.post_call_feedback(
                summary_text=call_state["summary_text"],
                tier=profile_update["tier"],
                stage=profile_update["stage"],
                topics=profile_update["topics"],
                call_metrics=call_state["metrics"],
                seller_id=call_state["seller_id"]  # ✅ Adicionar seller_id para personalização
            )
            
            # 2.1. Aprimorar feedback com insights DISC
            if self.disc_batch_job:
                enhanced_feedback = self.enhance_coaching_with_disc(
                    call_state["seller_id"], 
                    feedback_bullets
                )
                feedback_bullets = enhanced_feedback
            
            # 3. Calcular XP
            xp_earned = compute_xp(
                call_metrics=call_state["metrics"],
                client_tier=profile_update["tier"],
                stage_before=call_state["stage_before"],
                stage_after=profile_update["stage"]
            )
            
            # 4. Atualizar XP do vendedor
            new_total = self.dao.add_xp(
                seller_id=call_state["seller_id"],
                call_id=call_id,
                xp=xp_earned,
                reason="call"
            )
            
            # 5. Determinar novo nível
            new_level = level_from_xp(new_total)
            
            # 6. Obter resumo de objeções
            objections_summary = self.get_objections_summary(call_id)
            
            # 7. Persistir coaching
            self.dao.insert_call_coaching(
                call_id=call_id,
                seller_id=call_state["seller_id"],
                client_id=call_state["client_id"],
                customer_complexity=profile_update["tier"],
                objections_count=call_state["metrics"]["objections_count"],
                objections_resolved=objections_summary["resolved"],  # ✅ Implementado tracking
                avg_valence=call_state["metrics"]["sentiment_avg"],
                engagement=call_state["metrics"]["engagement"],
                xp_earned=xp_earned,
                feedback_short="\n".join(feedback_bullets),
                training_task=training_task
            )
            
            # 7. Publicar eventos com tratamento de erro
            self._safe_publish_events(call_id, call_state, profile_update, 
                                    feedback_bullets, training_task, xp_earned, 
                                    new_total, new_level)
            
            self.logger.info(f"✅ Call processada: {call_id} - XP: +{xp_earned}, Tier: {profile_update['tier']}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro no fim da call: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _safe_publish_events(self, call_id: str, call_state: Dict[str, Any], 
                           profile_update: Dict[str, Any], feedback_bullets: List[str],
                           training_task: str, xp_earned: int, new_total: int, 
                           new_level: str):
        """Publicar eventos com tratamento de erro robusto."""
        try:
            # Coaching event
            coaching_event = {
                "call_id": call_id,
                "client_id": call_state["client_id"],
                "seller_id": call_state["seller_id"],
                "complexity": profile_update["tier"],
                "feedback_short": feedback_bullets,
                "training_task": training_task
            }
            self.mentor_coaching.emit(coaching_event)  # ✅ Usar sinal PyQt6
            self.event_bus.publish("mentor.coaching", coaching_event)
            
            # XP event
            xp_event = {
                "seller_id": call_state["seller_id"],
                "call_id": call_id,
                "xp": xp_earned,
                "new_total": new_total,
                "level": new_level
            }
            self.xp_awarded.emit(xp_event)  # ✅ Usar sinal PyQt6
            self.event_bus.publish("xp.awarded", xp_event)
            
            # Leaderboard event
            leaderboard = self.dao.get_leaderboard(limit=10)
            leaderboard_event = {
                "top": leaderboard,
                "my_rank": self._get_seller_rank(call_state["seller_id"], leaderboard)
            }
            self.leaderboard_updated.emit(leaderboard_event)  # ✅ Usar sinal PyQt6
            self.event_bus.publish("leaderboard.updated", leaderboard_event)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao publicar eventos: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _safe_publish(self, event_type: str, payload: Dict[str, Any]):
        """Publicar evento com tratamento de erro."""
        try:
            self.event_bus.publish(event_type, payload)
        except Exception as e:
            self.logger.error(f"❌ Erro ao publicar {event_type}: {e}")
    
    def _get_seller_rank(self, seller_id: str, leaderboard: List[Dict[str, Any]]) -> int:
        """Obter rank do vendedor no leaderboard."""
        for i, seller in enumerate(leaderboard):
            if seller["id"] == seller_id:
                return i + 1
        return len(leaderboard) + 1
    
    def get_current_call_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Obter estado atual de uma call."""
        return self.current_calls.get(call_id)
    
    def get_seller_profile(self, seller_id: str) -> Dict[str, Any]:
        """Obter perfil completo do vendedor."""
        seller = self.dao.get_seller(seller_id)
        if not seller:
            return {
                "id": seller_id,
                "name": "Vendedor",
                "xp": 0,
                "level": "junior"
            }
        
        # Adicionar histórico de coaching
        coaching_history = self.dao.get_seller_coaching_history(seller_id, limit=5)
        
        # ✅ Adicionar análise de tendências e pontos fortes/fraquezas
        trends = self.dao.get_seller_trends(seller_id, days=90)
        strengths = self.dao.get_seller_strengths(seller_id, days=30)
        weaknesses = self.dao.get_seller_weaknesses(seller_id, days=30)
        
        return {
            **seller,
            "coaching_history": coaching_history,
            "trends": trends,
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def get_seller_analytics(self, seller_id: str) -> Dict[str, Any]:
        """
        Obter analytics completos do vendedor.
        
        Args:
            seller_id: ID do vendedor
            
        Returns:
            Dict com analytics completos
        """
        try:
            # Perfil básico
            profile = self.get_seller_profile(seller_id)
            
            # Performance recente
            recent_performance = self.dao.get_seller_recent_performance(seller_id, limit=10)
            
            # Análise de tendências
            trends = self.dao.get_seller_trends(seller_id, days=90)
            
            # Pontos fortes e fraquezas
            strengths = self.dao.get_seller_strengths(seller_id, days=30)
            weaknesses = self.dao.get_seller_weaknesses(seller_id, days=30)
            
            # Estatísticas por tier de cliente
            tier_stats = self._get_seller_tier_stats(seller_id)
            
            # Recomendações personalizadas
            recommendations = self._generate_seller_recommendations(
                seller_id, profile, trends, strengths, weaknesses
            )
            
            return {
                "profile": profile,
                "recent_performance": recent_performance,
                "trends": trends,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "tier_stats": tier_stats,
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar analytics: {e}")
            return {}
    
    def _get_seller_tier_stats(self, seller_id: str) -> Dict[str, Any]:
        """Obter estatísticas por tier de cliente."""
        try:
            cursor = self.dao.connection.cursor()
            cursor.execute(
                """SELECT cc.customer_complexity, 
                          COUNT(*) as total_calls,
                          AVG(cc.xp_earned) as avg_xp,
                          AVG(cc.engagement) as avg_engagement,
                          AVG(cc.avg_valence) as avg_valence,
                          SUM(cc.objections_count) as total_objections,
                          SUM(cc.objections_resolved) as total_resolved
                   FROM call_coaching cc
                   WHERE cc.seller_id = ?
                   GROUP BY cc.customer_complexity""",
                (seller_id,)
            )
            rows = cursor.fetchall()
            
            tier_stats = {}
            for row in rows:
                tier = row[0]
                tier_stats[tier] = {
                    "total_calls": row[1],
                    "avg_xp": row[2],
                    "avg_engagement": row[3],
                    "avg_valence": row[4],
                    "total_objections": row[5],
                    "total_resolved": row[6],
                    "resolution_rate": row[6] / row[5] if row[5] > 0 else 1.0
                }
            
            return tier_stats
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter tier stats: {e}")
            return {}
    
    def _generate_seller_recommendations(self, seller_id: str, profile: Dict[str, Any],
                                       trends: Dict[str, Any], strengths: Dict[str, Any],
                                       weaknesses: Dict[str, Any]) -> List[str]:
        """Gerar recomendações personalizadas para o vendedor."""
        recommendations = []
        
        # Recomendações baseadas em fraquezas
        weaknesses_list = weaknesses.get("weaknesses", [])
        if "baixo_engajamento" in weaknesses_list:
            recommendations.append("🎯 Pratique técnicas de storytelling e perguntas abertas para melhorar engajamento")
        
        if "sentimento_negativo" in weaknesses_list:
            recommendations.append("😊 Trabalhe rapport e empatia para manter sentimento positivo")
        
        if "objeções_não_resolvidas" in weaknesses_list:
            recommendations.append("🛡️ Estude técnicas de handling de objeções e prepare respostas")
        
        if "poucos_clientes_difíceis" in weaknesses_list:
            recommendations.append("💪 Aceite mais desafios com clientes difíceis para crescer")
        
        # Recomendações baseadas em tendências
        trends_data = trends.get("trends", {})
        if trends_data.get("xp") == "piorando":
            recommendations.append("📈 Revise suas estratégias - seu XP está diminuindo")
        
        if trends_data.get("engagement") == "piorando":
            recommendations.append("🎤 Foque em melhorar interação com clientes")
        
        # Recomendações baseadas em pontos fortes
        strengths_list = strengths.get("strengths", [])
        if "alto_engajamento" in strengths_list:
            recommendations.append("✅ Continue mantendo alto engajamento - é seu ponto forte")
        
        if "resolução_objeções" in strengths_list:
            recommendations.append("🛡️ Aproveite sua habilidade de resolver objeções")
        
        # Recomendações baseadas no nível
        level = profile.get("level", "junior")
        if level == "junior":
            recommendations.append("🚀 Foque em calls com clientes médios para ganhar experiência")
        elif level == "pleno":
            recommendations.append("💼 Aceite mais clientes difíceis para evoluir para sênior")
        elif level == "senior":
            recommendations.append("🎓 Compartilhe conhecimento com vendedores juniores")
        
        return recommendations[:5]  # Limitar a 5 recomendações 
    
    def on_disc_profile_updated(self, event: Dict[str, Any]):
        """Handler para atualização de perfil DISC."""
        try:
            seller_id = event.get("seller_id")
            scores = event.get("scores", {})
            gaps = event.get("gaps", [])
            plan = event.get("plan", {})
            
            self.logger.info(f"📊 Perfil DISC atualizado para {seller_id}: {gaps}")
            
            # Armazenar contexto DISC para uso em coaching
            if not hasattr(self, 'disc_contexts'):
                self.disc_contexts = {}
            
            self.disc_contexts[seller_id] = {
                'scores': scores,
                'gaps': gaps,
                'plan': plan,
                'updated_at': time.time()
            }
            
            # Publicar evento para UI
            disc_event = {
                'seller_id': seller_id,
                'scores': scores,
                'gaps': gaps,
                'plan': plan
            }
            self.event_bus.publish("mentor.disc.updated", disc_event)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar atualização DISC: {e}")
    
    def on_disc_context(self, event: Dict[str, Any]):
        """Handler para contexto DISC do vendedor."""
        try:
            seller_id = event.get("seller_id")
            disc_context = event.get("disc_context", {})
            quick_tips = event.get("quick_tips", [])
            
            self.logger.info(f"🎯 Contexto DISC carregado para {seller_id}")
            
            # Armazenar contexto para uso em coaching
            if not hasattr(self, 'disc_contexts'):
                self.disc_contexts = {}
            
            self.disc_contexts[seller_id] = {
                **self.disc_contexts.get(seller_id, {}),
                'context': disc_context,
                'quick_tips': quick_tips
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar contexto DISC: {e}")
    
    def get_disc_context_for_seller(self, seller_id: str) -> Dict[str, Any]:
        """Obter contexto DISC do vendedor para coaching."""
        if not hasattr(self, 'disc_contexts'):
            return {}
        
        return self.disc_contexts.get(seller_id, {})
    
    def enhance_coaching_with_disc(self, seller_id: str, base_feedback: List[str]) -> List[str]:
        """Aprimora feedback de coaching com insights DISC."""
        disc_context = self.get_disc_context_for_seller(seller_id)
        
        if not disc_context:
            return base_feedback
        
        enhanced_feedback = base_feedback.copy()
        gaps = disc_context.get('gaps', [])
        quick_tips = disc_context.get('quick_tips', [])
        
        # Adicionar dicas DISC específicas
        if gaps:
            enhanced_feedback.append("")
            enhanced_feedback.append("🎯 **Foco DISC para próxima call:**")
            
            for gap in gaps[:2]:  # Top 2 fraquezas
                if gap == "D_baixa":
                    enhanced_feedback.append("• Seja mais assertivo: use frases diretas e objetivas")
                elif gap == "I_baixa":
                    enhanced_feedback.append("• Faça mais perguntas abertas para explorar necessidades")
                elif gap == "S_baixa":
                    enhanced_feedback.append("• Evite interromper e pratique escuta ativa")
                elif gap == "C_baixa":
                    enhanced_feedback.append("• Estruture sua apresentação em 3 pontos principais")
        
        # Adicionar dicas rápidas
        if quick_tips:
            enhanced_feedback.append("")
            enhanced_feedback.append("💡 **Dicas rápidas:**")
            for tip in quick_tips[:3]:
                enhanced_feedback.append(f"• {tip}")
        
        return enhanced_feedback 
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Obter métricas de performance do Mentor Engine.
        
        Returns:
            Dict com métricas de performance
        """
        return {
            **self.performance_metrics,
            "active_calls": len(self.current_calls),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "memory_usage_mb": self._get_memory_usage(),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calcular taxa de hit do cache."""
        if not hasattr(self, '_cache_stats'):
            return 0.0
        
        stats = self._cache_stats
        total_requests = stats.get('hits', 0) + stats.get('misses', 0)
        return stats.get('hits', 0) / total_requests if total_requests > 0 else 0.0
    
    def _get_memory_usage(self) -> float:
        """Obter uso de memória em MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def reset_performance_metrics(self):
        """Resetar métricas de performance."""
        self.performance_metrics = {
            "calls_processed": 0,
            "tips_generated": 0,
            "feedback_generated": 0,
            "xp_awarded": 0,
            "errors_count": 0,
            "avg_processing_time_ms": 0.0
        }
        self._start_time = time.time()
        self._cache_stats = {"hits": 0, "misses": 0} 
    
    def _log_with_context(self, level: str, message: str, context: Dict[str, Any] = None):
        """Log com contexto estruturado."""
        if context is None:
            context = {}
        
        # Adicionar contexto padrão
        log_context = {
            "component": "mentor_engine",
            "active_calls": len(self.current_calls),
            **context
        }
        
        if level == "debug":
            self.logger.debug(f"{message} | {log_context}")
        elif level == "info":
            self.logger.info(f"{message} | {log_context}")
        elif level == "warning":
            self.logger.warning(f"{message} | {log_context}")
        elif level == "error":
            self.logger.error(f"{message} | {log_context}")
            self.performance_metrics["errors_count"] += 1 
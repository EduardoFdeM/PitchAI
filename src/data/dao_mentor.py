"""
DAO Mentor - Data Access Object para operações de mentoring
========================================================

Gerencia operações de banco relacionadas ao sistema de mentoring.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date


class DAOMentor:
    """DAO para operações de mentoring."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    # === OPERAÇÕES DE VENDEDORES ===
    
    def create_seller(self, seller_id: str, name: str, email: str = None) -> bool:
        """Criar novo vendedor."""
        try:
            query = """
                INSERT INTO sellers (id, name, email)
                VALUES (?, ?, ?)
            """
            self.db.execute_query(query, (seller_id, name, email))
            self.logger.info(f"✅ Vendedor criado: {seller_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar vendedor: {e}")
            return False
    
    def get_seller(self, seller_id: str) -> Optional[Dict[str, Any]]:
        """Obter dados do vendedor."""
        try:
            query = "SELECT * FROM sellers WHERE id = ?"
            result = self.db.execute_query(query, (seller_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter vendedor: {e}")
            return None
    
    def get_seller_xp(self, seller_id: str) -> int:
        """Obter XP do vendedor."""
        try:
            query = "SELECT xp FROM sellers WHERE id = ?"
            result = self.db.execute_query(query, (seller_id,))
            return result[0]['xp'] if result else 0
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter XP: {e}")
            return 0
    
    def _update_seller_xp(self, seller_id: str, xp: int) -> bool:
        """Atualizar XP do vendedor."""
        try:
            query = "UPDATE sellers SET xp = ? WHERE id = ?"
            self.db.execute_query(query, (xp, seller_id))
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar XP: {e}")
            return False
    
    def award_xp(self, seller_id: str, xp_amount: int) -> bool:
        """Adicionar XP ao vendedor."""
        try:
            current_xp = self.get_seller_xp(seller_id)
            new_xp = current_xp + xp_amount
            return self._update_seller_xp(seller_id, new_xp)
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar XP: {e}")
            return False
    
    def update_seller_level(self, seller_id: str, level: str) -> bool:
        """Atualizar nível do vendedor."""
        try:
            query = "UPDATE sellers SET level = ? WHERE id = ?"
            self.db.execute_query(query, (level, seller_id))
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar nível: {e}")
            return False
    
    # === OPERAÇÕES DE CALLS ===
    
    def create_call(self, call_id: str, seller_id: str, **kwargs) -> bool:
        """Criar nova call."""
        try:
            query = """
                INSERT INTO calls (id, seller_id, client_tier, client_stage, 
                                 duration_seconds, sentiment_score, engagement_score, 
                                 objections_count, xp_earned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                call_id, seller_id,
                kwargs.get('client_tier'),
                kwargs.get('client_stage'),
                kwargs.get('duration_seconds', 0),
                kwargs.get('sentiment_score', 0.0),
                kwargs.get('engagement_score', 0.0),
                kwargs.get('objections_count', 0),
                kwargs.get('xp_earned', 0)
            )
            self.db.execute_query(query, params)
            self.logger.info(f"✅ Call criada: {call_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar call: {e}")
            return False
    
    def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Obter dados da call."""
        try:
            query = "SELECT * FROM calls WHERE id = ?"
            result = self.db.execute_query(query, (call_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter call: {e}")
            return None
    
    def update_call_xp(self, call_id: str, xp_earned: int) -> bool:
        """Atualizar XP ganho na call."""
        try:
            query = "UPDATE calls SET xp_earned = ? WHERE id = ?"
            self.db.execute_query(query, (xp_earned, call_id))
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar XP da call: {e}")
            return False
    
    def get_seller_calls(self, seller_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obter calls do vendedor."""
        try:
            query = """
                SELECT * FROM calls 
                WHERE seller_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """
            return self.db.execute_query(query, (seller_id, limit))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter calls do vendedor: {e}")
            return []
    
    # === OPERAÇÕES DE COACHING ===
    
    def save_coaching_feedback(self, call_id: str, seller_id: str, 
                              feedback_type: str, feedback_text: str, 
                              tips: str = None, xp_bonus: int = 0) -> bool:
        """Salvar feedback de coaching."""
        try:
            query = """
                INSERT INTO coaching_feedback 
                (call_id, seller_id, feedback_type, feedback_text, tips, xp_bonus)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(query, (call_id, seller_id, feedback_type, 
                                        feedback_text, tips, xp_bonus))
            self.logger.info(f"✅ Feedback salvo para call: {call_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar feedback: {e}")
            return False
    
    def get_call_feedback(self, call_id: str) -> List[Dict[str, Any]]:
        """Obter feedback de uma call."""
        try:
            query = """
                SELECT * FROM coaching_feedback 
                WHERE call_id = ? 
                ORDER BY created_at DESC
            """
            return self.db.execute_query(query, (call_id,))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter feedback: {e}")
            return []
    
    # === OPERAÇÕES DE ANALYTICS ===
    
    def save_metric(self, seller_id: str, metric_name: str, 
                   metric_value: float, date: date = None) -> bool:
        """Salvar métrica de analytics."""
        try:
            if date is None:
                date = datetime.now().date()
            
            query = """
                INSERT INTO analytics (seller_id, metric_name, metric_value, date)
                VALUES (?, ?, ?, ?)
            """
            self.db.execute_query(query, (seller_id, metric_name, metric_value, date))
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar métrica: {e}")
            return False
    
    def get_seller_metrics(self, seller_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Obter métricas do vendedor."""
        try:
            query = """
                SELECT * FROM analytics 
                WHERE seller_id = ? 
                AND date >= date('now', '-{} days')
                ORDER BY date DESC
            """.format(days)
            return self.db.execute_query(query, (seller_id,))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter métricas: {e}")
            return []
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obter leaderboard de vendedores."""
        try:
            query = """
                SELECT id, name, xp, level 
                FROM sellers 
                ORDER BY xp DESC 
                LIMIT ?
            """
            return self.db.execute_query(query, (limit,))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter leaderboard: {e}")
            return [] 
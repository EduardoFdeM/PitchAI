"""
DAO DISC - Data Access Object para operações DISC
===============================================

Gerencia operações de banco relacionadas ao sistema DISC.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


class DAODisc:
    """DAO para operações DISC."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    # === OPERAÇÕES DE PERFIS DISC ===
    
    def save_disc_profile(self, seller_id: str, call_id: str, 
                         dominance_score: float, influence_score: float,
                         steadiness_score: float, conscientiousness_score: float,
                         primary_style: str, secondary_style: str = None) -> bool:
        """Salvar perfil DISC de uma call."""
        try:
            query = """
                INSERT INTO disc_profiles 
                (seller_id, call_id, dominance_score, influence_score, 
                 steadiness_score, conscientiousness_score, primary_style, secondary_style)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                seller_id, call_id, dominance_score, influence_score,
                steadiness_score, conscientiousness_score, primary_style, secondary_style
            )
            self.db.execute_query(query, params)
            self.logger.info(f"✅ Perfil DISC salvo para call: {call_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar perfil DISC: {e}")
            return False
    
    def get_call_disc_profile(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Obter perfil DISC de uma call específica."""
        try:
            query = "SELECT * FROM disc_profiles WHERE call_id = ?"
            result = self.db.execute_query(query, (call_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter perfil DISC: {e}")
            return None
    
    def get_seller_disc_profiles(self, seller_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obter perfis DISC de um vendedor."""
        try:
            query = """
                SELECT * FROM disc_profiles 
                WHERE seller_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """
            return self.db.execute_query(query, (seller_id, limit))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter perfis DISC do vendedor: {e}")
            return []
    
    def get_seller_average_disc(self, seller_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Obter média dos scores DISC de um vendedor."""
        try:
            query = """
                SELECT 
                    AVG(dominance_score) as avg_dominance,
                    AVG(influence_score) as avg_influence,
                    AVG(steadiness_score) as avg_steadiness,
                    AVG(conscientiousness_score) as avg_conscientiousness,
                    COUNT(*) as total_calls
                FROM disc_profiles 
                WHERE seller_id = ? 
                AND created_at >= date('now', '-{} days')
            """.format(days)
            
            result = self.db.execute_query(query, (seller_id,))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter média DISC: {e}")
            return None
    
    def get_seller_primary_styles(self, seller_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Obter distribuição de estilos primários de um vendedor."""
        try:
            query = """
                SELECT 
                    primary_style,
                    COUNT(*) as frequency,
                    AVG(dominance_score) as avg_dominance,
                    AVG(influence_score) as avg_influence,
                    AVG(steadiness_score) as avg_steadiness,
                    AVG(conscientiousness_score) as avg_conscientiousness
                FROM disc_profiles 
                WHERE seller_id = ? 
                AND created_at >= date('now', '-{} days')
                GROUP BY primary_style
                ORDER BY frequency DESC
            """.format(days)
            
            return self.db.execute_query(query, (seller_id,))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estilos primários: {e}")
            return []
    
    def get_disc_trends(self, seller_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Obter tendências DISC por dia."""
        try:
            query = """
                SELECT 
                    DATE(created_at) as date,
                    AVG(dominance_score) as avg_dominance,
                    AVG(influence_score) as avg_influence,
                    AVG(steadiness_score) as avg_steadiness,
                    AVG(conscientiousness_score) as avg_conscientiousness,
                    COUNT(*) as calls_count
                FROM disc_profiles 
                WHERE seller_id = ? 
                AND created_at >= date('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """.format(days)
            
            return self.db.execute_query(query, (seller_id,))
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter tendências DISC: {e}")
            return []
    
    def get_team_disc_insights(self, days: int = 30) -> Dict[str, Any]:
        """Obter insights DISC da equipe."""
        try:
            # Estatísticas gerais
            general_query = """
                SELECT 
                    COUNT(DISTINCT seller_id) as total_sellers,
                    COUNT(*) as total_calls,
                    AVG(dominance_score) as team_avg_dominance,
                    AVG(influence_score) as team_avg_influence,
                    AVG(steadiness_score) as team_avg_steadiness,
                    AVG(conscientiousness_score) as team_avg_conscientiousness
                FROM disc_profiles 
                WHERE created_at >= date('now', '-{} days')
            """.format(days)
            
            general_result = self.db.execute_query(general_query)
            general_stats = general_result[0] if general_result else {}
            
            # Distribuição de estilos
            styles_query = """
                SELECT 
                    primary_style,
                    COUNT(*) as frequency,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM disc_profiles WHERE created_at >= date('now', '-{} days')), 2) as percentage
                FROM disc_profiles 
                WHERE created_at >= date('now', '-{} days')
                GROUP BY primary_style
                ORDER BY frequency DESC
            """.format(days, days)
            
            styles_result = self.db.execute_query(styles_query)
            
            return {
                'general_stats': general_stats,
                'style_distribution': styles_result
            }
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter insights da equipe: {e}")
            return {}
    
    def delete_disc_profile(self, call_id: str) -> bool:
        """Deletar perfil DISC de uma call."""
        try:
            query = "DELETE FROM disc_profiles WHERE call_id = ?"
            self.db.execute_query(query, (call_id,))
            self.logger.info(f"✅ Perfil DISC deletado para call: {call_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao deletar perfil DISC: {e}")
            return False
    
    def get_disc_leaderboard(self, style: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Obter leaderboard DISC."""
        try:
            if style:
                # Leaderboard por estilo específico
                query = """
                    SELECT 
                        dp.seller_id,
                        s.name,
                        AVG(dp.{}_score) as avg_score,
                        COUNT(*) as calls_count
                    FROM disc_profiles dp
                    JOIN sellers s ON dp.seller_id = s.id
                    WHERE dp.created_at >= date('now', '-{} days')
                    GROUP BY dp.seller_id, s.name
                    ORDER BY avg_score DESC
                    LIMIT 10
                """.format(style.lower(), days)
            else:
                # Leaderboard geral (média de todos os scores)
                query = """
                    SELECT 
                        dp.seller_id,
                        s.name,
                        AVG((dp.dominance_score + dp.influence_score + dp.steadiness_score + dp.conscientiousness_score) / 4.0) as avg_score,
                        COUNT(*) as calls_count
                    FROM disc_profiles dp
                    JOIN sellers s ON dp.seller_id = s.id
                    WHERE dp.created_at >= date('now', '-{} days')
                    GROUP BY dp.seller_id, s.name
                    ORDER BY avg_score DESC
                    LIMIT 10
                """.format(days)
            
            return self.db.execute_query(query)
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter leaderboard DISC: {e}")
            return [] 
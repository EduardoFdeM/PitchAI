"""
PitchAI - Dashboard Service
==========================

Serviço que gerencia todos os dados do dashboard:
- Metas de vendas
- Ranking de vendedores
- Histórico de gravações
- Estatísticas em tempo real
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from data.database import DatabaseManager
from data.dao_mentor import DAOMentor


@dataclass
class SalesGoal:
    """Meta de vendas."""
    id: str
    seller_id: str
    target_units: int
    target_contracts: int
    current_units: int
    current_contracts: int
    period_start: datetime
    period_end: datetime
    created_at: datetime


@dataclass
class SellerRanking:
    """Ranking de vendedor."""
    seller_id: str
    seller_name: str
    total_sales: int
    total_contracts: int
    total_xp: int
    level: int
    position: int
    last_activity: datetime


@dataclass
class CallHistory:
    """Histórico de chamada."""
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    sentiment_avg: Optional[float]
    objection_count: int
    opportunity_count: int
    summary: Optional[str]
    status: str  # 'completed', 'in_progress', 'failed'


class DashboardService:
    """Serviço de dashboard que integra frontend com backend."""
    
    def __init__(self, database: DatabaseManager, dao_mentor: DAOMentor):
        self.database = database
        self.dao_mentor = dao_mentor
        self.logger = logging.getLogger(__name__)
        self._create_dashboard_tables()
    
    def _create_dashboard_tables(self):
        """Criar tabelas específicas do dashboard."""
        
        # Tabela de metas de vendas
        self.database.connection.execute("""
            CREATE TABLE IF NOT EXISTS sales_goals (
                id TEXT PRIMARY KEY,
                seller_id TEXT NOT NULL,
                target_units INTEGER NOT NULL,
                target_contracts INTEGER NOT NULL,
                current_units INTEGER DEFAULT 0,
                current_contracts INTEGER DEFAULT 0,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES seller_xp (seller_id)
            )
        """)
        
        # Tabela de vendas concluídas
        self.database.connection.execute("""
            CREATE TABLE IF NOT EXISTS completed_sales (
                id TEXT PRIMARY KEY,
                seller_id TEXT NOT NULL,
                call_id TEXT NOT NULL,
                units_sold INTEGER DEFAULT 1,
                contract_value REAL,
                sale_date TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES seller_xp (seller_id),
                FOREIGN KEY (call_id) REFERENCES call (id)
            )
        """)
        
        # Tabela de configurações do dashboard
        self.database.connection.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.database.connection.commit()
        self.logger.info("✅ Tabelas do dashboard criadas")
    
    def get_dashboard_data(self, seller_id: str = "giovanna") -> Dict[str, Any]:
        """Obter todos os dados do dashboard para um vendedor."""
        try:
            # Dados do vendedor
            seller_xp = self.dao_mentor.get_seller_xp(seller_id)
            
            # Metas atuais
            current_goals = self._get_current_goals(seller_id)
            
            # Ranking
            ranking = self._get_seller_ranking(seller_id)
            
            # Histórico recente
            recent_calls = self._get_recent_calls(seller_id, limit=5)
            
            # Estatísticas gerais
            stats = self._get_seller_stats(seller_id)
            
            return {
                "seller": {
                    "id": seller_id,
                    "name": "Giovanna",
                    "level": seller_xp['level'],
                    "total_xp": seller_xp['total_xp']
                },
                "goals": current_goals,
                "ranking": ranking,
                "recent_calls": recent_calls,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter dados do dashboard: {e}")
            return self._get_default_dashboard_data(seller_id)
    
    def _get_current_goals(self, seller_id: str) -> Dict[str, Any]:
        """Obter metas atuais do vendedor."""
        # Buscar meta do mês atual
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        cursor = self.database.connection.execute("""
            SELECT * FROM sales_goals 
            WHERE seller_id = ? AND period_start <= ? AND period_end >= ?
        """, (seller_id, now, now))
        
        goal_data = cursor.fetchone()
        
        if goal_data:
            # Meta existente
            units_percent = (goal_data['current_units'] / goal_data['target_units']) * 100 if goal_data['target_units'] > 0 else 0
            contracts_percent = (goal_data['current_contracts'] / goal_data['target_contracts']) * 100 if goal_data['target_contracts'] > 0 else 0
            
            return {
                "units": {
                    "target": goal_data['target_units'],
                    "current": goal_data['current_units'],
                    "percent": min(units_percent, 100)
                },
                "contracts": {
                    "target": goal_data['target_contracts'],
                    "current": goal_data['current_contracts'],
                    "percent": min(contracts_percent, 100)
                }
            }
        else:
            # Criar meta padrão se não existir
            default_goal = self._create_default_goal(seller_id, month_start, month_end)
            return {
                "units": {
                    "target": default_goal.target_units,
                    "current": default_goal.current_units,
                    "percent": 0
                },
                "contracts": {
                    "target": default_goal.target_contracts,
                    "current": default_goal.current_contracts,
                    "percent": 0
                }
            }
    
    def _create_default_goal(self, seller_id: str, start: datetime, end: datetime) -> SalesGoal:
        """Criar meta padrão para o vendedor."""
        goal_id = f"goal_{seller_id}_{start.strftime('%Y%m')}"
        
        # Metas padrão baseadas no nível do vendedor
        seller_xp = self.dao_mentor.get_seller_xp(seller_id)
        level = seller_xp['level']
        
        if level >= 10:  # Sênior
            target_units = 50
            target_contracts = 15
        elif level >= 5:  # Pleno
            target_units = 30
            target_contracts = 10
        else:  # Júnior
            target_units = 20
            target_contracts = 5
        
        goal = SalesGoal(
            id=goal_id,
            seller_id=seller_id,
            target_units=target_units,
            target_contracts=target_contracts,
            current_units=0,
            current_contracts=0,
            period_start=start,
            period_end=end,
            created_at=datetime.now()
        )
        
        self.database.connection.execute("""
            INSERT INTO sales_goals 
            (id, seller_id, target_units, target_contracts, current_units, current_contracts, 
             period_start, period_end, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (goal.id, goal.seller_id, goal.target_units, goal.target_contracts,
              goal.current_units, goal.current_contracts, goal.period_start, 
              goal.period_end, goal.created_at))
        
        self.database.connection.commit()
        self.logger.info(f"📊 Meta padrão criada para {seller_id}: {target_units} unidades, {target_contracts} contratos")
        
        return goal
    
    def _get_seller_ranking(self, seller_id: str) -> Dict[str, Any]:
        """Obter ranking do vendedor."""
        # Buscar todos os vendedores ordenados por vendas
        cursor = self.database.connection.execute("""
            SELECT 
                sx.seller_id,
                sx.total_xp,
                sx.level,
                COALESCE(SUM(cs.units_sold), 0) as total_sales,
                COALESCE(COUNT(cs.id), 0) as total_contracts,
                MAX(cs.sale_date) as last_activity
            FROM seller_xp sx
            LEFT JOIN completed_sales cs ON sx.seller_id = cs.seller_id
            GROUP BY sx.seller_id
            ORDER BY total_sales DESC, total_xp DESC
        """)
        
        rankings = []
        position = 1
        
        for row in cursor.fetchall():
            seller_name = self._get_seller_name(row['seller_id'])
            
            ranking = SellerRanking(
                seller_id=row['seller_id'],
                seller_name=seller_name,
                total_sales=row['total_sales'],
                total_contracts=row['total_contracts'],
                total_xp=row['total_xp'],
                level=row['level'],
                position=position,
                last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else datetime.now()
            )
            
            rankings.append(ranking)
            position += 1
        
        # Encontrar posição do vendedor atual
        current_ranking = next((r for r in rankings if r.seller_id == seller_id), None)
        
        return {
            "current_position": current_ranking.position if current_ranking else 1,
            "total_sellers": len(rankings),
            "top_sellers": rankings[:5]  # Top 5
        }
    
    def _get_seller_name(self, seller_id: str) -> str:
        """Obter nome do vendedor."""
        # Mapeamento simples - em produção seria uma tabela de usuários
        names = {
            "giovanna": "Giovanna",
            "joao": "João Silva",
            "maria": "Maria Santos",
            "pedro": "Pedro Costa"
        }
        return names.get(seller_id, seller_id.title())
    
    def _get_recent_calls(self, seller_id: str, limit: int = 5) -> List[CallHistory]:
        """Obter chamadas recentes do vendedor."""
        cursor = self.database.connection.execute("""
            SELECT * FROM call 
            WHERE channel = ? 
            ORDER BY start_time DESC 
            LIMIT ?
        """, (seller_id, limit))
        
        calls = []
        for row in cursor.fetchall():
            call = CallHistory(
                id=row['id'],
                start_time=datetime.fromisoformat(row['start_time']),
                end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                duration_seconds=row['duration_seconds'],
                sentiment_avg=row['sentiment_avg'],
                objection_count=row['objection_count'],
                opportunity_count=row['opportunity_count'],
                summary=row['summary'],
                status='completed' if row['end_time'] else 'in_progress'
            )
            calls.append(call)
        
        return calls
    
    def _get_seller_stats(self, seller_id: str) -> Dict[str, Any]:
        """Obter estatísticas do vendedor."""
        # Estatísticas do mês atual
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cursor = self.database.connection.execute("""
            SELECT 
                COUNT(*) as total_calls,
                AVG(duration_seconds) as avg_duration,
                AVG(sentiment_avg) as avg_sentiment,
                SUM(objection_count) as total_objections,
                SUM(opportunity_count) as total_opportunities
            FROM call 
            WHERE channel = ? AND start_time >= ?
        """, (seller_id, month_start))
        
        stats_row = cursor.fetchone()
        
        # Vendas do mês
        cursor = self.database.connection.execute("""
            SELECT 
                SUM(units_sold) as monthly_units,
                COUNT(*) as monthly_contracts,
                SUM(contract_value) as monthly_revenue
            FROM completed_sales 
            WHERE seller_id = ? AND sale_date >= ?
        """, (seller_id, month_start))
        
        sales_row = cursor.fetchone()
        
        return {
            "monthly_calls": stats_row['total_calls'] if stats_row else 0,
            "avg_duration": stats_row['avg_duration'] if stats_row and stats_row['avg_duration'] else 0,
            "avg_sentiment": stats_row['avg_sentiment'] if stats_row and stats_row['avg_sentiment'] else 0.5,
            "total_objections": stats_row['total_objections'] if stats_row else 0,
            "total_opportunities": stats_row['total_opportunities'] if stats_row else 0,
            "monthly_units": sales_row['monthly_units'] if sales_row else 0,
            "monthly_contracts": sales_row['monthly_contracts'] if sales_row else 0,
            "monthly_revenue": sales_row['monthly_revenue'] if sales_row else 0.0
        }
    
    def _get_default_dashboard_data(self, seller_id: str) -> Dict[str, Any]:
        """Dados padrão do dashboard em caso de erro."""
        return {
            "seller": {
                "id": seller_id,
                "name": "Giovanna",
                "level": 1,
                "total_xp": 0
            },
            "goals": {
                "units": {"target": 20, "current": 0, "percent": 0},
                "contracts": {"target": 5, "current": 0, "percent": 0}
            },
            "ranking": {
                "current_position": 1,
                "total_sellers": 1,
                "top_sellers": []
            },
            "recent_calls": [],
            "stats": {
                "monthly_calls": 0,
                "avg_duration": 0,
                "avg_sentiment": 0.5,
                "total_objections": 0,
                "total_opportunities": 0,
                "monthly_units": 0,
                "monthly_contracts": 0,
                "monthly_revenue": 0.0
            }
        }
    
    def record_sale(self, seller_id: str, call_id: str, units: int = 1, 
                   contract_value: Optional[float] = None) -> bool:
        """Registrar uma venda concluída."""
        try:
            sale_id = f"sale_{call_id}_{datetime.now().timestamp()}"
            
            self.database.connection.execute("""
                INSERT INTO completed_sales 
                (id, seller_id, call_id, units_sold, contract_value, sale_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, seller_id, call_id, units, contract_value, datetime.now()))
            
            # Atualizar metas
            self._update_goals(seller_id, units, 1)
            
            self.database.connection.commit()
            self.logger.info(f"💰 Venda registrada: {seller_id} - {units} unidades")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao registrar venda: {e}")
            return False
    
    def _update_goals(self, seller_id: str, units: int, contracts: int):
        """Atualizar metas do vendedor."""
        now = datetime.now()
        
        self.database.connection.execute("""
            UPDATE sales_goals 
            SET current_units = current_units + ?, current_contracts = current_contracts + ?
            WHERE seller_id = ? AND period_start <= ? AND period_end >= ?
        """, (units, contracts, seller_id, now, now))
    
    def get_call_history(self, seller_id: str, limit: int = 20) -> List[CallHistory]:
        """Obter histórico completo de chamadas."""
        cursor = self.database.connection.execute("""
            SELECT * FROM call 
            WHERE channel = ? 
            ORDER BY start_time DESC 
            LIMIT ?
        """, (seller_id, limit))
        
        calls = []
        for row in cursor.fetchall():
            call = CallHistory(
                id=row['id'],
                start_time=datetime.fromisoformat(row['start_time']),
                end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                duration_seconds=row['duration_seconds'],
                sentiment_avg=row['sentiment_avg'],
                objection_count=row['objection_count'],
                opportunity_count=row['opportunity_count'],
                summary=row['summary'],
                status='completed' if row['end_time'] else 'in_progress'
            )
            calls.append(call)
        
        return calls

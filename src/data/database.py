"""
Database Manager - Gerenciador do banco SQLite
============================================

Gerencia conexões, migrações e operações básicas do banco.
"""

import sqlite3
import logging
import os
from typing import Optional, List, Dict, Any
from pathlib import Path


class DatabaseManager:
    """Gerenciador do banco de dados SQLite."""
    
    def __init__(self, db_path: str = "data/pitchai.db"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger(__name__)
        
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Estabelecer conexão com o banco."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Para acesso por nome
            self.logger.info(f"✅ Conectado ao banco: {self.db_path}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar ao banco: {e}")
            raise
    
    def _create_tables(self):
        """Criar tabelas se não existirem."""
        try:
            cursor = self.connection.cursor()
            
            # Aplicar migrações
            self._apply_migrations()
            
            # Tabela de vendedores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sellers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    xp INTEGER DEFAULT 0,
                    level TEXT DEFAULT 'junior',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de calls
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY,
                    seller_id TEXT NOT NULL,
                    client_tier TEXT,
                    client_stage TEXT,
                    duration_seconds INTEGER,
                    sentiment_score REAL,
                    engagement_score REAL,
                    objections_count INTEGER DEFAULT 0,
                    xp_earned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES sellers (id)
                )
            """)
            
            # Tabela de perfis DISC
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disc_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_id TEXT NOT NULL,
                    call_id TEXT NOT NULL,
                    dominance_score REAL,
                    influence_score REAL,
                    steadiness_score REAL,
                    conscientiousness_score REAL,
                    primary_style TEXT,
                    secondary_style TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES sellers (id),
                    FOREIGN KEY (call_id) REFERENCES calls (id)
                )
            """)
            
            # Tabela de coaching feedback
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coaching_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT NOT NULL,
                    seller_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    feedback_text TEXT NOT NULL,
                    tips TEXT,
                    xp_bonus INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (call_id) REFERENCES calls (id),
                    FOREIGN KEY (seller_id) REFERENCES sellers (id)
                )
            """)
            
            # Tabela de analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES sellers (id)
                )
            """)
            
            self.connection.commit()
            self.logger.info("✅ Tabelas criadas/verificadas com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def _apply_migrations(self):
        """Aplicar migrações do banco de dados."""
        try:
            # Verificar se a tabela de migrações existe
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Lista de migrações
            migrations = [
                "0006_real_data_tables.sql"
            ]
            
            for migration in migrations:
                # Verificar se já foi aplicada
                cursor.execute("SELECT COUNT(*) FROM migrations WHERE migration_name = ?", (migration,))
                if cursor.fetchone()[0] == 0:
                    # Aplicar migração
                    migration_path = Path(__file__).parent / "migrations" / migration
                    if migration_path.exists():
                        with open(migration_path, 'r') as f:
                            sql = f.read()
                        
                        # Executar SQL da migração
                        cursor.executescript(sql)
                        
                        # Registrar migração aplicada
                        cursor.execute("INSERT INTO migrations (migration_name) VALUES (?)", (migration,))
                        
                        self.logger.info(f"✅ Migração aplicada: {migration}")
                    else:
                        self.logger.warning(f"⚠️ Arquivo de migração não encontrado: {migration}")
            
            self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao aplicar migrações: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executar query e retornar resultados como lista de dicionários."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                return [dict(row) for row in cursor.fetchall()]
            else:
                self.connection.commit()
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Erro na query: {e}")
            self.connection.rollback()
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Executar múltiplas queries."""
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
        except Exception as e:
            self.logger.error(f"❌ Erro em executemany: {e}")
            self.connection.rollback()
            raise
    
    def close(self):
        """Fechar conexão com o banco."""
        if self.connection:
            self.connection.close()
            self.logger.info("✅ Conexão com banco fechada")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
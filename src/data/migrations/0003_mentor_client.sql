-- Migração 0003: Mentor e Client System
-- Data: 2024-08-31
-- Descrição: Criação das tabelas para sistema de mentoring e perfis de clientes

-- Tabela de vendedores
CREATE TABLE IF NOT EXISTS sellers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    xp INTEGER DEFAULT 0,
    level TEXT DEFAULT 'junior',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de calls
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
);

-- Tabela de coaching feedback
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
);

-- Tabela de analytics
CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers (id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_calls_seller_id ON calls(seller_id);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_coaching_call_id ON coaching_feedback(call_id);
CREATE INDEX IF NOT EXISTS idx_analytics_seller_date ON analytics(seller_id, date); 
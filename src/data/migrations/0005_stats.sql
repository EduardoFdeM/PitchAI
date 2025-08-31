-- Migração 0005: Estatísticas e Analytics
-- Data: 2024-08-31
-- Descrição: Criação de tabelas e índices para analytics avançados

-- Tabela de métricas detalhadas
CREATE TABLE IF NOT EXISTS detailed_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id TEXT NOT NULL,
    call_id TEXT NOT NULL,
    metric_category TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers (id),
    FOREIGN KEY (call_id) REFERENCES calls (id)
);

-- Tabela de tendências diárias
CREATE TABLE IF NOT EXISTS daily_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id TEXT NOT NULL,
    date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    avg_duration REAL DEFAULT 0,
    avg_sentiment REAL DEFAULT 0,
    avg_engagement REAL DEFAULT 0,
    total_xp_earned INTEGER DEFAULT 0,
    objections_resolved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers (id)
);

-- Tabela de achievements
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id TEXT NOT NULL,
    achievement_type TEXT NOT NULL,
    achievement_name TEXT NOT NULL,
    achievement_description TEXT,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers (id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_detailed_metrics_seller ON detailed_metrics(seller_id);
CREATE INDEX IF NOT EXISTS idx_detailed_metrics_call ON detailed_metrics(call_id);
CREATE INDEX IF NOT EXISTS idx_detailed_metrics_category ON detailed_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_daily_trends_seller_date ON daily_trends(seller_id, date);
CREATE INDEX IF NOT EXISTS idx_achievements_seller ON achievements(seller_id);
CREATE INDEX IF NOT EXISTS idx_achievements_type ON achievements(achievement_type);

-- View para resumo de performance
CREATE VIEW IF NOT EXISTS seller_performance_summary AS
SELECT 
    s.id as seller_id,
    s.name as seller_name,
    s.xp as total_xp,
    s.level as current_level,
    COUNT(c.id) as total_calls,
    AVG(c.duration_seconds) as avg_call_duration,
    AVG(c.sentiment_score) as avg_sentiment,
    AVG(c.engagement_score) as avg_engagement,
    SUM(c.xp_earned) as total_xp_earned,
    MAX(c.created_at) as last_call_date
FROM sellers s
LEFT JOIN calls c ON s.id = c.seller_id
GROUP BY s.id, s.name, s.xp, s.level; 
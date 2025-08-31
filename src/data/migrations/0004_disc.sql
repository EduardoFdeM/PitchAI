-- Migração 0004: Sistema DISC
-- Data: 2024-08-31
-- Descrição: Criação das tabelas para sistema DISC

-- Tabela de perfis DISC
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
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_disc_seller_id ON disc_profiles(seller_id);
CREATE INDEX IF NOT EXISTS idx_disc_call_id ON disc_profiles(call_id);
CREATE INDEX IF NOT EXISTS idx_disc_created_at ON disc_profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_disc_primary_style ON disc_profiles(primary_style); 
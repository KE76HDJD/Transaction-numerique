-- ============================================
-- V4 — Table pour les transactions Kafka
-- ============================================

CREATE TABLE IF NOT EXISTS transactions_streamed (
    id SERIAL PRIMARY KEY,
    
    -- Donnees de la transaction
    step INTEGER,
    type VARCHAR(20) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    
    -- Emetteur
    name_orig VARCHAR(20) NOT NULL,
    old_balance_org NUMERIC(15, 2),
    new_balance_orig NUMERIC(15, 2),
    
    -- Destinataire
    name_dest VARCHAR(20) NOT NULL,
    old_balance_dest NUMERIC(15, 2),
    new_balance_dest NUMERIC(15, 2),
    
    -- Fraude
    is_fraud INTEGER DEFAULT 0,
    is_flagged_fraud INTEGER DEFAULT 0,
    
    -- Metadonnees Kafka
    kafka_offset BIGINT,
    kafka_partition INTEGER,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les requetes frequentes
CREATE INDEX IF NOT EXISTS idx_streamed_type ON transactions_streamed(type);
CREATE INDEX IF NOT EXISTS idx_streamed_fraud ON transactions_streamed(is_fraud);
CREATE INDEX IF NOT EXISTS idx_streamed_received ON transactions_streamed(received_at);
CREATE INDEX IF NOT EXISTS idx_streamed_offset ON transactions_streamed(kafka_offset);

-- Commentaires
COMMENT ON TABLE transactions_streamed IS 'Transactions recues via Kafka (streaming temps reel)';
COMMENT ON COLUMN transactions_streamed.kafka_offset IS 'Offset du message Kafka';
COMMENT ON COLUMN transactions_streamed.kafka_partition IS 'Partition Kafka du message';
COMMENT ON COLUMN transactions_streamed.received_at IS 'Timestamp de reception par le consumer';

-- ============================================
-- Transaction Data Platform - Create Tables
-- ============================================
-- Ce script cree la structure de la base de donnees
-- pour stocker les transactions traitees.
--
-- Usage :
--   psql -U kevin -d transaction_db -f sql/create_tables.sql
--   ou
--   psql -U kevin -d transaction_db < sql/create_tables.sql

-- Supprimer la table si elle existe (pour recreer proprement)
DROP TABLE IF EXISTS transactions;

-- ============================================
-- Table principale : transactions
-- ============================================
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    
    -- Temporel
    transaction_date TIMESTAMP NOT NULL,
    transaction_date_only DATE NOT NULL,
    transaction_hour INTEGER NOT NULL,
    step INTEGER NOT NULL,
    
    -- Transaction
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
    is_fraud INTEGER NOT NULL DEFAULT 0,
    is_flagged_fraud INTEGER NOT NULL DEFAULT 0,
    
    -- Metadonnees
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Index pour les requetes frequentes
-- ============================================

-- Index sur la date (pour les requetes temporelles)
CREATE INDEX idx_transactions_date ON transactions(transaction_date_only);

-- Index sur le type de transaction
CREATE INDEX idx_transactions_type ON transactions(type);

-- Index sur la fraude (pour filtrer les fraudes)
CREATE INDEX idx_transactions_fraud ON transactions(is_fraud);

-- Index sur l'emetteur
CREATE INDEX idx_transactions_orig ON transactions(name_orig);

-- Index sur le destinataire
CREATE INDEX idx_transactions_dest ON transactions(name_dest);

-- ============================================
-- Commentaires pour la documentation
-- ============================================
COMMENT ON TABLE transactions IS 'Table principale des transactions numeriques';
COMMENT ON COLUMN transactions.step IS 'Unite de temps (1 step = 1 heure)';
COMMENT ON COLUMN transactions.type IS 'Type de transaction: PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT';
COMMENT ON COLUMN transactions.amount IS 'Montant de la transaction en devise';
COMMENT ON COLUMN transactions.is_fraud IS '1 si transaction frauduleuse, 0 sinon';
COMMENT ON COLUMN transactions.is_flagged_fraud IS '1 si transaction suspecte, 0 sinon';

-- ============================================
-- Verification
-- ============================================
SELECT 'Table transactions creee avec succes!' AS message;
SELECT COUNT(*) AS colonnes FROM information_schema.columns 
WHERE table_name = 'transactions';

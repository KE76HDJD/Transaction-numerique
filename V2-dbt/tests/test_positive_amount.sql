-- ============================================
-- test_positive_amount.sql
-- Test custom: tous les montants doivent etre positifs
-- ============================================

select *
from {{ ref('stg_transactions') }}
where amount < 0

-- ============================================
-- stg_transactions.sql
-- Staging: Nettoyage et normalisation des donnees brutes
-- ============================================

with source as (
    select * from {{ source('raw', 'transactions') }}
),

renamed as (
    select
        id,
        transaction_date,
        transaction_date_only,
        transaction_hour,
        step,
        type,
        amount,
        name_orig as sender_id,
        old_balance_org as sender_balance_before,
        new_balance_orig as sender_balance_after,
        name_dest as receiver_id,
        old_balance_dest as receiver_balance_before,
        new_balance_dest as receiver_balance_after,
        is_fraud,
        is_flagged_fraud,
        created_at
    from source
    where amount > 0
      and type in ('PAYMENT', 'TRANSFER', 'CASH_OUT', 'CASH_IN', 'DEBIT')
)

select * from renamed

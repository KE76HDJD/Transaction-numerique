-- ============================================
-- mart_transactions.sql
-- Mart: Table business-ready pour l'analyse
-- ============================================

with daily_agg as (
    select * from {{ ref('int_daily_agg') }}
),

final as (
    select
        transaction_date,
        total_transactions,
        unique_senders,
        unique_receivers,
        total_amount,
        round(avg_amount, 2) as avg_amount,
        min_amount,
        max_amount,
        payment_count,
        transfer_count,
        cash_out_count,
        cash_in_count,
        debit_count,
        fraud_count,
        flagged_fraud_count,
        fraud_rate_pct,
        round(total_amount / nullif(total_transactions, 0), 2) as avg_amount_per_txn,
        round(total_amount / nullif(unique_senders, 0), 2) as amount_per_sender
    from daily_agg
)

select * from final
order by transaction_date

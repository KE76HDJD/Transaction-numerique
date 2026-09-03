-- ============================================
-- int_daily_agg.sql
-- Intermediate: Agregation quotidienne des transactions
-- ============================================

with stg as (
    select * from {{ ref('stg_transactions') }}
),

daily_stats as (
    select
        transaction_date_only as transaction_date,
        count(*) as total_transactions,
        count(distinct sender_id) as unique_senders,
        count(distinct receiver_id) as unique_receivers,
        sum(amount) as total_amount,
        avg(amount) as avg_amount,
        min(amount) as min_amount,
        max(amount) as max_amount,
        sum(case when is_fraud = 1 then 1 else 0 end) as fraud_count,
        sum(case when is_flagged_fraud = 1 then 1 else 0 end) as flagged_fraud_count,
        round(
            sum(case when is_fraud = 1 then 1 else 0 end)::decimal 
            / nullif(count(*), 0) * 100, 
            4
        ) as fraud_rate_pct
    from stg
    group by transaction_date_only
),

by_type as (
    select
        transaction_date_only as transaction_date,
        type,
        count(*) as type_count,
        sum(amount) as type_total_amount,
        avg(amount) as type_avg_amount
    from stg
    group by transaction_date_only, type
),

daily_with_types as (
    select
        d.*,
        max(case when t.type = 'PAYMENT' then t.type_count else 0 end) as payment_count,
        max(case when t.type = 'TRANSFER' then t.type_count else 0 end) as transfer_count,
        max(case when t.type = 'CASH_OUT' then t.type_count else 0 end) as cash_out_count,
        max(case when t.type = 'CASH_IN' then t.type_count else 0 end) as cash_in_count,
        max(case when t.type = 'DEBIT' then t.type_count else 0 end) as debit_count
    from daily_stats d
    left join by_type t on d.transaction_date = t.transaction_date
    group by 
        d.transaction_date,
        d.total_transactions,
        d.unique_senders,
        d.unique_receivers,
        d.total_amount,
        d.avg_amount,
        d.min_amount,
        d.max_amount,
        d.fraud_count,
        d.flagged_fraud_count,
        d.fraud_rate_pct
)

select * from daily_with_types

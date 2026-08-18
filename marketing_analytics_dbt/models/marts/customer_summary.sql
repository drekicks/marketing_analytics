with customers as (

    select *
    from {{ ref('stg_customer') }}

),

rentals as (

    select
        customer_id,
        count(*) as total_rentals,
        min(rental_date) as first_rental_date,
        max(rental_date) as last_rental_date
    from {{ ref('stg_rental') }}
    group by customer_id

),

payments as (

    select
        customer_id,
        sum(amount) as total_payments,
        avg(amount) as avg_payment_amount
    from {{ ref('stg_payment') }}
    group by customer_id

)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.is_active,
    coalesce(r.total_rentals, 0) as total_rentals,
    r.first_rental_date,
    r.last_rental_date,
    coalesce(p.total_payments, 0) as total_payments,
    coalesce(p.avg_payment_amount, 0) as avg_payment_amount
from customers c
left join rentals r
    on c.customer_id = r.customer_id
left join payments p
    on c.customer_id = p.customer_id
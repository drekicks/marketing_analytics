--high value active was heavily skewed to lapse for older data. 55% was lapsed..code below changes that to 7%.

create table high_value as 
(
WITH
-- ---------------------------------------------------------------------
-- 0) Snapshot date: "today" for this dataset = the most recent rental.
--    Sakila's sample data is historical, so days-since-last-rental must
--    be measured against the last activity in the table, not CURRENT_DATE.
-- ---------------------------------------------------------------------
snapshot AS (
    SELECT MAX(rental_date) AS snapshot_date
    FROM rental
),
-- ---------------------------------------------------------------------
-- 1) Base customer metrics
--    Reconstructs the fields from your customer_extract query. Adjust
--    table/column names here if your schema differs (e.g. store_id
--    filters, active-customer filters, etc.)
-- ---------------------------------------------------------------------
customer_rentals AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c3.country,
        MIN(r.rental_date)                 AS first_rental,
        MAX(r.rental_date)                 AS last_rental,
        COUNT(DISTINCT r.rental_id)        AS total_rentals,
        COUNT(DISTINCT f.film_id)          AS unique_films
    FROM rental r
    JOIN customer c   ON c.customer_id = r.customer_id
    JOIN inventory i  ON i.inventory_id = r.inventory_id
    JOIN film f       ON f.film_id = i.film_id
    join address a 	on a.address_id = c.address_id
    join city c2  on c2.city_id = a.city_id 
    join country c3 on c3.country_id = c2.country_id 
    GROUP BY c.customer_id, c.first_name, c.last_name,c3.country 
),
customer_payments AS (
    SELECT
        p.customer_id,
        SUM(p.amount)   AS total_payments,
        AVG(p.amount)   AS avg_payment_amount
    FROM payment p
    GROUP BY p.customer_id
),
-- Favorite MPAA rating and film category = the one each customer rented most,
-- ties broken alphabetically for determinism.
customer_fav_rating AS (
    SELECT customer_id, mpaa_rating AS fav_mpaa_rating
    FROM (
        SELECT
            c.customer_id,
            f.rating AS mpaa_rating,
            COUNT(*) AS n,
            ROW_NUMBER() OVER (
                PARTITION BY c.customer_id
                ORDER BY COUNT(*) DESC, f.rating ASC
            ) AS rn
        FROM rental r
        JOIN customer c  ON c.customer_id = r.customer_id
        JOIN inventory i ON i.inventory_id = r.inventory_id
        JOIN film f      ON f.film_id = i.film_id
        GROUP BY c.customer_id, f.rating
    ) ranked
    WHERE rn = 1
),
customer_fav_category AS (
    SELECT customer_id, category_name AS fav_film_ctgry
    FROM (
        SELECT
            c.customer_id,
            cat.name AS category_name,
            COUNT(*) AS n,
            ROW_NUMBER() OVER (
                PARTITION BY c.customer_id
                ORDER BY COUNT(*) DESC, cat.name ASC
            ) AS rn
        FROM rental r
        JOIN customer c        ON c.customer_id = r.customer_id
        JOIN inventory i       ON i.inventory_id = r.inventory_id
        JOIN film f            ON f.film_id = i.film_id
        JOIN film_category fc  ON fc.film_id = f.film_id
        JOIN category cat      ON cat.category_id = fc.category_id
        GROUP BY c.customer_id, cat.name
    ) ranked
    WHERE rn = 1
),
customer_base AS (
    SELECT
        cr.customer_id,
        cr.customer_name,
        cr.country,
        cr.total_rentals,
        fr.fav_mpaa_rating,
        fc.fav_film_ctgry,
        cr.unique_films,
        (s.snapshot_date::date - cr.first_rental::date)   AS customer_tenure_days,
        (s.snapshot_date::date - cr.last_rental::date)     AS days_since_last_rental,
        COALESCE(cp.total_payments, 0)                     AS total_payments,
        round(COALESCE(cp.total_payments, 0) / NULLIF(cr.total_rentals, 0),2) AS rev_per_rentals,
        round(COALESCE(cp.avg_payment_amount, 0),2)                  AS avg_payment_amount
    FROM customer_rentals cr
    CROSS JOIN snapshot s
    LEFT JOIN customer_payments cp   ON cp.customer_id = cr.customer_id
    LEFT JOIN customer_fav_rating fr ON fr.customer_id = cr.customer_id
    LEFT JOIN customer_fav_category fc ON fc.customer_id = cr.customer_id
),
-- Value tier: decile 1 = High, 2-5 = Medium, 6-10 = Low (matches existing definition)
customer_tiered AS (
    SELECT
        *,
        NTILE(10) OVER (ORDER BY total_payments DESC) AS payment_decile
    FROM customer_base
),
customer_tier_final AS (
    SELECT
        *,
        CASE
            WHEN payment_decile = 1 THEN 'High Value'
            WHEN payment_decile BETWEEN 2 AND 5 THEN 'Medium Value'
            ELSE 'Low Value'
        END AS customer_tier
    FROM customer_tiered
),-- select payment_decile, avg(total_payments), avg(avg_payment_amount), sum(total_payments), sum(unique_films), sum(total_rentals) from customer_tier_final group by 1;,
-- ---------------------------------------------------------------------
-- 2) Recency + engagement rate segmentation
-- ---------------------------------------------------------------------
customer_metrics AS (
    SELECT
        *,
        CASE WHEN days_since_last_rental <= 60 THEN 'Active' when days_since_last_rental between 61 and 175 then 'Pre-Lapsed' ELSE 'Lapsed' END AS recency_segment,
        round(unique_films / (customer_tenure_days / 30.0),2) AS films_per_month
    FROM customer_tier_final
) select cm.customer_tier, recency_segment, cm.customer_id,last_rental 
from customer_metrics cm join customer_rentals cr on cm.customer_id = cr.customer_id 
where customer_tier='High Value'
--group by 1,2
order by 2);

--you have to update  TIMESTAMP '2026-04-17' + (random() * (TIMESTAMP '2026-05-01' - TIMESTAMP '2026-04-17') to get proper range for recency.
with tt as 
(select recency_segment, hv.customer_id, rental_id, r.return_date, last_rental, dense_rank() over (order by hv.customer_id) row_num 
from public.high_value hv join rental r 
on hv.customer_id = r.customer_id 
and hv.last_rental = rental_date
where hv.customer_id<600
)
UPDATE high_value hv
SET last_rental = TIMESTAMP '2026-04-17' + (random() * (TIMESTAMP '2026-05-01' - TIMESTAMP '2026-04-17'))
from tt
WHERE hv.customer_id=tt.customer_id and tt.row_num <195;

WITH
snapshot AS (
    SELECT MAX(rental_date) AS snapshot_date
    FROM rental
),
tt2 as 
(
select *,
(s.snapshot_date::date - hv.last_rental::date) AS days_since_last_rental
from high_value hv
CROSS JOIN snapshot s
where customer_id<600
),
tt3 as (select *, CASE WHEN days_since_last_rental <= 60 THEN 'Active' when days_since_last_rental between 61 and 175 then 'Pre-Lapsed' ELSE 'Lapsed' END AS recency_segment_new
from tt2)
select recency_segment_new, count(*) from tt3 group by 1;

--base table used to update rental and payment table
create table temp_table_dt_fx as 
(
with ttr as (select hv.*, r.rental_id, b.last_rental orig_lr, r.return_date, return_date-b.last_rental dtr, p.payment_date-b.last_rental dtp, p.payment_date, payment_id
from high_value hv join high_value_2 b 
	on hv.customer_id = b.customer_id
join rental r 
on hv.customer_id = r.customer_id 
and b.last_rental = rental_date
join payment p
on hv.customer_id = p.customer_id
and r.rental_id = p.rental_id
where hv.customer_id<600)
select customer_id, rental_id, payment_id, last_rental as new_rental_date,  orig_lr, last_rental+dtr new_rental_return, payment_date, last_rental+dtp new_payment_date
from ttr
order by customer_id
);

create table rental_bkup as (select * from rental);
create table payment_bkup as (select * from payment);

select r.rental_id, r.customer_id, rental_date, new_rental_date, r.return_date, new_rental_return  
from rental r join temp_table_dt_fx tf 
	on r.customer_id = tf.customer_id
	and r.rental_id = tf.rental_id;
	
update rental r
set rental_date = new_rental_date, return_date = new_rental_return
from temp_table_dt_fx tf 
where r.customer_id = tf.customer_id
and r.rental_id = tf.rental_id;

select p.customer_id, p.payment_id, p.payment_date, tf.new_payment_date 
from payment p join temp_table_dt_fx tf 
	on p.customer_id = tf.customer_id
	and p.payment_id = tf.payment_id;

update payment p
set payment_date = new_payment_date
from temp_table_dt_fx tf 
where p.customer_id = tf.customer_id
and p.payment_id = tf.payment_id

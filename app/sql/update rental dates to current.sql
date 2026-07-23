BEGIN;

-- ============================================================
-- STEP 1: Shift rental and customer dates by 18 years
-- (guarded to only touch original historical data, not synthetic rows)
-- ============================================================

UPDATE rental
SET rental_date = rental_date + INTERVAL '18 years',
    return_date = return_date + INTERVAL '18 years'  -- NULL stays NULL automatically
    WHERE rental_date < '2020-01-01';

UPDATE customer
SET create_date = create_date + INTERVAL '18 years'
WHERE create_date < '2020-01-01';

-- ============================================================
-- STEP 2: Fix payment_date to be relative to its actual rental_date
-- (0-3 days after rental, matching the logic used in the synthetic generator)
-- Only touches payments linked to a rental via rental_id.
-- ============================================================

UPDATE payment p
SET payment_date = r.rental_date + (floor(random() * 4) || ' days')::interval
FROM rental r
WHERE p.rental_id = r.rental_id
  AND p.payment_date < '2020-01-01';

-- ============================================================
-- STEP 3: Handle any payments with no linked rental (rare, but exists
-- in the original dvdrental data — e.g. manual adjustments).
-- These have no rental_date to anchor to, so just apply the flat shift.
-- ============================================================

UPDATE payment
SET payment_date = payment_date + INTERVAL '18 years'
WHERE rental_id IS NULL
  AND payment_date < '2020-01-01';

-- ============================================================
-- VERIFY
-- ============================================================

SELECT MIN(rental_date), MAX(rental_date) FROM rental;
SELECT MIN(payment_date), MAX(payment_date) FROM payment;
SELECT MIN(create_date), MAX(create_date) FROM customer;

-- Spot check: payment_date should now be same-day to a few days after rental_date
SELECT r.rental_date, p.payment_date, p.payment_date - r.rental_date AS days_between
FROM payment p
JOIN rental r ON p.rental_id = r.rental_id
WHERE r.rental_date > '2020-01-01'
ORDER BY r.rental_date
LIMIT 20;

COMMIT;

-- email cleanup for duplicates
create table temp_email as (
with dup_em as (select email, count(*) from customer c
group by 1
having count(*)>1),
em as (select customer_id, c.email, split_part(c.email,'@',1) pt1, split_part(c.email,'@',2) pt2, row_number() over (partition by c.email order by customer_id) em_rnk
from customer c join dup_em d on c.email = d.email)
select customer_id, pt1||em_rnk||'@'||pt2 as new_em from em where em_rnk>1
);

select t.*,c.email  from temp_email t join customer c on t.customer_id = c.customer_id

update customer c
set email = t.new_em
from temp_email t
where c.customer_id=t.customer_id
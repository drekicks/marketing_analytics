select count(c.customer_id) from customer c;

select count(film_id) from film f ;

select count(store_id) from store s;

select count(rental_id) from rental r;

select count(actor_id) from actor a;

with rntl_cnt as (
select  f.title, count(r.rental_id) rentals,
row_number() over (order by count(r.rental_id) desc, title) as rental_rank
from rental r join inventory i 
	on r.inventory_id = i.inventory_id 
join film f
	on f.film_id = i.film_id 
group by 1
) 
select rental_rank, title, rentals
from rntl_cnt where rental_rank <=10;

select  s.store_id, c2.country , sum(amount) rental_amt from payment p join staff s 
	on p.staff_id = s.staff_id 
	join address a 
		on a.address_id = s.address_id 
	join city c
		on c.city_id= a.city_id 
	join country c2 
		on c2.country_id = c.country_id 
group by 1,2;

select date_trunc('month',payment_date)::date as rntl_mnth, sum(p.amount) revenue from payment p
group by 1
order by 1;

select avg(return_date - rental_date) as avg_actual_rental_duration
from rental
where return_date is not null;

--Stretch Goals:
select count(*) from information_schema."tables" t 
where t.table_schema ='public' and t.table_type ='BASE TABLE';

select distinct
    tc.table_schema,
    tc.table_name,
    kc.column_name,
    tc.constraint_type 
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kc
    ON tc.constraint_name = kc.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
and kc.table_schema ='public'
order by 2;

SELECT
    tc.table_schema,
    tc.table_name,
    kc.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kc
    ON tc.constraint_name = kc.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON rc.unique_constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
order by 2;

select psut.relname , psut.n_live_tup from pg_catalog.pg_stat_user_tables psut;

select table_name, c.column_name, c.data_type  from information_schema."columns" c 
where c.udt_catalog ='dvdrental'  and table_schema ='public' order by 1 ;
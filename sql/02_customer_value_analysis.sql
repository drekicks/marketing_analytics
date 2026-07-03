--1.
with cust_rev as (select p.customer_id,c.first_name , c.last_name, c3.country, sum(p.amount) revenue,
row_number() over(order by sum(p.amount) desc) as rev_rank
from payment p join customer c 
	on p.customer_id = c.customer_id 
join address a 
	on a.address_id = c.address_id 
join city c2 
	on c2.city_id = a.city_id 
join country c3
	on c3.country_id = c2.country_id 
group by 1,2,3,4
)
select first_name, last_name, country,revenue, rev_rank 
from cust_rev
where rev_rank<=20;

--2. 
select
	c.first_name,
	c.last_name,
	sum(p.amount) total_rev,
	count(distinct r.rental_id) rentals,
	round(avg(p.amount),2) avg_pymt
from customer c join rental r 
	on c.customer_id = r.customer_id
join payment p 
	on p.rental_id = r.rental_id 
	and p.customer_id = r.customer_id 
group by 1,2
order by 4 desc;

--3. 
with cust_rev as (
select customer_id, sum(p.amount) revenue  
from payment p  
group by 1),
rv_dcle as 
(
select customer_id, revenue , ntile(10) over(order by revenue desc) as rev_decile from cust_rev
),
cust_tier as(select customer_id, revenue,rev_decile, 
	case 
		when rev_decile = 1 then 'High Value'
		when rev_decile between 2 and 5 then 'Medium Value'
		else 'Low Value'
	end as value_tier
from rv_dcle
) select value_tier, min(revenue), max(revenue),count(*) from cust_tier group by 1 order by 1;
--select value_tier, min(rev_decile), max(rev_decile), min(revenue), max(revenue),count(*) from cust_tier group by 1 order by 2;

--4. 
select c3.country, count(distinct c.customer_id) customers, sum(p.amount) revenue
from payment p join customer c 
	on p.customer_id = c.customer_id 
join address a 
	on a.address_id = c.address_id 
join city c2 
	on c2.city_id = a.city_id 
join country c3 
	on c3.country_id = c2.country_id
group by 1
order by 2 desc;

--5. 
with cust_hist as (select r.customer_id, count(r.rental_id) num_rentals, sum(p.amount) revenue
from rental r join payment p 
	on r.rental_id = p.rental_id 
	and r.customer_id = p.customer_id 
group by 1
) 
, cust_rr as (select 
	customer_id,
	num_rentals, 
	--sum(num_rentals) over (order by num_rentals desc rows between unbounded preceding and current row) as running_rntl_ttl,
	revenue,
	sum(revenue) over (order by revenue desc rows between unbounded preceding and current row) as running_rev_ttl
from cust_hist),
cust_rr2 as (select 
	customer_id,
	num_rentals,
	--sum(num_rentals) over (order by num_rentals desc rows between unbounded preceding and current row) as running_rntl_ttl,
	ntile(5) over(order by num_rentals desc) q_tier,
	revenue,
	running_rev_ttl
from cust_rr)
select 
	case
		when q_tier<=2 then 'High Frequency'
		when q_tier between 3 and 4 then 'Medium Frequency'
		else 'Low Frequency'
	end as buyer_type,
	count(customer_id) num_custs,
	sum(revenue) ttl_rev,
	round(avg(revenue),2) avg_rev,
	round(avg(num_rentals),2) avg_rentals
from cust_rr2
group by 1
ORDER by min(
    CASE
        WHEN q_tier <= 2 THEN 1
        WHEN q_tier BETWEEN 3 AND 4 THEN 2
        ELSE 3
    end);

--6. 
select c.customer_id, first_name, last_name, max(r.rental_date)::date rcnt_rntl
from customer c join rental r 
	on c.customer_id = r.customer_id
group by 1,2,3;

--7. 
select distinct first_name, last_name
from customer c left join rental r 
	on c.customer_id = r.customer_id
where r.customer_id isnull; 

--this is just my analysis looking at most popular titles and categories. it wasn't one of the queries requeste.
select --title,
c."name",
count(distinct r.rental_id) rentals,
count(distinct i.inventory_id) inventory
from rental r join payment p 
	on r.customer_id = p.customer_id 
	and r.rental_id = p.rental_id 
join inventory i 
	on i.inventory_id = r.inventory_id 
join film f 
	on f.film_id = i.film_id 
join film_category fc 
	on fc.film_id = f.film_id 
join category c 
	on c.category_id = fc.category_id 
group by 1--,2
order by 2 desc;


select --title,
c."name",
count(distinct i.inventory_id) inventory
from  inventory i join film f 
	on f.film_id = i.film_id 
join film_category fc 
	on fc.film_id = f.film_id 
join category c 
	on c.category_id = fc.category_id 
group by 1--,2
order by 2 desc


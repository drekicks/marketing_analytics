with store_info as (
select s.store_id, (c.city::text || ', '::text) || cy.country::text AS store
from store s 
join address a 
	on a.address_id = s.address_id 
join city c 
	on c.city_id = a.city_id 
join country cy
	on cy.country_id = c.country_id 
),
cust_dtls as (
select 
	c.customer_id,
	c.first_name||' '||c.last_name as customer_name,
	c.email,
	c.active,
	si.store,
	c2.city,
	c3.country,
	coalesce(sum(p.amount),0) total_revenue,
	coalesce(count(distinct r.rental_id),0) totaL_rentals,
	coalesce(round(avg(p.amount),2),0) avg_payment_amount,
	max(r.rental_date)::date most_recent_rental_date
from customer c left join rental r 
	on c.customer_id = r.customer_id
left join payment p 
	on p.rental_id = r.rental_id 
	and p.customer_id = r.customer_id 
join address a 
	on a.address_id = c.address_id 
join city c2 
	on c2.city_id = a.city_id 
join country c3 
	on c3.country_id = c2.country_id 
join store_info si 
	on si.store_id = c.store_id 
group by 1,2,3,4,5,6,7
),
cust_dtls2 as
(
select 
	*,
	ntile(10) over(order by total_revenue desc) rev_decile
	from cust_dtls
)
select 
	customer_id,
	customer_name,
	email,
	active,
	store,
	city,
	country,
	total_revenue,
	total_rentals,
	avg_payment_amount,
	most_recent_rental_date,
	case 
		when rev_decile = 1 then 'High Value'
		when rev_decile between 2 and 5 then 'Medium Value'
		else 'Low Value'
	end as customer_tier
from cust_dtls2;

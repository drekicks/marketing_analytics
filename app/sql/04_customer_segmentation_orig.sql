--this is my code...going to use the code created by AI as it incorporates the categories and has boolean flags where customer can be in multiple segments which is better for Tableau.
with rent_hist as 
(
	select 
		customer_id, 
		'2006-04-15'::date curr_date,
		min(r.rental_date)::date first_rental, 
		max(r.rental_date)::date last_rental,
		count(distinct i.film_id) unique_films,
		count(distinct r.rental_id) total_rentals
	from rental r join inventory i 
		on r.inventory_id = i.inventory_id 
	group by 1
),
rent_hist2 as 
(
	select 
		customer_id,
		first_rental, 
		last_rental,
		unique_films,
		total_rentals,
		curr_date-first_rental customer_tenure_days, 
		curr_date -last_rental days_since_last_rental,
		extract(year from age(curr_date, first_rental))*12 +
		extract(month from age(curr_date, first_rental)) as customer_tenure_mnths
	from rent_hist
),
rent_hist3 as 
(
select *, round(unique_films/customer_tenure_mnths,2) uniq_films_mnth from rent_hist2
),
rent_hist4 as 
(
select *, ntile(3) over (order by uniq_films_mnth desc) as uniq_film_tertile from rent_hist3
),
rating_cte as 
(
	select 
		r.customer_id, 
		rating,
		row_number()over (partition by r.customer_id order by count(f.film_id) desc, rating asc) rating_rnk
	from rental r join inventory i 
		on r.inventory_id = i.inventory_id
	join film f 
		on f.film_id = i.film_id 
	join film_category fc 
		on fc.film_id = f.film_id 
	join category c 
		on c.category_id = fc.category_id 
	group by 1,2
),
fav_mpaa as 
(
	select * from rating_cte where rating_rnk=1
)
,
ctgry_cte as
(
	select 
		r.customer_id, 
		c.name,
		count(f.film_id),
		row_number()over (partition by r.customer_id order by count(f.film_id) desc) ctgry_rnk
	from rental r join inventory i 
		on r.inventory_id = i.inventory_id
	join film f 
		on f.film_id = i.film_id 
	join film_category fc 
		on fc.film_id = f.film_id 
	join category c 
		on c.category_id = fc.category_id 
	group by 1,2
),
fav_catg as
(
	select customer_id, name as fav_film_ctgry from ctgry_cte where ctgry_rnk=1
),
pymt_hist as 
(
	select 
		c.customer_id,
		coalesce(sum(p.amount),0) total_payments,
		round(coalesce(sum(p.amount),0)/coalesce(count(distinct r.rental_id),0),2) rev_per_rentals,
		coalesce(round(avg(p.amount),2),0) avg_payment_amount
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
	group by 1
),
pymt_hist2 as
(
select 
	*,
	ntile(10) over(order by total_payments desc) rev_decile
	from pymt_hist 
),
cust_seg as 
(
select 
	c.customer_id, 
	c.first_name||' '||c.last_name as customer_name,
	r.first_rental,
	r.last_rental,
	fm.rating as fav_mpaa_rating, 
	fc.fav_film_ctgry,
	r.unique_films,
	r.customer_tenure_days,
	r.days_since_last_rental, 
	r.customer_tenure_mnths,
	r.uniq_films_mnth,
	case 
		when rev_decile = 1 then 'High Value'
		when rev_decile between 2 and 5 then 'Medium Value'
		else 'Low Value'
	end as customer_tier,
	case 
		when days_since_last_rental < 91 then 'Active'
		else 'Lapsed'
	end as buyer_status,
	case
		when r.uniq_film_tertile = 1 then 'High Engagement'
		when r.uniq_film_tertile = 2 then 'Medium Engagement'
		else 'Low Engagement'
	end as buyer_engagement,	
	total_payments,
	rev_per_rentals,
	avg_payment_amount
from customer c left join rent_hist4 r 
	on c.customer_id = r.customer_id 
left join fav_mpaa fm 
	on c.customer_id = fm.customer_id  
left join fav_catg fc
	on c.customer_id = fc.customer_id
left join pymt_hist2 ph
	on c.customer_id = ph.customer_id 
)
select c.*, 
case 
	when c.customer_tier ='High Value' and c.buyer_status ='Lapsed' then 'Win-Back VIP'
	when c.customer_tier ='Medium Value' and c.buyer_status ='Lapsed' then 'Win-Back Growth'
	when c.customer_tier ='Low Value' and c.buyer_status ='Lapsed' then 'Win-Back Reactivation'
	when c.customer_tier ='Low Value' and c.buyer_engagement ='High Engagement' then 'Upsell-Core'
	when c.customer_tier ='Medium Value' and c.buyer_engagement ='High Engagement' then 'Upsell-Scale'
	when c.customer_tier ='Medium Value' and c.buyer_engagement ='Low Engagement' then 'Engagement Growth-Core'
	when c.customer_tier ='Low Value' and c.buyer_engagement ='Low Engagement' then 'Engagement Growth-Volume'
	when c.customer_tier ='High Value' and c.buyer_engagement ='High Engagement' and c.buyer_status ='Active' then 'Champions'
	else ''
end
from cust_seg c
order by 2

;
	


SELECT
    c.customer_id,
    cat.name AS category,
    COUNT(r.rental_id) AS rentals_in_category,
    COUNT(DISTINCT f.film_id) AS unique_films_in_category,
    MIN(r.rental_date) AS first_rental_in_category,
    MAX(r.rental_date) AS last_rental_in_category,
    coalesce(SUM(p.amount),0) AS revenue_in_category
FROM rental r
JOIN customer c   ON c.customer_id = r.customer_id
JOIN inventory i  ON i.inventory_id = r.inventory_id
JOIN film f       ON f.film_id = i.film_id
JOIN film_category fc ON fc.film_id = f.film_id
JOIN category cat ON cat.category_id = fc.category_id
LEFT JOIN payment p ON p.rental_id = r.rental_id
GROUP BY c.customer_id, cat.name
ORDER BY c.customer_id, rentals_in_category DESC;


SELECT
    sub.name AS category,
    COUNT(*) FILTER (WHERE rentals_in_category >= 3) AS customers_with_3plus_rentals,
    COUNT(*) AS total_customers_in_category,
    ROUND(100.0 * COUNT(*) FILTER (WHERE rentals_in_category >= 3) / COUNT(*), 1) AS pct_repeat_engaged
FROM (
    SELECT c.customer_id, cat.name, COUNT(r.rental_id) AS rentals_in_category
    FROM rental r
    JOIN customer c ON c.customer_id = r.customer_id
    JOIN inventory i ON i.inventory_id = r.inventory_id
    JOIN film f ON f.film_id = i.film_id
    JOIN film_category fc ON fc.film_id = f.film_id
    JOIN category cat ON cat.category_id = fc.category_id
    GROUP BY c.customer_id, cat.name
) sub
GROUP BY sub.name
ORDER BY pct_repeat_engaged DESC;

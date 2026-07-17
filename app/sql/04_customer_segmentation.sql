-- =====================================================================
-- CUSTOMER SEGMENTATION FOR TABLEAU
-- Builds: Value Tier, Recency, Engagement, Category Affinity segments
-- Output: one row per customer with segment flags + a single
--         priority-ordered primary_segment field for categorical viz
-- =====================================================================

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
),
engagement_tiled AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY films_per_month) AS engagement_tile
    FROM customer_metrics
),
engagement_final AS (
    SELECT
        *,
        CASE engagement_tile
            WHEN 1 THEN 'Very Low Engagement'
            WHEN 2 THEN 'Low Engagement'
            WHEN 3 THEN 'Moderate Engagement'
            when 4 then 'High Engagement'
            when 5 then 'Very High Engagement'
            else 'Review'
        END AS engagement_segment
    FROM engagement_tiled
),-- select engagement_segment, recency_segment, customer_tier, count(distinct customer_id) custs, avg(films_per_month) avg_fpm, min(films_per_month) min_fpm, max(films_per_month) max_fpm from engagement_final group by 1,2,3 order by 5;,
-- ---------------------------------------------------------------------
-- 3) Category affinity: per-customer rental counts by category
--    (this is your first query, reused here as a CTE)
-- ---------------------------------------------------------------------
category_rentals AS (
    SELECT
        c.customer_id,
        cat.name AS category,
        COUNT(r.rental_id)          AS rentals_in_category,
        COUNT(DISTINCT f.film_id)   AS unique_films_in_category,
        SUM(p.amount)                AS revenue_in_category
    FROM rental r
    JOIN customer c        ON c.customer_id = r.customer_id
    JOIN inventory i       ON i.inventory_id = r.inventory_id
    JOIN film f             ON f.film_id = i.film_id
    JOIN film_category fc   ON fc.film_id = f.film_id
    JOIN category cat       ON cat.category_id = fc.category_id
    LEFT JOIN payment p     ON p.rental_id = r.rental_id
    GROUP BY c.customer_id, cat.name
),
category_breadth AS (
    SELECT customer_id, COUNT(DISTINCT category) AS categories_touched
    FROM category_rentals
    GROUP BY customer_id
),
top_category_ranked AS (
    SELECT
        customer_id,
        category,
        rentals_in_category,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY rentals_in_category DESC, category ASC
        ) AS rn
    FROM category_rentals
),
top_category AS (
    SELECT customer_id, category AS top_rental_category, rentals_in_category AS top_category_rentals
    FROM top_category_ranked
    WHERE rn = 1
),
-- ---------------------------------------------------------------------
-- 4) Category-level repeat engagement (this is your second query, reused)
-- ---------------------------------------------------------------------
category_engagement_base AS (
    SELECT
        category,
        COUNT(*) FILTER (WHERE rentals_in_category >= 3) AS customers_with_3plus_rentals,
        COUNT(*)                                          AS total_customers_in_category,
        ROUND(100.0 * COUNT(*) FILTER (WHERE rentals_in_category >= 3) / COUNT(*), 1) AS pct_repeat_engaged
    FROM category_rentals
    GROUP BY category
),
category_engagement_tiled AS (
    SELECT
        *,
        NTILE(3) OVER (ORDER BY pct_repeat_engaged) AS category_engagement_tile
    FROM category_engagement_base
),
category_engagement_final AS (
    SELECT
        *,
        CASE category_engagement_tile
            WHEN 1 THEN 'Low Engagement Category'
            WHEN 2 THEN 'Medium Engagement Category'
            WHEN 3 THEN 'High Engagement Category'
        END AS category_engagement_tier
    FROM category_engagement_tiled
),
-- ---------------------------------------------------------------------
-- 5) Assemble full customer-level segmentation table + flags
-- ---------------------------------------------------------------------
customer_segments AS (
    SELECT
        e.customer_id,
        e.customer_name,
        e.country,
        e.fav_mpaa_rating,
        e.fav_film_ctgry,
        e.customer_tier,
        e.recency_segment,
        e.engagement_segment,
        e.total_payments,
        e.rev_per_rentals,
        e.avg_payment_amount,
        e.unique_films,
        e.films_per_month,
        e.customer_tenure_days,
        e.days_since_last_rental,
        e.total_rentals,
        cb.categories_touched,
        tc.top_rental_category,
        tc.top_category_rentals,
        cef.category_engagement_tier,
        -- Segment membership flags (NOT mutually exclusive — a customer can
        -- belong to more than one; use these for Tableau filter shelves)
        (e.customer_tier = 'High Value' AND e.recency_segment = 'Active'
            AND e.engagement_segment in ('High Engagement','Very High Engagement'))
            AS is_champion,
        (e.customer_tier = 'High Value' AND e.recency_segment = 'Lapsed')
            AS is_winback_vip,
        (e.customer_tier = 'Medium Value' AND e.recency_segment = 'Lapsed')
            AS is_winback_growth,
        (e.customer_tier = 'Low Value' AND e.recency_segment = 'Lapsed')
            AS is_winback_reactivation,
        (e.customer_tier = 'Low Value' AND e.engagement_segment in ('High Engagement','Very High Engagement','Moderate Engagement') and e.recency_segment='Active')
            AS is_upsell_core,
        (e.customer_tier = 'Medium Value' AND e.engagement_segment in ('High Engagement','Very High Engagement','Moderate Engagement') and e.recency_segment='Active')
            AS is_upsell_scale,
        --(e.customer_tier = 'Medium Value' AND e.engagement_segment in ('Very Low Engagement','Low Engagement'))
          --  AS is_engagement_growth_scale,
        (e.customer_tier in ('Low Value','Medium Value') AND e.engagement_segment in ('Very Low Engagement','Low Engagement'))
            AS is_engagement_growth,
        (e.recency_segment = 'Pre-Lapsed') as is_churn_watchlist,
        /*(e.customer_tier in ('Medium Value','High Value') AND e.recency_segment = 'Pre-Lapsed'
            AND e.engagement_segment in ('High Engagement','Very High Engagement','Moderate Engagement'))
            AS is_churn_watchlist,*/
        (cb.categories_touched <= 12)
            AS is_narrow_explorer
    FROM engagement_final e
    LEFT JOIN category_breadth cb          ON cb.customer_id = e.customer_id
    LEFT JOIN top_category tc              ON tc.customer_id = e.customer_id
    LEFT JOIN category_engagement_final cef ON cef.category = tc.top_rental_category
)
-- =======================================================================
-- FINAL OUTPUT — point Tableau at this
-- primary_segment = single categorical field, priority-ordered so every
-- customer gets exactly one label for color/filter shelves; the
-- is_* boolean flags let you build multi-segment filters independently.
-- =======================================================================
SELECT
    *,
    CASE
        WHEN is_champion                  THEN 'Champion'
        WHEN is_winback_vip               THEN 'Win-Back VIP'
        WHEN is_winback_growth            THEN 'Win-Back Growth'
        WHEN is_winback_reactivation      THEN 'Win-Back Reactivation'
        WHEN is_upsell_scale              THEN 'Upsell - Scale'
        WHEN is_upsell_core               THEN 'Upsell - Core'
        --WHEN is_engagement_growth_scale    THEN 'Engagement Growth - Scale'
        WHEN is_engagement_growth	      THEN 'Engagement Growth'
        when is_churn_watchlist			  then 'Churn Watchlist'
        WHEN is_narrow_explorer           THEN 'Category Expansion'
        ELSE 'Maintain'
    END AS primary_segment,
    case 
    	when is_champion or is_upsell_scale then 'Champion'
    	when is_winback_vip or is_winback_growth or is_winback_reactivation then 'Win-Back'
    	when is_upsell_core or is_engagement_growth then 'Growth'
    	when is_churn_watchlist then 'Churn Watchlist'
    	else 'Review'
    end as market_segment
FROM customer_segments;
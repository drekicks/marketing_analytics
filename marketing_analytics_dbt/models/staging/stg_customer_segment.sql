select
    customer_id,
    country,
    primary_segment,
    customer_tier,
    market_segment as customer_segment,
    fav_film_ctgry,
    recency_segment,
    is_champion,
    is_churn_watchlist,
    is_engagement_growth,
    is_narrow_explorer,
    is_upsell_core,
    is_upsell_scale,
    is_winback_growth,
    is_winback_reactivation,
    is_winback_vip,
    category_engagement_tier
from {{ source('dvdrental', 'customer_segment') }}
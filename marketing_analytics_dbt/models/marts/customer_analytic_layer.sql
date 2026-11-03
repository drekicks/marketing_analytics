{#
  grants: the app's read-only role (customer text-to-SQL) exists only in Neon.

  replica identity: Neon has a logical-replication publication covering this
  table, and Postgres rejects DELETE on a published table without a replica
  identity. Incremental runs update rows with DELETE + INSERT, so:
    - pre_hook sets it on an existing table before the incremental DELETE
      (skipped on a first build or full refresh, when the table is new);
    - post_hook sets it on every newly created or fully refreshed table.
  FULL (not USING INDEX) avoids index-name clashes with the backup table dbt
  keeps during --full-refresh. Postgres only; other targets are unaffected.
#}
{{ config(
    materialized='incremental',
    unique_key=['campaign_id', 'customer_id'],
    grants={'select': ['app_readonly']} if target.name == 'neon' else {},
    pre_hook="{% if is_incremental() and target.type == 'postgres' %}alter table {{ this }} replica identity full{% endif %}",
    post_hook="{% if target.type == 'postgres' %}alter table {{ this }} replica identity full{% endif %}"
) }}

select
cr.customer_id,
cr.campaign_id,
cr.campaign_name,
cs.country,
cr.start_date,
cr.end_date,
cs.primary_segment,
cs.customer_tier,
cr.customer_segment,
cs.fav_film_ctgry,
cs.recency_segment,
cs.is_champion,
cs.is_churn_watchlist,
cs.is_engagement_growth,
cs.is_narrow_explorer,
cs.is_upsell_core,
cs.is_upsell_scale,
cs.is_winback_growth,
cs.is_winback_reactivation,
cs.is_winback_vip,
cr.treatment_group,
cr.conversion_flag,
cr.campaign_revenue,
cs.category_engagement_tier,
offer_cost,
contact_cost,
offer_cost + contact_cost as total_campaign_cost,
cr.updated_at as updated_at
from {{ ref('stg_campaign_results') }} cr join {{ ref('stg_customer_segment') }} cs
	on cr.customer_id = cs.customer_id

{% if is_incremental() %}
where cr.updated_at > (
    select coalesce(max(t.updated_at),'1990-01-01'::date)
    from {{ this }} as t
)
{% endif %}
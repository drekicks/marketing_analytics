{# Every campaign with results must have a goal; the app errors without one. #}
select cps.campaign_id
from {{ ref('campaign_performance_summary') }} cps
left join {{ ref('campaign_goals') }} cg
    on cg.campaign_id = cps.campaign_id
where cg.campaign_id is null

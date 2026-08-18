# Marketing Data Products

## Campaign Performance Summary

**Purpose:**  
Provides campaign-level performance metrics for marketing analysis.

**Grain:**  
One row per campaign.

**Primary Consumers:**  
AI Marketing Analytics Assistant, analysts, reporting.

**Source:**  
Campaign results data.

**Key Measures:**  
- Audience size
- Campaign revenue
- Conversion rate
- Absolute lift

**Quality Expectations:**  
Campaign identifiers must be populated and campaign performance
metrics must pass defined business-rule validations.

**dbt Model:**  
campaign_performance_summary

## Segment Performance Summary

**Purpose:**  
Provides segment-level performance metrics for marketing analysis.

**Grain:**  
One row per segment per campaign.

**Primary Consumers:**  
AI Marketing Analytics Assistant, analysts, reporting.

**Source:**  
Campaign results data.

**Key Measures:**  
- Audience size
- Campaign revenue
- Conversion rate
- Absolute lift
- Campaign Cost
- Revenue per customer
- Incremental revenue
- Marketing ROI

**Quality Expectations:**  
Campaign and segment identifiers must be populated and segment performance
metrics must pass defined business-rule validations.

**dbt Model:**  
segment_performance_summary

## Customer Analytic Layer

**Purpose:**  
Provides customer-level performance metrics for marketing analysis.

**Grain:**
One row per customer per campaign.

**Primary Consumers:**  
Analysts, downstream applications, AI-ready data use cases.

**Source:**  
Campaign results data.

**Key Measures:**  
- Campaign revenue
- Campaign Cost

**Quality Expectations:**  
Customer, campaign and segment identifiers must be populated and customer performance
metrics must pass defined business-rule validations.

**dbt Model:**  
customer_analytic_layer

# Marketing Data Quality Rules

## Conversion Rate Validity

**Rule:**  
Campaign conversion rates must be between 0 and 1.

**Business Rationale:**  
A conversion rate represents a proportion of the audience and
therefore cannot be negative or exceed 100%.

**Applies To:**  
- Campaign Performance Summary
- Segment Performance Summary

**Validation:**  
Enforced through dbt data tests.

**Failure Impact:**  
The affected data product should not be considered business-ready
until the validation failure is resolved.

## Data Product Grain

**Rule:**  
Campaign summary is one row per campaign. 
Segment summary is one row per segment per campaign.
Customer analytic layer is one row per customer per campaign.

**Business Rationale:**  
Each data product must contain only one record at its defined grain to prevent duplicate records 
and incorrect aggregation.

**Applies To:**  
- Campaign Performance Summary
- Segment Performance Summary
- Customer Analytic Layer

**Validation:**  
Enforced through dbt data tests.

**Failure Impact:**  
The affected data product should not be considered business-ready
until the validation failure is resolved.

## Conversions vs Audience

**Rule:**  
Conversions must be less than or equal to the audience.

**Business Rationale:**  
Conversions are a subset of the audience who have been converted, so they cannot be greater than the audience.

**Applies To:**  
- Campaign Performance Summary
- Segment Performance Summary

**Validation:**  
Enforced through dbt data tests.

**Failure Impact:**  
The affected data product should not be considered business-ready
until the validation failure is resolved.

## Campaign Costs

**Rule:**  
Customers in the TEST group must have a contact cost greater than zero.
Customers in the CONTROL group must have zero contact and offer costs.
TEST customers who convert must also have an offer cost greater than zero.

**Business Rationale:**  
Customers in the Control group were not part of the campaign and therefore have no costs.

**Applies To:**  
- Campaign Performance Summary
- Segment Performance Summary
- Customer Analytic Layer

**Validation:**  
Enforced through dbt data tests.

**Failure Impact:**  
The affected data product should not be considered business-ready
until the validation failure is resolved.

## Campaign Revenue

**Rule:**  
Campaign revenue must be greater than or equal to 0.

**Business Rationale:**  
Campaign revenue captures purchases, not returns, so numbers should be positive.

**Applies To:**  
- Campaign Performance Summary
- Segment Performance Summary
- Customer Analytic Layer

**Validation:**  
Enforced through dbt data tests.

**Failure Impact:**  
The affected data product should not be considered business-ready
until the validation failure is resolved.

## Required Identifiers

**Rule:**  
Required customer, campaign, and segment identifiers must not be null.

**Business Rationale:**  
Records without the identifiers required by the data product's defined grain cannot be reliably attributed or analyzed.

**Required Fields:**  
- Campaign Performance Summary: `campaign_id`
- Segment Performance Summary: `campaign_id`, `customer_segment`
- Customer Analytic Layer: `campaign_id`, `customer_id`, `customer_segment`

**Applies To:**  
- Campaign Performance Summary
- Segment Performance Summary
- Customer Analytic Layer

**Validation:**  
Enforced through dbt data tests.

**Failure Impact:**  
The affected data product should not be considered business-ready
until the validation failure is resolved.
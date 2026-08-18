# Customer Segments

## Champion

**Definition:**  
These are customers who spend the most, are active, and highly engaged.

**Business Rule:**  
customer_tier  in ('High Value', 'Medium Value') AND recency_segment = 'Active'
AND engagement_segment in ('High Engagement','Very High Engagement','Moderate Engagement')

**Available In:**  
`segment_performance_summary` — campaign + customer segment performance
`customer_analytic_layer` — customer + campaign level

## Growth

**Definition:**  
These are customers where we have the potential to grow their business with us.

**Business Rule:**  
(
customer_tier = 'Low Value' 
and recency_segment='Active'
AND engagement_segment in 
('High Engagement','Very High Engagement','Moderate Engagement')
)
OR
(
customer_tier in ('Low Value','Medium Value')
AND engagement_segment in ('Very Low Engagement','Low Engagement')
)

**Available In:**  
`segment_performance_summary` — campaign + customer segment performance
`customer_analytic_layer` — customer + campaign level

## Churn Watchlist

**Definition:**  
Customers whose last purchase occurred 61 to 175 days before the data snapshot date. 

**Business Rule:**  
recency_segment = 'Pre-Lapsed'

**Available In:**  
`segment_performance_summary` — campaign + customer segment performance
`customer_analytic_layer` — customer + campaign level

## Win-Back

**Definition:**  
Customers whose last purchase occurred more than 175 days before the data snapshot date.

**Business Rule:**  
recency_segment = 'Lapsed'

**Available In:**  
- `segment_performance_summary` — campaign + customer segment performance
- `customer_analytic_layer` — customer + campaign level

# Segmentation Attributes

## Customer Tier

**Definition:**  
Customer tier is a classification of customers based on their revenue. Customers are divided into 10 equal groups (deciles 1 to 10). 
Decile 1 is the highest revenue.

### High Value
Customers in Decile 1

### Medium Value
Customers in deciles 2 to 5  

### Low Value
Customers in deciles 6 to 10 

**Available In:**  
- `segment_performance_summary` — campaign + customer segment performance
- `customer_analytic_layer` — customer + campaign level

## Recency Segment

**Definition:**  
The recency segment is a classification of customers based on their recency of the last purchase based on the data snapshot date.

### Active
Purchased within the last 60 days.

### Pre-Lapsed
Purchased within the last 61 to 175 days.

### Lapsed
Purchase greater than 175 days.

**Available In:**  
- `segment_performance_summary` — campaign + customer segment performance
- `customer_analytic_layer` — customer + campaign level

## Engagement Segment

**Definition:**  
Based on customer tenure, this is the number of unique films a customer has rented per month. Customers are divided into 5 equal groups (Quintile 1 to 5). 
The higher the number of films rented, the higher the engagement and decile.

### Very High Engagement
Customers in Quintile 5.

### High Engagement
Customers in Quintile 4.

### Moderate Engagement
Customers in Quintile 3.

### Low Engagement
Customers in Quintile 2.

### Very Low Engagement
Customers in Quintile 1.

**Available In:**  
- `segment_performance_summary` — campaign + customer segment performance
- `customer_analytic_layer` — customer + campaign level

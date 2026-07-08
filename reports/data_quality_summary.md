I reviewed a customer dataset of 599 records. The dataset include customer contact details, customer revenue, average payment amount, total number of rentals, active flag along with the store information. I created customer tiers of High,Medium and Low based on revenue.

Validation were done on email, revenue, customer ID and countries. These are the results of the validation. There were no issues found with any of the items checked.

DATA VALIDATION SUMMARY
=======================================================
Duplicate Customer Ids..................         0 issue(s)
Null Emails.............................         0 issue(s)
Negative Revenue........................         0 issue(s)
Future Rental Dates.....................         0 issue(s)
Missing Countries.......................         0 issue(s)
Duplicate Emails........................         0 issue(s)
Invalid Emails..........................         0 issue(s)
Non Positive Rentals....................         0 issue(s)
Rentals Revenue Mismatch................         0 issue(s)
Country Whitespace Issues...............         0 issue(s)

Data Validation Definition:
Future Rental Dates: rental date > current date
Rentals Revenue Mismatch: customer has rentals, but no revenue or vice versa.
Country Whitespace Issues: spaces before after the value; for example 'Canada '.
Invalid Emails: email doesn't follow standard email format; for example, it doesn't have @. 

I would recommend getting an understanding of how active is determined. Is it based on latest rental date? Is it something the customer requested? There are instance where the customer is inactive, but has rentals more recently than some active customers. Once you have that definition, I would set up validation to make sure active column is being maintained correctly.
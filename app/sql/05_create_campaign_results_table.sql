-- public.customer definition

-- Drop table

-- DROP TABLE public.customer;

CREATE TABLE public.campaign_results (
	customer_id serial4 NOT NULL,
	customer_segment varchar(45) not null,
	campaign_id varchar(20) not null,
	campaign_name varchar(75) not null,
	treatment_grp varchar(15) not null,
	contacted_flg varchar(1) not null,
	response_flg varchar(1) not null,
	cnvrsn_flg varchar(1) not null,
	cmpgn_rvn numeric(5, 2) NOT NULL,
	contact_cost numeric(5, 2) NOT NULL,
	offer_cost numeric(5, 2) NOT NULL,
	start_date timestamp NOT NULL,
	end_date timestamp NOT null
	--CONSTRAINT cmpgn_pkey PRIMARY KEY (customer_id)
);
CREATE INDEX idx_fk_cmpgn_customer_id ON public.campaign_results USING btree (customer_id)

CREATE UNIQUE INDEX idx_unq_rental_rental_date_inventory_id_customer_id ON public.rental USING btree (rental_date, inventory_id, customer_id);

-- public.payment foreign keys

ALTER TABLE public.campaign_results ADD CONSTRAINT campaign_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customer(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE;


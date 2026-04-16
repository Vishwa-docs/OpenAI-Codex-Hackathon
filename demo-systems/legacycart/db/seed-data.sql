insert into customers (email, full_name) values
  ('customer@example.com', 'Ari Example'),
  ('buyer@example.com', 'Jamie Buyer');

insert into orders (customer_id, total_amount, status) values
  (1, 149.99, 'paid'),
  (2, 78.50, 'pending');


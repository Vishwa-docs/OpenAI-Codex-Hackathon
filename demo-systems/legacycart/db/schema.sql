create table customers (
  id bigserial primary key,
  email text not null,
  full_name text not null,
  created_at timestamptz not null default now()
);

create table orders (
  id bigserial primary key,
  customer_id bigint not null references customers(id),
  total_amount numeric(12, 2) not null,
  status text not null,
  created_at timestamptz not null default now()
);


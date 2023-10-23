create table
  public.barrels_catalog (
    barrel_id bigint generated by default as identity,
    sku text not null,
    ml_per_barrel integer not null,
    constraint barrels_pkey primary key (barrel_id)
  ) tablespace pg_default;
create table
  public.barrels_history (
    id bigint generated by default as identity,
    catalog_id bigint not null,
    barrel_id bigint not null,
    cost integer not null,
    quantity bigint not null default '0'::bigint,
    constraint catalog_loggin_pkey primary key (id),
    constraint barrels_history_barrel_id_fkey foreign key (barrel_id) references barrels_catalog (barrel_id) on update cascade on delete cascade,
    constraint barrels_history_catalog_id_fkey foreign key (catalog_id) references barrels_sessions (catalog_id) on update cascade on delete cascade
  ) tablespace pg_default;
create table
  public.barrels_sessions (
    catalog_id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    constraint barrel_catalog_sessions_pkey primary key (catalog_id)
  ) tablespace pg_default;
create table
  public.carts (
    cart_id bigint generated by default as identity,
    customer_name text not null,
    created_at timestamp with time zone not null default now(),
    constraint carts_pkey1 primary key (cart_id)
  ) tablespace pg_default;
create table
  public.carts_transactions (
    id bigint generated by default as identity,
    cart_id bigint not null,
    sku text not null,
    quantity integer not null,
    created_at timestamp with time zone not null default now(),
    constraint carts_transactions_pkey primary key (id),
    constraint carts_transactions_cart_id_fkey foreign key (cart_id) references carts (cart_id) on delete cascade,
    constraint carts_transactions_sku_fkey foreign key (sku) references potion_inventory (sku)
  ) tablespace pg_default;
create table
  public.potion_inventory (
    id bigint generated by default as identity,
    sku text not null,
    type_red smallint not null,
    type_green smallint not null,
    type_blue smallint not null,
    cost integer not null,
    type_dark integer not null default 0,
    name text null,
    constraint potion_inventory_pkey primary key (id),
    constraint potion_inventory_id_key unique (id),
    constraint potion_inventory_sku_key unique (sku)
  ) tablespace pg_default;
create table
  public.potion_ledger (
    id bigint generated by default as identity,
    description text null,
    created_at timestamp with time zone not null default now(),
    potion_id bigint not null,
    d_quan bigint not null default '0'::bigint,
    constraint potion_ledger_pkey primary key (id),
    constraint potion_ledger_potion_id_fkey foreign key (potion_id) references potion_inventory (id)
  ) tablespace pg_default;
create table
  public.stock_ledger (
    id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    description text null,
    d_gold bigint not null default '0'::bigint,
    d_red bigint not null default '0'::bigint,
    d_green bigint not null default '0'::bigint,
    d_blue bigint not null default '0'::bigint,
    d_dark bigint not null default '0'::bigint,
    constraint stock_ledger_pkey primary key (id)
  ) tablespace pg_default;
1.1. customer ↔ order_items
Tabelas: olist_customers_dataset (PK: customer_id) → olist_orders_dataset (FK: customer_id)
Cardinalidade: 1:N (um cliente pode ter vários pedidos).
Observação: customer_unique_id identifica a pessoa ao longo do tempo; um mesmo customer_unique_id pode aparecer com múltiplos customer_id.

1.2. orders ↔ order_items
Tabelas: olist_orders_dataset (PK: order_id) → olist_order_items_dataset (FK: order_id , PK composta: order_id , order_item_id)
cardinalidade: 1:N (um pedido tem vários itens).

1.3. order_items ↔ products
Tabelas: olist_order_items_dataset (FK: product_id) → olist_products_dataset (PK: product_id)
Cardinalidade: N:1 (muitos itens referenciam um produto).

1.4. order_items ↔ sellers
Tabelas: olist_order_items_dataset (FK: seller_id) → olist_sellers_dataset (PK: seller_id)
Cardinalidade: N:1 (muitos itens referenciam um seller).

1.5. orders ↔ payments
Tabelas: olist_orders_dataset (PK: order_id) → olist_order_payments_dataset (FK: order_id , PK composta sugerida: order_id , payment_sequential)
Cardinalidade: 1:N (um pedido pode ter várias parcelas/lançamentos de pagamento).

1.6. orders ↔ reviews
Tabelas: olist_orders_dataset (PK: order_id) → olist_order_reviews_dataset (FK: order_id , PK: review_id)
Cardinalidade: 1:0..1 (em regra há no máximo 1 review por pedido; alguns pedidos não têm review).

Boa prática: ao encontrar mais de um review para um pedido, usar o mais recente por review_creation_date.

1.7. products ↔ product_category
Tabelas: olist_products_dataset (coluna: product_category_name) → product_category_translation (PK: product_category_name)
Cardinalidade: N:1 (muitos produtos mapeiam para um nome de categoria).
Observação: há produtos sem categoria → usar LEFT JOIN.

1.8. clientes/sellers ↔ geolocation
Tabelas:
olist_customers_dataset.customer_zip_code_prefix → olist_geolocation_dataset.geolocation_zip_code_prefix
olist_sellers_dataset.seller_zip_code_prefix → olist_geolocation_dataset.geolocation_zip_code_prefix
Cardinalidade: 1:N do ponto de vista do prefixo (um mesmo prefixo aparece várias vezes com coordenadas próximas).

Observação: olist_geolocation_dataset não tem PK única; contém múltiplas amostras por prefixo. Use agregações (ex.: média/mediana de lat/long) ou dedupe conforme a análise.
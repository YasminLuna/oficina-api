from prometheus_client import Counter, Histogram

HTTP_LATENCY = Histogram('oficina_http_latency_seconds', 'API latency', ['method','path'])
ORDERS_CREATED = Counter('oficina_orders_created_total', 'Orders created')
ORDER_FAILURES = Counter('oficina_order_failures_total', 'Order processing failures')

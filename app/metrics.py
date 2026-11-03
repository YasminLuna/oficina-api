from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    'oficina_http_requests_total',
    'HTTP requests processed by the API',
    ['method', 'path', 'status_code'],
)
HTTP_LATENCY = Histogram(
    'oficina_http_latency_seconds',
    'API request latency in seconds',
    ['method', 'path'],
)
ORDERS_CREATED = Counter(
    'oficina_orders_created_total',
    'Service orders created',
)
ORDER_FAILURES = Counter(
    'oficina_order_failures_total',
    'Service order processing failures',
)
INTEGRATION_ERRORS = Counter(
    'oficina_integration_errors_total',
    'Errors while integrating API, database or external dependencies',
    ['integration', 'operation'],
)
STATUS_DURATION_SECONDS = Histogram(
    'oficina_order_status_duration_seconds',
    'Time spent by a service order in each status',
    ['status'],
)
STATUS_CHANGES = Counter(
    'oficina_order_status_changes_total',
    'Service order status transitions',
    ['from_status', 'to_status'],
)

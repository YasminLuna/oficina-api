import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Session

from .core.logging import configure_logging
from .core.security import current_customer
from .db import Base, engine, get_db
from .metrics import (
    HTTP_LATENCY,
    HTTP_REQUESTS,
    INTEGRATION_ERRORS,
    ORDER_FAILURES,
    ORDERS_CREATED,
    STATUS_CHANGES,
    STATUS_DURATION_SECONDS,
)
from .models import Customer, OrderStatus, OrderStatusHistory, ServiceOrder
from .schemas import CustomerCreate, CustomerOut, OrderCreate, OrderOut

configure_logging()
logger = logging.getLogger('oficina.api')
Base.metadata.create_all(bind=engine)
app = FastAPI(title='Oficina API - Fase 3', version='3.0.0')


@app.middleware('http')
async def correlation_and_metrics(request: Request, call_next):
    correlation_id = request.headers.get('x-correlation-id') or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        ORDER_FAILURES.inc()
        INTEGRATION_ERRORS.labels('api', request.url.path).inc()
        logger.exception(
            'request_failed',
            extra={
                'correlation_id': correlation_id,
                'path': request.url.path,
                'method': request.method,
            },
        )
        raise

    elapsed = time.perf_counter() - start
    path = request.scope.get('route').path if request.scope.get('route') else request.url.path
    HTTP_LATENCY.labels(request.method, path).observe(elapsed)
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    response.headers['x-correlation-id'] = correlation_id
    logger.info(
        'request_completed',
        extra={
            'correlation_id': correlation_id,
            'path': request.url.path,
            'method': request.method,
            'status_code': response.status_code,
            'duration_ms': round(elapsed * 1000, 2),
        },
    )
    return response


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/ready')
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except Exception as exc:
        INTEGRATION_ERRORS.labels('postgresql', 'readiness').inc()
        raise HTTPException(status_code=503, detail='Banco de dados indisponível') from exc
    return {'status': 'ready'}


@app.get('/metrics', include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post('/internal/customers', response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    document = ''.join(filter(str.isdigit, payload.document))
    existing = db.scalar(select(Customer).where(Customer.document == document))
    if existing:
        return existing
    customer = Customer(document=document, name=payload.name)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.post('/api/v1/orders', response_model=OrderOut)
def create_order(
    payload: OrderCreate,
    claims: dict = Depends(current_customer),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, claims['sub'])
    if not customer or not customer.active:
        raise HTTPException(status_code=403, detail='Cliente inativo ou inexistente')

    order = ServiceOrder(customer_id=customer.id, vehicle_plate=payload.vehicle_plate.upper())
    db.add(order)
    db.flush()
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.RECEIVED))
    db.commit()
    db.refresh(order)
    ORDERS_CREATED.inc()
    return order


@app.get('/api/v1/orders', response_model=list[OrderOut])
def list_orders(
    claims: dict = Depends(current_customer),
    db: Session = Depends(get_db),
):
    del claims
    priority = [
        OrderStatus.EXECUTION,
        OrderStatus.WAITING_APPROVAL,
        OrderStatus.DIAGNOSIS,
        OrderStatus.RECEIVED,
    ]
    rows = db.scalars(select(ServiceOrder).where(ServiceOrder.status.in_(priority))).all()
    rank = {status: index for index, status in enumerate(priority)}
    return sorted(rows, key=lambda item: (rank[item.status], item.created_at))


@app.patch('/api/v1/orders/{order_id}/status', response_model=OrderOut)
def update_status(
    order_id: str,
    status: OrderStatus,
    claims: dict = Depends(current_customer),
    db: Session = Depends(get_db),
):
    del claims
    order = db.get(ServiceOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail='OS não encontrada')

    previous_status = order.status
    if previous_status == status:
        return order

    now = datetime.now(timezone.utc)
    open_history = db.scalar(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order.id)
        .where(OrderStatusHistory.exited_at.is_(None))
        .order_by(OrderStatusHistory.entered_at.desc())
    )
    if open_history:
        entered_at = open_history.entered_at
        if entered_at.tzinfo is None:
            entered_at = entered_at.replace(tzinfo=timezone.utc)
        duration_seconds = max((now - entered_at).total_seconds(), 0)
        open_history.exited_at = now
        STATUS_DURATION_SECONDS.labels(previous_status.value).observe(duration_seconds)

    order.status = status
    db.add(OrderStatusHistory(order_id=order.id, status=status, entered_at=now))
    db.commit()
    db.refresh(order)
    STATUS_CHANGES.labels(previous_status.value, status.value).inc()
    return order

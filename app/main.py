import logging
import time
import uuid
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Session

from .core.logging import configure_logging
from .core.security import current_customer
from .db import Base, engine, get_db
from .metrics import HTTP_LATENCY, ORDERS_CREATED, ORDER_FAILURES
from .models import Customer, OrderStatus, ServiceOrder
from .schemas import CustomerCreate, CustomerOut, OrderCreate, OrderOut

configure_logging()
logger = logging.getLogger('oficina.api')
Base.metadata.create_all(bind=engine)
app = FastAPI(title='Oficina API - Fase 3', version='3.0.0')

@app.middleware('http')
async def correlation_and_metrics(request: Request, call_next):
    cid = request.headers.get('x-correlation-id') or str(uuid.uuid4())
    start=time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        ORDER_FAILURES.inc()
        logger.exception('request_failed', extra={'correlation_id': cid, 'path': request.url.path, 'method': request.method})
        raise
    elapsed=time.perf_counter()-start
    HTTP_LATENCY.labels(request.method, request.url.path).observe(elapsed)
    response.headers['x-correlation-id']=cid
    logger.info('request_completed', extra={'correlation_id': cid, 'path': request.url.path, 'method': request.method, 'status_code': response.status_code})
    return response

@app.get('/health')
def health(): return {'status':'ok'}

@app.get('/ready')
def ready(db: Session=Depends(get_db)):
    db.execute(select(1))
    return {'status':'ready'}

@app.get('/metrics', include_in_schema=False)
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post('/internal/customers', response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session=Depends(get_db)):
    customer=Customer(document=''.join(filter(str.isdigit,payload.document)), name=payload.name)
    db.add(customer); db.commit(); db.refresh(customer)
    return customer

@app.post('/api/v1/orders', response_model=OrderOut)
def create_order(payload: OrderCreate, claims: dict=Depends(current_customer), db: Session=Depends(get_db)):
    customer=db.get(Customer, claims['sub'])
    if not customer or not customer.active:
        raise HTTPException(403,'Cliente inativo ou inexistente')
    order=ServiceOrder(customer_id=customer.id, vehicle_plate=payload.vehicle_plate.upper())
    db.add(order); db.commit(); db.refresh(order); ORDERS_CREATED.inc()
    return order

@app.get('/api/v1/orders', response_model=list[OrderOut])
def list_orders(claims: dict=Depends(current_customer), db: Session=Depends(get_db)):
    priority = [OrderStatus.EXECUTION, OrderStatus.WAITING_APPROVAL, OrderStatus.DIAGNOSIS, OrderStatus.RECEIVED]
    rows=db.scalars(select(ServiceOrder).where(ServiceOrder.status.in_(priority))).all()
    rank={s:i for i,s in enumerate(priority)}
    return sorted(rows, key=lambda x:(rank[x.status], x.created_at))

@app.patch('/api/v1/orders/{order_id}/status', response_model=OrderOut)
def update_status(order_id: str, status: OrderStatus, claims: dict=Depends(current_customer), db: Session=Depends(get_db)):
    order=db.get(ServiceOrder, order_id)
    if not order: raise HTTPException(404,'OS não encontrada')
    order.status=status; db.commit(); db.refresh(order)
    return order

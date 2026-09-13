import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class OrderStatus(str, enum.Enum):
    RECEIVED='Recebida'
    DIAGNOSIS='Diagnóstico'
    WAITING_APPROVAL='Aguardando Aprovação'
    EXECUTION='Execução'
    FINISHED='Finalizada'
    DELIVERED='Entregue'

class Customer(Base):
    __tablename__='customers'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class ServiceOrder(Base):
    __tablename__='service_orders'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(ForeignKey('customers.id'), index=True)
    vehicle_plate: Mapped[str] = mapped_column(String(10), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.RECEIVED, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

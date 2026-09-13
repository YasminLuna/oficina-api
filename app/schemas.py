from pydantic import BaseModel, Field
from .models import OrderStatus

class CustomerCreate(BaseModel):
    document: str = Field(min_length=11, max_length=14)
    name: str

class CustomerOut(CustomerCreate):
    id: str
    active: bool
    model_config = {'from_attributes': True}

class OrderCreate(BaseModel):
    vehicle_plate: str

class OrderOut(BaseModel):
    id: str
    customer_id: str
    vehicle_plate: str
    status: OrderStatus
    model_config = {'from_attributes': True}

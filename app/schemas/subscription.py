from pydantic import BaseModel
from typing import Optional


class DomainCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SubscriptionPlanCreate(BaseModel):
    domain_id: int
    name: str
    duration_months: int
    price: float
    features: Optional[str] = None


class StartTrialRequest(BaseModel):
    domain_id: int


class ActivateSubscriptionRequest(BaseModel):
    plan_id: int
    payment_method: Optional[str] = "manual"
    transaction_id: Optional[str] = None
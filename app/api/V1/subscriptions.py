from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.subscription import Domain, SubscriptionPlan, Subscription, Payment

from app.schemas.subscription import (
    DomainCreate,
    SubscriptionPlanCreate,
    StartTrialRequest,
    ActivateSubscriptionRequest
)

from app.services import subscriptions_service

router = APIRouter(tags=["Domains & Subscriptions"])

@router.post('/api/domains')
async def create_domain(data: DomainCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.create_domain(data, current_user, db)

@router.get('/api/domains')
async def get_domains(db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.get_domains(db)

@router.post('/api/subscription-plans')
async def create_subscription_plan(data: SubscriptionPlanCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.create_subscription_plan(data, current_user, db)

@router.get('/api/subscription-plans')
async def get_subscription_plans(db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.get_subscription_plans(db)

@router.post('/api/subscriptions/start-trial')
async def start_trial(data: StartTrialRequest, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.start_trial(data, current_user, db)

@router.post('/api/subscriptions/activate')
async def activate_subscription(data: ActivateSubscriptionRequest, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.activate_subscription(data, current_user, db)

@router.get('/api/subscriptions/me')
async def get_my_subscription(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await subscriptions_service.get_my_subscription(current_user, db)

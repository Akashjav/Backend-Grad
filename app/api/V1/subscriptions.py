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

router = APIRouter(tags=["Domains & Subscriptions"])

@router.post("/api/domains")
async def create_domain(
    data: DomainCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create domains")

    existing = await db.execute(select(Domain).where(Domain.name == data.name))
    existing_domain = existing.scalar_one_or_none()
    if existing_domain:
        return {
            "message": "Domain already exists",
            "domain_id": existing_domain.id
        }

    domain = Domain(
        name=data.name,
        description=data.description
    )

    db.add(domain)
    await db.commit()
    await db.refresh(domain)

    return {
        "message": "Domain created successfully",
        "domain_id": domain.id
    }


@router.get("/api/domains")
async def get_domains(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Domain).order_by(Domain.name))
    domains = result.scalars().all()

    return [
        {
            "id": domain.id,
            "name": domain.name,
            "description": domain.description
        }
        for domain in domains
    ]

@router.post("/api/subscription-plans")
async def create_subscription_plan(
    data: SubscriptionPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create plans")

    domain_result = await db.execute(
        select(Domain).where(Domain.id == data.domain_id)
    )
    domain = domain_result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    plan = SubscriptionPlan(
        domain_id=data.domain_id,
        name=data.name,
        duration_months=data.duration_months,
        price=data.price,
        features=data.features
    )

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {
        "message": "Subscription plan created successfully",
        "plan_id": plan.id
    }


@router.get("/api/subscription-plans")
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SubscriptionPlan))
    plans = result.scalars().all()

    output = []

    for plan in plans:
        domain_result = await db.execute(
            select(Domain).where(Domain.id == plan.domain_id)
        )
        domain = domain_result.scalar_one_or_none()

        output.append({
            "id": plan.id,
            "domain_id": plan.domain_id,
            "domain_name": domain.name if domain else None,
            "name": plan.name,
            "duration_months": plan.duration_months,
            "price": plan.price,
            "features": plan.features
        })

    return output

@router.post("/api/subscriptions/start-trial")
async def start_trial(
    data: StartTrialRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can start trial")

    domain_result = await db.execute(
        select(Domain).where(Domain.id == data.domain_id)
    )
    domain = domain_result.scalar_one_or_none()

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    existing_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["trial", "active"])
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have an active or trial subscription"
        )

    trial_days = 7

    subscription = Subscription(
        user_id=current_user.id,
        domain_id=data.domain_id,
        plan_id=None,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=trial_days),
        status="trial",
        payment_status="unpaid"
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return {
        "message": "Trial started successfully",
        "subscription_id": subscription.id,
        "domain_id": subscription.domain_id,
        "status": subscription.status,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date
    }

@router.post("/api/subscriptions/activate")
async def activate_subscription(
    data: ActivateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can activate subscription")

    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == data.plan_id)
    )
    plan = plan_result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    current_subscription_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["trial", "active"])
        )
    )
    current_subscription = current_subscription_result.scalar_one_or_none()

    now = datetime.utcnow()

    end_date = now + timedelta(days=plan.duration_months * 30)

    if current_subscription:
        current_subscription.status = "expired"

    subscription = Subscription(
        user_id=current_user.id,
        domain_id=plan.domain_id,
        plan_id=plan.id,
        start_date=now,
        end_date=end_date,
        status="active",
        payment_status="paid"
    )

    db.add(subscription)
    await db.flush()

    payment = Payment(
        user_id=current_user.id,
        subscription_id=subscription.id,
        amount=plan.price,
        payment_method=data.payment_method,
        payment_status="paid",
        transaction_id=data.transaction_id
    )

    db.add(payment)
    await db.commit()
    await db.refresh(subscription)

    return {
        "message": "Subscription activated successfully",
        "subscription_id": subscription.id,
        "domain_id": subscription.domain_id,
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date
    }

@router.get("/api/subscriptions/me")
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students have subscriptions")

    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )

    subscription = result.scalars().first()

    if not subscription:
        return {
            "has_subscription": False,
            "status": None
        }

    now = datetime.utcnow()

    if subscription.end_date < now and subscription.status in ["trial", "active"]:
        subscription.status = "expired"
        await db.commit()

    domain_result = await db.execute(
        select(Domain).where(Domain.id == subscription.domain_id)
    )
    domain = domain_result.scalar_one_or_none()

    plan = None
    if subscription.plan_id:
        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

    return {
        "has_subscription": True,
        "subscription_id": subscription.id,
        "domain_id": subscription.domain_id,
        "domain_name": domain.name if domain else None,
        "plan_id": subscription.plan_id,
        "plan_name": plan.name if plan else "Trial",
        "status": subscription.status,
        "payment_status": subscription.payment_status,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "is_active": subscription.status in ["trial", "active"] and subscription.end_date >= now
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.V1.users import get_current_user
from app.models.user import User
from app.models.job import Job, SavedJob, JobApplication
from app.schemas.job import JobCreate

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("/")
async def create_job(
    data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["admin", "alumni"]:
        raise HTTPException(status_code=403, detail="Only admin or alumni can post jobs")

    job = Job(
        title=data.title,
        company=data.company,
        location=data.location,
        job_type=data.job_type,
        salary_or_stipend=data.salary_or_stipend,
        deadline=data.deadline,
        description=data.description,
        tags=data.tags,
        created_by=current_user.id
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return {
        "message": "Job created successfully",
        "job_id": job.id
    }

@router.get("/")
async def get_jobs(
    search: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Job)

    if search:
        query = query.where(
            or_(
                Job.title.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
                Job.location.ilike(f"%{search}%"),
                Job.tags.ilike(f"%{search}%")
            )
        )

    if job_type:
        query = query.where(Job.job_type == job_type)

    query = query.order_by(Job.created_at.desc())

    result = await db.execute(query)
    jobs = result.scalars().all()

    output = []

    for job in jobs:
        saved_result = await db.execute(
            select(SavedJob).where(
                SavedJob.job_id == job.id,
                SavedJob.user_id == current_user.id
            )
        )

        applied_result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == job.id,
                JobApplication.user_id == current_user.id
            )
        )

        output.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "salary_or_stipend": job.salary_or_stipend,
            "deadline": job.deadline,
            "description": job.description,
            "tags": job.tags,
            "created_by": job.created_by,
            "created_at": job.created_at,
            "is_saved": saved_result.scalar_one_or_none() is not None,
            "is_applied": applied_result.scalar_one_or_none() is not None
        })

    return output

@router.get("/saved")
async def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedJob).where(SavedJob.user_id == current_user.id)
    )

    saved_jobs = result.scalars().all()

    output = []

    for saved in saved_jobs:
        job_result = await db.execute(select(Job).where(Job.id == saved.job_id))
        job = job_result.scalar_one_or_none()

        if job:
            output.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_type": job.job_type,
                "salary_or_stipend": job.salary_or_stipend,
                "deadline": job.deadline,
                "saved_at": saved.saved_at
            })

    return output

@router.get("/applied")
async def get_applied_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(JobApplication).where(JobApplication.user_id == current_user.id)
    )

    applications = result.scalars().all()

    output = []

    for application in applications:
        job_result = await db.execute(select(Job).where(Job.id == application.job_id))
        job = job_result.scalar_one_or_none()

        if job:
            output.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_type": job.job_type,
                "salary_or_stipend": job.salary_or_stipend,
                "deadline": job.deadline,
                "application_status": application.status,
                "applied_at": application.applied_at
            })

    return output

@router.get("/{job_id}")
async def get_job_detail(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    saved_result = await db.execute(
        select(SavedJob).where(
            SavedJob.job_id == job.id,
            SavedJob.user_id == current_user.id
        )
    )

    applied_result = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == job.id,
            JobApplication.user_id == current_user.id
        )
    )

    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "job_type": job.job_type,
        "salary_or_stipend": job.salary_or_stipend,
        "deadline": job.deadline,
        "description": job.description,
        "tags": job.tags,
        "created_by": job.created_by,
        "created_at": job.created_at,
        "is_saved": saved_result.scalar_one_or_none() is not None,
        "is_applied": applied_result.scalar_one_or_none() is not None
    }

@router.post("/{job_id}/save")
async def save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_result = await db.execute(
        select(SavedJob).where(
            SavedJob.job_id == job_id,
            SavedJob.user_id == current_user.id
        )
    )

    if existing_result.scalar_one_or_none():
        return {"message": "Job already saved"}

    saved_job = SavedJob(
        job_id=job_id,
        user_id=current_user.id
    )

    db.add(saved_job)
    await db.commit()

    return {"message": "Job saved successfully"}

@router.delete("/{job_id}/save")
async def unsave_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedJob).where(
            SavedJob.job_id == job_id,
            SavedJob.user_id == current_user.id
        )
    )

    saved_job = result.scalar_one_or_none()

    if not saved_job:
        raise HTTPException(status_code=404, detail="Saved job not found")

    await db.delete(saved_job)
    await db.commit()

    return {"message": "Job removed from saved jobs"}

@router.post("/{job_id}/apply")
async def apply_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can apply for jobs")

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_result = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.user_id == current_user.id
        )
    )

    if existing_result.scalar_one_or_none():
        return {"message": "Already applied"}

    application = JobApplication(
        job_id=job_id,
        user_id=current_user.id,
        status="applied"
    )

    db.add(application)
    await db.commit()

    return {"message": "Job applied successfully"}

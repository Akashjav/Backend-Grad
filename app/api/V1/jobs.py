from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select, or_

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.job import Job, SavedJob, JobApplication

from app.schemas.job import JobCreate

from app.services import jobs_service

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post('/')
async def create_job(data: JobCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.create_job(data, current_user, db)

@router.get('/')
async def get_jobs(search: str | None=Query(default=None), job_type: str | None=Query(default=None), current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.get_jobs(search, job_type, current_user, db)

@router.get('/saved')
async def get_saved_jobs(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.get_saved_jobs(current_user, db)

@router.get('/applied')
async def get_applied_jobs(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.get_applied_jobs(current_user, db)

@router.get('/{job_id}')
async def get_job_detail(job_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.get_job_detail(job_id, current_user, db)

@router.post('/{job_id}/save')
async def save_job(job_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.save_job(job_id, current_user, db)

@router.delete('/{job_id}/save')
async def unsave_job(job_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.unsave_job(job_id, current_user, db)

@router.post('/{job_id}/apply')
async def apply_job(job_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await jobs_service.apply_job(job_id, current_user, db)

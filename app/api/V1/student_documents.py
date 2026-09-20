import os

import shutil

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.student_document import StudentDocument

from app.models.student import StudentProfile

from app.services import student_documents_service

router = APIRouter(prefix="/api/student/documents", tags=["Student Documents"])

UPLOAD_DIR = "uploads/student_documents"

@router.post('/')
async def upload_student_document(document_type: str=Form(...), file: UploadFile=File(...), current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await student_documents_service.upload_student_document(document_type, file, current_user, db)

@router.get('/')
async def get_my_documents(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await student_documents_service.get_my_documents(current_user, db)

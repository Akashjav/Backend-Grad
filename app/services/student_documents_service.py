import os
import shutil
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.student_document import StudentDocument
from app.models.student import StudentProfile

UPLOAD_DIR = os.getenv("STUDENT_DOCUMENT_STORAGE_PATH", "uploads/student_documents")

async def upload_student_document(document_type: str, file: UploadFile, current_user: User, db: AsyncSession):
    if current_user.role != 'student':
        raise HTTPException(status_code=403, detail='Only students can upload documents')
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student_profile = student_result.scalar_one_or_none()
    if not student_profile:
        raise HTTPException(status_code=404, detail='Student profile not found')
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    original_filename = file.filename or ''
    file_ext = os.path.splitext(original_filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail='Only JPG, PNG, and PDF files are allowed')
    if document_type not in {'College ID', 'Bonafide Certificate', 'Student Proof', 'Resume', 'college_id', 'bonafide', 'student_proof', 'resume'}:
        raise HTTPException(422, 'Unsupported document type')
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, 'Maximum document size is 5 MiB')
    signatures = {'.pdf': b'%PDF-', '.png': b'\x89PNG\r\n\x1a\n', '.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff'}
    if not content.startswith(signatures[file_ext]):
        raise HTTPException(415, 'File contents do not match the extension')
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_filename = uuid4().hex + file_ext
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, 'wb') as buffer:
        buffer.write(content)
    document = StudentDocument(user_id=current_user.id, document_type=document_type, file_url=file_path, verification_status='pending')
    student_profile.verification_status = 'pending'
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return {'message': 'Document uploaded successfully', 'document_id': document.id, 'document_type': document.document_type, 'file_url': document.file_url, 'verification_status': document.verification_status}

async def get_my_documents(current_user: User, db: AsyncSession):
    if current_user.role != 'student':
        raise HTTPException(status_code=403, detail='Only students can view student documents')
    result = await db.execute(select(StudentDocument).where(StudentDocument.user_id == current_user.id).order_by(StudentDocument.uploaded_at.desc()))
    documents = result.scalars().all()
    return [{'id': doc.id, 'document_type': doc.document_type, 'file_url': doc.file_url, 'verification_status': doc.verification_status, 'uploaded_at': doc.uploaded_at, 'verified_at': doc.verified_at} for doc in documents]

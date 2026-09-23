from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.parser import extract_text_from_pdf
from app.models.resume import resume_document
from app.core.db import get_database
from bson import ObjectId

router = APIRouter(prefix="/resume", tags=["resume"])

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    text = await extract_text_from_pdf(file)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
    
    db = get_database()
    doc = resume_document(
        user_id="anonymous",  # we'll wire up real auth later
        filename=file.filename,
        raw_text=text
    )
    result = db.resumes.insert_one(doc)
    
    return {
        "resume_id": str(result.inserted_id),
        "filename": file.filename,
        "preview": text[:300]  # first 300 chars so you can verify extraction worked
    }

@router.get("/{resume_id}")
def get_resume(resume_id: str):
    db = get_database()
    resume = db.resumes.find_one({"_id": ObjectId(resume_id)})
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {
        "resume_id": str(resume["_id"]),
        "filename": resume["filename"],
        "raw_text": resume["raw_text"],
        "created_at": resume["created_at"]
    }
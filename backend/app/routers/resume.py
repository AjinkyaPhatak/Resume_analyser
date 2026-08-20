"""Resume API routes."""

from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile) -> None:
    # TODO: Parse and persist an uploaded resume.
    pass


@router.get("/{resume_id}")
async def get_resume(resume_id: str) -> None:
    # TODO: Retrieve a resume by its identifier.
    pass

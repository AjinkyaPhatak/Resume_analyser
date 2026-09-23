from datetime import datetime

def resume_document(user_id: str, filename: str, raw_text: str) -> dict:
    return {
        "user_id": user_id,
        "filename": filename,
        "raw_text": raw_text,
        "created_at": datetime.utcnow()
    }
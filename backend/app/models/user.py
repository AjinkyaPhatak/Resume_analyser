from datetime import datetime

def user_document(name: str, email: str, hashed_password: str) -> dict:
    return {
        "name": name,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
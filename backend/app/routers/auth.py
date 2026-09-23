from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import user_document
from app.core.db import get_database
from app.core.security import hash_password, verify_password, create_access_token
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    db = get_database()
    
    # check if email already exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(user.password)
    doc = user_document(user.name, user.email, hashed)
    result = db.users.insert_one(doc)
    
    return UserResponse(
        id=str(result.inserted_id),
        name=user.name,
        email=user.email
    )

@router.post("/login")
def login(credentials: UserLogin):
    db = get_database()
    
    user = db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    
    return {"access_token": token, "token_type": "bearer"}
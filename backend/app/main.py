from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from .db import Base, engine
from . import models, auth

# ----------------------------
# CREATE DATABASE TABLES
# ----------------------------
Base.metadata.create_all(bind=engine)

# ----------------------------
# FASTAPI INITIALIZATION
# ----------------------------
app = FastAPI(title="AI Fraud Detection Backend")

# ----------------------------
# REQUEST MODELS
# ----------------------------
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ----------------------------
# ROUTES
# ----------------------------
@app.post("/auth/signup")
def signup(request: SignupRequest, db: Session = Depends(auth.get_db)):
    """Register a new user."""
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = auth.get_password_hash(request.password)
    new_user = models.User(email=request.email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(auth.get_db)):
    """Authenticate a user and return an access token."""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/")
def root():
    """Root endpoint to verify the backend is live."""
    return {"message": "AI Fraud Detection Backend Running 🚀 with Auth enabled!"}

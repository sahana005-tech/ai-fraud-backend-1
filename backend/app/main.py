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
import random
from datetime import datetime

# ----------------------------
# DUMMY BANK ACCOUNT LINKING
# ----------------------------
@app.post("/bank/link")
def link_dummy_account(db: Session = Depends(auth.get_db)):
    """Simulate linking a dummy bank account."""
    dummy_account = models.Account(
        account_name="Axis Bank Primary Account",
        account_number="AXISXXXX8765",
        bank_name="Axis Bank"
    )
    db.add(dummy_account)
    db.commit()
    db.refresh(dummy_account)
    return {"message": "Dummy bank account linked successfully", "account_id": dummy_account.id}


# ----------------------------
# GENERATE DUMMY TRANSACTIONS
# ----------------------------
@app.post("/transactions/generate")
def generate_dummy_transactions(db: Session = Depends(auth.get_db)):
    """Generate 10 random dummy transactions with risk scoring."""
    merchants = ["Amazon", "Flipkart", "Swiggy", "Uber", "Zomato", "Myntra", "BigBasket", "IRCTC", "Paytm", "Ola"]
    new_txns = []

    # Get the first account
    account = db.query(models.Account).first()
    if not account:
        raise HTTPException(status_code=400, detail="No linked account found. Link one using /bank/link first.")

    for i in range(10):
        amount = round(random.uniform(100, 15000), 2)
        risk_score = round(random.uniform(10, 100), 2)
        risk_label = (
            "High Risk 🚨" if risk_score > 90 else
            "Suspicious ⚠️" if risk_score > 70 else
            "Safe ✅"
        )
        blocked = risk_score > 90
        verification_required = 70 < risk_score <= 90

        txn = models.Transaction(
            account_id=account.id,
            txn_id=f"TXN{i+1}{random.randint(1000,9999)}",
            amount=amount,
            merchant=random.choice(merchants),
            timestamp=datetime.utcnow(),
            risk_score=risk_score,
            risk_label=risk_label,
            blocked=blocked,
            verification_required=verification_required,
            verification_status="pending" if verification_required else "none",
            reasons="['Unusual amount', 'Merchant mismatch']" if risk_score > 80 else "[]"
        )

        db.add(txn)
        db.commit()
        db.refresh(txn)
        new_txns.append({
            "txn_id": txn.txn_id,
            "amount": txn.amount,
            "merchant": txn.merchant,
            "risk_score": txn.risk_score,
            "risk_label": txn.risk_label,
            "blocked": txn.blocked,
            "verification_required": txn.verification_required
        })

    return {"message": "Dummy transactions generated successfully", "transactions": new_txns}

def root():
    """Root endpoint to verify the backend is live."""
    return {"message": "AI Fraud Detection Backend Running 🚀 with Auth enabled!"}

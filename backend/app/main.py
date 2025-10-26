from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel
from .db import Base, engine
from . import models, auth
import random

# ----------------------------
# DATABASE INITIALIZATION
# ----------------------------
Base.metadata.create_all(bind=engine)

# ----------------------------
# APP INITIALIZATION
# ----------------------------
app = FastAPI(title="AI Fraud Detection Backend")

# ----------------------------
# ENABLE CORS (Frontend Access)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (Lovable will connect)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# AUTH ROUTES
# ----------------------------
@app.post("/auth/signup")
def signup(request: SignupRequest, db: Session = Depends(auth.get_db)):
    """Register a new user"""
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
    """Authenticate a user and return access token"""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

# ----------------------------
# ROOT ENDPOINT
# ----------------------------
@app.get("/")
def root():
    """Test endpoint"""
    return {"message": "AI Fraud Detection Backend Running 🚀 with Auth enabled!"}

# ----------------------------
# DUMMY BANK LINKING
# ----------------------------
@app.post("/bank/link")
def link_dummy_account(db: Session = Depends(auth.get_db)):
    """Simulate linking a dummy bank account"""
    existing_account = db.query(models.Account).first()
    if existing_account:
        return {"message": "Dummy account already linked", "account_id": existing_account.id}

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
    """Generate 10 random dummy transactions with risk scores"""
    merchants = ["Amazon", "Flipkart", "Swiggy", "Uber", "Zomato", "Myntra", "BigBasket", "IRCTC", "Paytm", "Ola"]
    new_txns = []

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

# ----------------------------
# GET ALL TRANSACTIONS
# ----------------------------
@app.get("/transactions")
def get_all_transactions(db: Session = Depends(auth.get_db)):
    """Retrieve all transactions from database"""
    transactions = db.query(models.Transaction).all()
    return [
        {
            "txn_id": t.txn_id,
            "merchant": t.merchant,
            "amount": t.amount,
            "risk_score": t.risk_score,
            "risk_label": t.risk_label,
            "blocked": t.blocked,
            "verification_required": t.verification_required,
            "timestamp": t.timestamp
        }
        for t in transactions
    ]

# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import random
import logging

from .db import Base, engine, SessionLocal
from . import models, auth

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-fraud-backend")

# ----------------------------
# Create DB tables
# ----------------------------
Base.metadata.create_all(bind=engine)

# ----------------------------
# App init + CORS
# ----------------------------
app = FastAPI(title="AI Fraud Detection Backend - Stable")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development allow all; later restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# DB dependency
# ----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# Request models
# ----------------------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Response small models
class SimpleMessage(BaseModel):
    message: str

# ----------------------------
# Utility: safe commit wrapper
# ----------------------------
def safe_commit(db: Session):
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB commit failed: %s", e)
        raise

# ----------------------------
# Health / root
# ----------------------------
@app.get("/", response_model=dict)
def root():
    return {"message": "AI Fraud Detection Backend Running 🚀 with Auth enabled!"}

# ----------------------------
# AUTH: Signup
# ----------------------------
@app.post("/auth/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(models.User).filter(models.User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = auth.get_password_hash(request.password)
    user = models.User(email=request.email, password_hash=hashed)
    db.add(user)
    safe_commit(db)
    db.refresh(user)
    logger.info("New user created: %s", user.email)
    return {"message": "User created successfully", "user_id": user.id}

# ----------------------------
# AUTH: Login
# ----------------------------
@app.post("/auth/login", response_model=dict)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": user.email}, timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES))
    logger.info("User logged in: %s", user.email)
    return {"access_token": token, "token_type": "bearer"}

# ----------------------------
# Link dummy bank account (idempotent)
# ----------------------------
@app.post("/bank/link", response_model=dict)
def link_dummy_account(db: Session = Depends(get_db)):
    # If an account already exists, return it instead of creating duplicates
    existing = db.query(models.Account).first()
    if existing:
        return {"message": "Dummy account already linked", "account_id": existing.id}

    account = models.Account(
        account_name="Axis Bank Primary Account",
        account_number="AXISXXXX8765",
        bank_name="Axis Bank"
    )
    db.add(account)
    safe_commit(db)
    db.refresh(account)
    logger.info("Dummy account linked: %s", account.account_number)
    return {"message": "Dummy bank account linked successfully", "account_id": account.id}

# ----------------------------
# Generate dummy transactions
# ----------------------------
@app.post("/transactions/generate", response_model=dict)
def generate_dummy_transactions(count: int = 10, db: Session = Depends(get_db)):
    """
    Generate `count` dummy transactions (default 10).
    Returns list of created transactions with risk attributes.
    """
    merchants = ["Amazon", "Flipkart", "Swiggy", "Uber", "Zomato", "Myntra", "BigBasket", "IRCTC", "Paytm", "Ola"]
    created = []

    account = db.query(models.Account).first()
    if not account:
        raise HTTPException(status_code=400, detail="No linked account found. Link one using /bank/link first.")

    # For simple baseline behavior: compute average historical amount (if exists)
    past = db.query(models.Transaction).filter(models.Transaction.account_id == account.id).all()
    avg_amount = (sum(p.amount for p in past) / len(past)) if past else 200.0

    for i in range(count):
        amount = round(random.uniform(20, 20000), 2)
        # Risk heuristic (simple, explainable):
        # - Very large amounts relative to avg are risky
        # - Night time (simulated) adds risk
        # - Random jitter to keep variety
        base_risk = min(95.0, max(5.0, (amount / max(1.0, avg_amount)) * 20 + random.uniform(-10, 10)))
        # small probability event for geo/device anomalies simulated:
        anomaly = random.random()
        if anomaly < 0.05:
            base_risk += 20  # rare anomaly
        risk_score = round(min(100.0, base_risk), 2)

        risk_label = "Safe" if risk_score < 70 else "Suspicious" if risk_score <= 90 else "High Risk"
        blocked = risk_score > 90
        verification_required = 70 < risk_score <= 90

        txn = models.Transaction(
            account_id=account.id,
            txn_id=f"TXN{int(datetime.utcnow().timestamp())}{random.randint(100,999)}",
            amount=amount,
            merchant=random.choice(merchants),
            timestamp=datetime.utcnow(),
            risk_score=risk_score,
            risk_label=risk_label,
            blocked=blocked,
            verification_required=verification_required,
            verification_status="pending" if verification_required else "none",
            reasons="['Large amount', 'Unusual merchant']" if risk_score > 75 else "[]"
        )

        db.add(txn)
        safe_commit(db)
        db.refresh(txn)

        created.append({
            "txn_id": txn.txn_id,
            "amount": txn.amount,
            "merchant": txn.merchant,
            "timestamp": txn.timestamp.isoformat(),
            "risk_score": txn.risk_score,
            "risk_label": txn.risk_label,
            "blocked": txn.blocked,
            "verification_required": txn.verification_required
        })

    logger.info("Generated %d transactions for account %s", len(created), account.account_number)
    return {"message": "Dummy transactions generated successfully", "transactions": created}

# ----------------------------
# Get all transactions
# ----------------------------
@app.get("/transactions", response_model=List[dict])
def get_all_transactions(db: Session = Depends(get_db)):
    txns = db.query(models.Transaction).order_by(models.Transaction.timestamp.desc()).all()
    out = []
    for t in txns:
        out.append({
            "txn_id": t.txn_id,
            "amount": t.amount,
            "merchant": t.merchant,
            "timestamp": t.timestamp.isoformat(),
            "risk_score": t.risk_score,
            "risk_label": t.risk_label,
            "blocked": t.blocked,
            "verification_required": t.verification_required,
            "verification_status": t.verification_status,
            "reasons": t.reasons
        })
    return out

# ----------------------------
# Optional: get transaction by id
# ----------------------------
@app.get("/transactions/{txn_id}", response_model=dict)
def get_transaction(txn_id: str, db: Session = Depends(get_db)):
    t = db.query(models.Transaction).filter(models.Transaction.txn_id == txn_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "txn_id": t.txn_id,
        "amount": t.amount,
        "merchant": t.merchant,
        "timestamp": t.timestamp.isoformat(),
        "risk_score": t.risk_score,
        "risk_label": t.risk_label,
        "blocked": t.blocked,
        "verification_required": t.verification_required,
        "verification_status": t.verification_status,
        "reasons": t.reasons
    }


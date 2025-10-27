from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from jose import jwt
from datetime import datetime, timedelta
import random

# --- SIMPLE IN-MEMORY DATABASE (TEMPORARY) ---
USERS = {}
TRANSACTIONS = []
DUMMY_ACCOUNT = None

# --- CONFIG ---
SECRET_KEY = "secret-key-demo"
ALGORITHM = "HS256"

app = FastAPI(title="AI Fraud Detection Backend")

# --- CORS for Lovable / Base44 / Frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Transaction(BaseModel):
    txn_id: str
    amount: float
    merchant: str
    risk_score: float
    risk_label: str
    blocked: bool

# --- AUTH HELPERS ---
def create_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=3)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- ROUTES ---

@app.get("/")
def root():
    return {"message": "AI Fraud Detection Backend Running 🚀 with Auth enabled!"}

# 1️⃣ SIGNUP
@app.post("/auth/signup")
def signup(req: SignupRequest):
    if req.email in USERS:
        raise HTTPException(status_code=400, detail="Email already registered")
    USERS[req.email] = req.password
    return {"message": "User created successfully", "user_id": len(USERS)}

# 2️⃣ LOGIN
@app.post("/auth/login")
def login(req: LoginRequest):
    if req.email not in USERS or USERS[req.email] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(req.email)
    return {"access_token": token, "token_type": "bearer"}

# 3️⃣ LINK DUMMY BANK ACCOUNT
@app.post("/bank/link")
def link_bank():
    global DUMMY_ACCOUNT
    DUMMY_ACCOUNT = {
        "account_id": "DUMMY-12345",
        "balance": 10000.0,
        "linked": True
    }
    return {"message": "Dummy bank account linked successfully", "account_id": DUMMY_ACCOUNT["account_id"]}

# 4️⃣ GENERATE DUMMY TRANSACTIONS
@app.post("/transactions/generate")
def generate_transactions():
    global TRANSACTIONS
    if not DUMMY_ACCOUNT:
        raise HTTPException(status_code=400, detail="No bank account linked")
    merchants = ["Amazon", "Starbucks", "Flipkart", "Zara", "Apple Store"]
    TRANSACTIONS = []
    for i in range(10):
        amount = round(random.uniform(10, 5000), 2)
        risk = round(random.uniform(0, 100), 2)
        label = "Safe"
        blocked = False
        if risk > 90:
            label = "High Risk"
            blocked = True
        elif risk > 60:
            label = "Suspicious"
        txn = {
            "txn_id": f"TXN{i+1:05d}",
            "amount": amount,
            "merchant": random.choice(merchants),
            "risk_score": risk,
            "risk_label": label,
            "blocked": blocked
        }
        TRANSACTIONS.append(txn)
    return {"message": "Dummy transactions generated successfully", "transactions": TRANSACTIONS}

# 5️⃣ FETCH ALL TRANSACTIONS
@app.get("/transactions", response_model=List[Transaction])
def get_transactions():
    if not TRANSACTIONS:
        raise HTTPException(status_code=404, detail="No transactions found")
    return TRANSACTIONS



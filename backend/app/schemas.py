from pydantic import BaseModel
from datetime import datetime

# ----------------------------
# USER SCHEMAS
# ----------------------------
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        orm_mode = True


# ----------------------------
# ACCOUNT SCHEMAS
# ----------------------------
class AccountBase(BaseModel):
    account_name: str
    account_number: str
    bank_name: str

class AccountResponse(AccountBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ----------------------------
# TRANSACTION SCHEMAS
# ----------------------------
class TransactionBase(BaseModel):
    txn_id: str
    amount: float
    merchant: str
    timestamp: datetime
    risk_score: float
    risk_label: str
    blocked: bool
    verification_required: bool
    verification_status: str
    reasons: str

class TransactionResponse(TransactionBase):
    id: int

    class Config:
        orm_mode = True

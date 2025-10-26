from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    accounts = relationship("LinkedAccount", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String)
    account_number = Column(String, unique=True)
    bank_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class LinkedAccount(Base):
    __tablename__ = "linked_accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    linked_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="accounts")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    txn_id = Column(String, unique=True)
    amount = Column(Float)
    merchant = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    risk_score = Column(Float, default=0)
    risk_label = Column(String)
    blocked = Column(Boolean, default=False)
    verification_required = Column(Boolean, default=False)
    verification_status = Column(String, default="none")
    reasons = Column(Text, default="[]")
    account = relationship("Account")

class TxVerification(Base):
    __tablename__ = "tx_verifications"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    method = Column(String)
    code = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

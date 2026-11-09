import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, Integer, DateTime, Boolean, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=uid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254),unique=True,index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=now)

class SessionToken(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64),primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime,index=True)

class LoginAttempt(Base):
    __tablename__='login_attempts'
    key: Mapped[str]=mapped_column(String(64),primary_key=True)
    count: Mapped[int]=mapped_column(Integer,default=0)
    window_start: Mapped[datetime]=mapped_column(DateTime,default=now)

class Job(Base):
    __tablename__='jobs'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    owner_id: Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True)
    title: Mapped[str]=mapped_column(String(160))
    category: Mapped[str]=mapped_column(String(40))
    emirate: Mapped[str]=mapped_column(String(40))
    description: Mapped[str]=mapped_column(Text,default='')
    status: Mapped[str]=mapped_column(String(30),default='Comparing')
    selected_quote_id: Mapped[str|None]=mapped_column(String(36),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class Document(Base):
    __tablename__='documents'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    job_id: Mapped[str]=mapped_column(ForeignKey('jobs.id',ondelete='CASCADE'),index=True)
    filename: Mapped[str]=mapped_column(String(180))
    storage_key: Mapped[str]=mapped_column(String(60))
    mime: Mapped[str]=mapped_column(String(80))
    sha256: Mapped[str]=mapped_column(String(64))
    size: Mapped[int]=mapped_column(Integer)
    state: Mapped[str]=mapped_column(String(30),default='queued',index=True)
    extracted: Mapped[str]=mapped_column(Text,default='[]')
    error: Mapped[str]=mapped_column(String(300),default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class Quote(Base):
    __tablename__='quotes'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    job_id: Mapped[str]=mapped_column(ForeignKey('jobs.id',ondelete='CASCADE'),index=True)
    document_id: Mapped[str|None]=mapped_column(ForeignKey('documents.id',ondelete='SET NULL'),nullable=True)
    provider: Mapped[str]=mapped_column(String(160))
    reference: Mapped[str]=mapped_column(String(100),default='')
    tax_mode: Mapped[str]=mapped_column(String(20),default='unspecified')
    tax_rate: Mapped[int]=mapped_column(Integer,default=0)  # basis points, entered by the user
    warranty_days: Mapped[int|None]=mapped_column(Integer,nullable=True)
    completion_days: Mapped[int|None]=mapped_column(Integer,nullable=True)
    valid_until: Mapped[str]=mapped_column(String(10),default='')
    exclusions: Mapped[str]=mapped_column(Text,default='')
    notes: Mapped[str]=mapped_column(Text,default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=now)

class LineItem(Base):
    __tablename__='line_items'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    quote_id: Mapped[str]=mapped_column(ForeignKey('quotes.id',ondelete='CASCADE'),index=True)
    label: Mapped[str]=mapped_column(String(200))
    kind: Mapped[str]=mapped_column(String(30))
    pricing: Mapped[str]=mapped_column(String(20))
    amount: Mapped[int|None]=mapped_column(Integer,nullable=True)  # fils, never float
    quantity: Mapped[int]=mapped_column(Integer,default=1)
    reviewed: Mapped[bool]=mapped_column(Boolean,default=False)
    source_page: Mapped[int|None]=mapped_column(Integer,nullable=True)
    source_excerpt: Mapped[str]=mapped_column(Text,default='')

class Expense(Base):
    __tablename__='expenses'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    job_id: Mapped[str]=mapped_column(ForeignKey('jobs.id',ondelete='CASCADE'),index=True)
    label: Mapped[str]=mapped_column(String(180))
    amount: Mapped[int]=mapped_column(Integer)
    paid_on: Mapped[str]=mapped_column(String(10))
    note: Mapped[str]=mapped_column(Text,default='')

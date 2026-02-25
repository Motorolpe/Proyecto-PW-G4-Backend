from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


# ============== User Schemas ==============
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "user"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    email_verified: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== Category Schemas ==============
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: UUID
    created_at: Optional[datetime]


class EgresoType(BaseModel):
    id: str | None = None
    amount : float
    expense_date : str
    description : str | None = None
    is_recurring : bool | None = False
    created_at : str | None = None
    updated_at : str | None = None
    user_id : str
    category_id : str
    class Config:
        from_attributes = True

class UserListSchema(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class BudgetCreate(BaseModel):
    amount_limit: float
    month: str
    year: str
    alert_treshold: float


class BudgetCreate(BudgetBase):
    user_id: UUID
    category_id: UUID


class BudgetUpdate(BaseModel):
    amount_limit: Optional[float] = None
    month: Optional[str] = None
    year: Optional[str] = None
    alert_treshold: Optional[float] = None
    category_id: Optional[UUID] = None


class BudgetResponse(BudgetBase):
    id: UUID
    user_id: UUID
    category_id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== Alert Schemas ==============
class AlertBase(BaseModel):
    alert_type: str
    percentage_reached: float
    amount_spent: float
    message: str


class AlertCreate(AlertBase):
    user_id: UUID
    budget_id: UUID


class AlertResponse(AlertBase):
    id: UUID
    user_id: UUID
    budget_id: UUID
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== Access Log Schemas ==============
class AccessLogBase(BaseModel):
    action_type: str
    status: str


class AccessLogCreate(AccessLogBase):
    user_id: UUID
    timestamp: datetime


class AccessLogResponse(AccessLogBase):
    id: UUID
    user_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True


# ============== Login Schemas ==============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ============== Stats Schemas ==============
class UserStatsSummary(BaseModel):
    total_users: int
    new_users_this_month: int
    users_by_month: dict[str, int]


class ExpenseFilters(BaseModel):
    category_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    category_id: UUID

class EgresoUpdate(BaseModel):
    amount: float
    expense_date: str
    description: str | None = None
    is_recurring: bool | None = False
    category_id: UUID

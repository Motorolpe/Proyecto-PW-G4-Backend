from pydantic import BaseModel
from uuid import UUID

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
    category_id: UUID

class EgresoUpdate(BaseModel):
    amount: float
    expense_date: str
    description: str | None = None
    is_recurring: bool | None = False
    category_name: str
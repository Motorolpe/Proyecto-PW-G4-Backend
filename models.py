import uuid
from database import Base
from sqlalchemy import UUID, Column, String, DateTime, ForeignKey, Table, Boolean, Double
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
        
    )
    role = Column(String, default="user") 
    full_name = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String, unique=True)
    role = Column(String)
    is_active = Column(Boolean)
    email_verified = Column(Boolean)
    verification_token = Column(String, unique=True)
    verification_token_expires = Column(DateTime)
    recovery_token = Column(String, unique=True)
    recovery_token_expires = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    access_logs = relationship("Access_log", back_populates="users") #Sin useList --> Relacion 1:N con Access_log
    alerts = relationship("Alert", back_populates="users") #Sin useList --> Relacion 1:N con Alert
    expenses = relationship("Expense", back_populates="users") #Sin useList --> Relacion 1:N con Expense
    budgets = relationship("Budget", back_populates="users") #Sin useList --> Relacion 1:N con Budget

class Access_log(Base):
    __tablename__ = "access_log"
    id = Column(
        String, 
        primary_key=True,
        index=True
    )
    last_login = Column(DateTime)

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id") #Relacion N:1 con User
        )
    
    users = relationship("User", back_populates="access_logs") 

class Alert(Base):
    __tablename__ = "alert"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    alert_type = Column(String)
    percentage_reached = Column(Double)
    amount_spent = Column(Double)
    message = Column(String)
    created_at = Column(DateTime)

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id"), unique=True #Relacion N:1 con User
        )
    budget_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("budget.id"), unique=True #Relacion N:1 con Budget
        )
    
    users = relationship("User", back_populates="alerts")
    budgets = relationship("Budget", back_populates="alerts")

class Category(Base):
    __tablename__ = "category"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    name = Column(String, unique=True)
    description = Column(String)
    created_at = Column(DateTime)

    expenses = relationship("Expense", back_populates="categories") #Sin useList --> Relacion 1:N con Expense
    budgets = relationship("Budget", back_populates="categories") #Sin useList --> Relacion 1:N con Budget

class Expense(Base):
    __tablename__ = "expense"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    amount = Column(Double)
    expense_date = Column(DateTime)
    description = Column(String)
    is_recurring = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id") #Relacion N:1 con User
        )
    category_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("category.id") #Relacion N:1 con Category
        )
    
    users = relationship("User", back_populates="expenses")
    categories = relationship("Category", back_populates="expenses")

class Budget(Base):
    __tablename__ = "budget"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    amount_limit = Column(Double)
    month = Column(String)
    year = Column(String)
    alert_treshold = Column(Double)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id") #Relacion N:1 con User
        )
    category_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("category.id") #Relacion N:1 con Category
        )
    
    users = relationship("User", back_populates="budgets")
    categories = relationship("Category", back_populates="budgets")
    alerts = relationship("Alert", back_populates="budgets")
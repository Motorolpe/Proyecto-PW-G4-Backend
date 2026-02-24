from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import datetime

from database import get_db
from models import Budget, Access_log
from schemas import BudgetCreate

router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.post("/")
def create_budget(
    budget: BudgetCreate,
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    
    # 🔐 Validar token
    access = db.query(Access_log).filter(
        Access_log.id == token
    ).first()

    if not access:
        raise HTTPException(status_code=401, detail="Token inválido")

    user_id = access.user_id

    # 🚨 Verificar si ya existe presupuesto para ese mes/año/categoría
    existing_budget = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == budget.category_id,
        Budget.month == budget.month,
        Budget.year == budget.year
    ).first()

    if existing_budget:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un presupuesto para esta categoría en ese mes y año"
        )

    # 💾 Crear presupuesto
    new_budget = Budget(
        id=uuid4(),
        amount_limit=budget.amount_limit,
        month=budget.month,
        year=budget.year,
        alert_treshold=budget.alert_treshold,
        created_at=datetime.datetime.now(),
        user_id=user_id,
        category_id=budget.category_id
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return {
        "msg": "Presupuesto creado correctamente",
        "data": new_budget
    }
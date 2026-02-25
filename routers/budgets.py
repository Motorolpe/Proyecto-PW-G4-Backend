from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session

from models import Budget, Access_log
from schemas import BudgetCreate, BudgetResponse, BudgetUpdate
from database import get_db
from security import verify_token

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    skip: int = 0,
    limit: int = 10,
    month: str | None = Query(None),
    year: str | None = Query(None),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Listar presupuestos del usuario actual (token header)"""
    access = db.query(Access_log).filter(Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    query = db.query(Budget).filter(Budget.user_id == user_id)
    if month:
        query = query.filter(Budget.month == month)
    if year:
        query = query.filter(Budget.year == year)

    budgets = query.offset(skip).limit(limit).all()
    return budgets

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


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Obtener presupuesto por ID (token header)"""
    access = db.query(Access_log).filter(Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if budget.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este presupuesto",
        )
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Actualizar presupuesto (token header)"""
    access = db.query(Access_log).filter(Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if budget.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este presupuesto",
        )

    if budget_update.amount_limit is not None:
        budget.amount_limit = budget_update.amount_limit
    if budget_update.month is not None:
        budget.month = budget_update.month
    if budget_update.year is not None:
        budget.year = budget_update.year
    if budget_update.alert_treshold is not None:
        budget.alert_treshold = budget_update.alert_treshold
    if budget_update.category_id is not None:
        budget.category_id = budget_update.category_id

    budget.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Eliminar presupuesto (token header)"""
    access = db.query(Access_log).filter(Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if budget.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este presupuesto",
        )

    db.delete(budget)
    db.commit()
    return None


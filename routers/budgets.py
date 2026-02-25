from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import verify_token

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=list[schemas.BudgetResponse])
async def list_budgets(
    skip: int = 0,
    limit: int = 10,
    month: str | None = Query(None),
    year: str | None = Query(None),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Listar presupuestos del usuario actual (token header)"""
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    query = db.query(models.Budget).filter(models.Budget.user_id == user_id)
    if month:
        query = query.filter(models.Budget.month == month)
    if year:
        query = query.filter(models.Budget.year == year)

    budgets = query.offset(skip).limit(limit).all()
    return budgets


@router.post("", response_model=schemas.BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Crear nuevo presupuesto (token header)"""
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    if budget.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear presupuestos para otros usuarios",
        )

    category = db.query(models.Category).filter(models.Category.id == budget.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    new_budget = models.Budget(
        amount_limit=budget.amount_limit,
        month=budget.month,
        year=budget.year,
        alert_treshold=budget.alert_treshold,
        user_id=user_id,
        category_id=budget.category_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


@router.get("/{budget_id}", response_model=schemas.BudgetResponse)
async def get_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Obtener presupuesto por ID (token header)"""
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if budget.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este presupuesto",
        )
    return budget


@router.put("/{budget_id}", response_model=schemas.BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_update: schemas.BudgetUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Actualizar presupuesto (token header)"""
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
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
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = access.user_id

    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
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

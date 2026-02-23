from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[schemas.BudgetResponse])
async def list_budgets(
    current_user: models.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    month: str | None = Query(None),
    year: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Listar presupuestos del usuario actual"""
    query = db.query(models.Budget).filter(models.Budget.user_id == current_user.id)
    if month:
        query = query.filter(models.Budget.month == month)
    if year:
        query = query.filter(models.Budget.year == year)

    budgets = query.offset(skip).limit(limit).all()
    return budgets


@router.post("", response_model=schemas.BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget: schemas.BudgetCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear nuevo presupuesto"""
    if budget.user_id != current_user.id:
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
        user_id=budget.user_id,
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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener presupuesto por ID"""
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    if budget.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este presupuesto",
        )

    return budget


@router.put("/{budget_id}", response_model=schemas.BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_update: schemas.BudgetUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar presupuesto"""
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    if budget.user_id != current_user.id:
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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar presupuesto"""
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    if budget.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este presupuesto",
        )

    db.delete(budget)
    db.commit()
    return None

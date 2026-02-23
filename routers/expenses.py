from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[schemas.ExpenseResponse])
async def list_expenses(
    current_user: models.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    category_id: UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    amount_min: float | None = Query(None),
    amount_max: float | None = Query(None),
    db: Session = Depends(get_db),
):
    """Listar gastos del usuario actual con filtros opcionales"""
    query = db.query(models.Expense).filter(models.Expense.user_id == current_user.id)

    if category_id:
        query = query.filter(models.Expense.category_id == category_id)
    if date_from:
        query = query.filter(models.Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(models.Expense.expense_date <= date_to)
    if amount_min is not None:
        query = query.filter(models.Expense.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(models.Expense.amount <= amount_max)

    expenses = query.order_by(models.Expense.expense_date.desc()).offset(skip).limit(limit).all()
    return expenses


@router.post("", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: schemas.ExpenseCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear nuevo gasto"""
    if expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear gastos para otros usuarios",
        )

    category = db.query(models.Category).filter(models.Category.id == expense.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    new_expense = models.Expense(
        amount=expense.amount,
        description=expense.description,
        is_recurring=expense.is_recurring,
        user_id=expense.user_id,
        category_id=expense.category_id,
        expense_date=expense.expense_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@router.get("/{expense_id}", response_model=schemas.ExpenseResponse)
async def get_expense(
    expense_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener gasto por ID"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    if expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este gasto",
        )

    return expense


@router.put("/{expense_id}", response_model=schemas.ExpenseResponse)
async def update_expense(
    expense_id: UUID,
    expense_update: schemas.ExpenseUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar gasto"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    if expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este gasto",
        )

    if expense_update.amount is not None:
        expense.amount = expense_update.amount
    if expense_update.description is not None:
        expense.description = expense_update.description
    if expense_update.is_recurring is not None:
        expense.is_recurring = expense_update.is_recurring
    if expense_update.category_id is not None:
        expense.category_id = expense_update.category_id

    expense.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar gasto"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    if expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este gasto",
        )

    db.delete(expense)
    db.commit()
    return None

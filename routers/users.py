from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user),
):
    """Obtener información del usuario actual"""
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar información del usuario actual"""
    try:
        if user_update.full_name:
            current_user.full_name = user_update.full_name
        if user_update.email:
            current_user.email = user_update.email
        if user_update.role:
            current_user.role = user_update.role

        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}",
        )


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Obtener usuario por ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get("", response_model=list[schemas.UserResponse])
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Listar todos los usuarios"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@router.get("/stats/summary", response_model=schemas.UserStatsSummary)
async def users_stats(db: Session = Depends(get_db)):
    """Estadísticas básicas de usuarios"""
    total_users = db.query(func.count(models.User.id)).scalar() or 0

    now = datetime.utcnow()
    new_users_this_month = (
        db.query(func.count(models.User.id))
        .filter(func.extract("year", models.User.created_at) == now.year)
        .filter(func.extract("month", models.User.created_at) == now.month)
        .scalar()
        or 0
    )

    users_by_month_rows = (
        db.query(
            func.extract("year", models.User.created_at).label("year"),
            func.extract("month", models.User.created_at).label("month"),
            func.count(models.User.id).label("count"),
        )
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    users_by_month = {
        f"{int(row.year):04d}-{int(row.month):02d}": int(row.count)
        for row in users_by_month_rows
        if row.year is not None and row.month is not None
    }

    return schemas.UserStatsSummary(
        total_users=int(total_users),
        new_users_this_month=int(new_users_this_month),
        users_by_month=users_by_month,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar usuario (solo el dueño)"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este usuario",
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuario: {str(e)}",
        )

    return None

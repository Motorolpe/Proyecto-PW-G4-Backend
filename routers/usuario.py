from datetime import datetime, timedelta
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import verify_token
from models import User

# Sin prefix: main.py lo registra con /usuarios y /users
router = APIRouter()


def _current_user(token: str, db: Session) -> models.User:
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.query(models.User).filter(models.User.id == access.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.post("/solicitar-recuperacion")
async def solicitar_recuperacion(email: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    token = str(uuid.uuid4())

    usuario.recovery_token = token
    usuario.recovery_token_expires = datetime.utcnow() + timedelta(minutes=15)

    db.commit()

    return {
        "msg": "Token de recuperación generado",
        "recovery_token": token 
    }

@router.put("/cambiar-password")
async def cambiar_password(email: str, token: str, nueva_password: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.recovery_token != token:
        raise HTTPException(status_code=400, detail="Token inválido")

    if usuario.recovery_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")

    usuario.password_hash = nueva_password

    usuario.recovery_token = None
    usuario.recovery_token_expires = None

    usuario.updated_at = datetime.utcnow()
    db.commit()

    return {
        "msg": "Contraseña actualizada correctamente"
    }


@router.get("/me", response_model=schemas.UserResponse)
async def obtener_usuario_actual(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    return _current_user(token, db)


@router.put("/me", response_model=schemas.UserResponse)
async def actualizar_usuario_actual(
    user_update: schemas.UserUpdate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user = _current_user(token, db)
    try:
        if user_update.full_name:
            user.full_name = user_update.full_name
        if user_update.email:
            user.email = user_update.email
        if user_update.role:
            user.role = user_update.role

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}",
        )


@router.get("/stats/summary", response_model=schemas.UserStatsSummary)
async def usuarios_stats(db: Session = Depends(get_db), token: str = Depends(verify_token)):
    _current_user(token, db)
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


@router.get("", response_model=list[schemas.UserResponse])
async def listar_usuarios(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    _current_user(token, db)
    return db.query(models.User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def obtener_usuario(user_id: UUID, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    _current_user(token, db)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    user_id: UUID,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user = _current_user(token, db)
    if user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este usuario",
        )

    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        db.delete(target)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuario: {str(e)}",
        )

    return None
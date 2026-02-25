from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel
import string
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import UUID, func
from sqlalchemy.orm import Session

from models import User
import schemas
from database import get_db
from security import verify_token
from enviarCorreo.email import enviar_correo_recuperacion, enviar_correo_contraseña

from schemas import UserListSchema
from typing import List

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

class RecuperacionCuenta(BaseModel):
    email: str

@router.post("/solicitar-recuperacion")
async def solicitar_recuperacion(request: RecuperacionCuenta, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == request.email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    token = str(uuid.uuid4())
    enviar_correo_recuperacion(usuario.email, token)

    usuario.recovery_token = token
    usuario.recovery_token_expires = datetime.utcnow() + timedelta(minutes=15)

    db.commit()

    return {
        "msg": "Token de recuperación generado",
        "recovery_token": token 
    }

class CambiarPasswordRequest(BaseModel):
    token: str
    nueva_password: str

class CambiarPasswordAutorizadoRequest(BaseModel):
    email: str
    old_password: str
    new_password: str

@router.put("/cambiar-password")
async def cambiar_password(data: CambiarPasswordRequest, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.recovery_token == data.token).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Token inválido")

    if usuario.recovery_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Tiempo expirado")

    usuario.password_hash = data.nueva_password

    usuario.recovery_token = None
    usuario.recovery_token_expires = None

    usuario.updated_at = datetime.utcnow()
    db.commit()

    return {
        "msg": "Contraseña actualizada correctamente"
    }


@router.get("/me", response_model=schemas.UserResponse)
async def obtener_usuario_actual(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    return


@router.put("/me", response_model=schemas.UserResponse)
async def actualizar_usuario_actual(
    user_update: schemas.UserUpdate,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user =
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

    total_users = db.query(func.count(User.id)).scalar() or 0

    now = datetime.utcnow()
    new_users_this_month = (
        db.query(func.count(User.id))
        .filter(func.extract("year", User.created_at) == now.year)
        .filter(func.extract("month", User.created_at) == now.month)
        .scalar()
        or 0
    )

    users_by_month_rows = (
        db.query(
            func.extract("year", User.created_at).label("year"),
            func.extract("month", User.created_at).label("month"),
            func.count(User.id).label("count"),
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

    return db.query(User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def obtener_usuario(user_id: UUID, db: Session = Depends(get_db), token: str = Depends(verify_token)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    user_id: UUID,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user =
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
@router.put("/cambiar-password-autorizado", dependencies=[Depends(verify_token)])
async def cambiar_password_autorizado(request: CambiarPasswordAutorizadoRequest, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(
        User.email == request.email,
        User.password_hash == request.old_password
        ).first()
    
    if not usuario:
        raise HTTPException(status_code=400, detail="Credenciales inválidas")
    
    usuario.password_hash = request.new_password
    usuario.updated_at = datetime.utcnow()
    db.commit()

    return {
        "msg": "Contraseña actualizada correctamente"
    }

@router.put("/cambiar-password-autorizado/{email}", dependencies=[Depends(verify_token)])
async def cambiar_password_olvido(email: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == email).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    random_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    enviar_correo_contraseña(usuario.email, random_password)

    usuario.password_hash = random_password
    usuario.updated_at = datetime.utcnow()
    db.commit()

    return {
        "msg": "Contraseña actualizada correctamente"
    }


@router.get("/")
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(User).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in usuarios
    ]

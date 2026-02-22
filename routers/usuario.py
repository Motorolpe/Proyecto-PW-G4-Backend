from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from database import get_db
from models import User   

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

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

    # Validar token
    if usuario.recovery_token != token:
        raise HTTPException(status_code=400, detail="Token inválido")

    # Validar expiración
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
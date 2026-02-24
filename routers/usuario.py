from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel
import string
import secrets

from database import get_db
from models import User
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
        raise HTTPException(status_code=400, detail="Token inválido")

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
    return usuarios
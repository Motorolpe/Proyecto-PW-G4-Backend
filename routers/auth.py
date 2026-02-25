import os
import time
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter()
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash de contraseña con bcrypt (trunca a 72 caracteres)."""
    safe_password = password[:72]
    hashed = bcrypt.hashpw(safe_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña con bcrypt."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario."""
    try:
        if len(user.password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña no puede superar 72 caracteres",
            )

        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

        db_fullname = db.query(models.User).filter(models.User.full_name == user.full_name).first()
        if db_fullname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre ya está registrado",
            )

        new_user = models.User(
            full_name=user.full_name,
            email=user.email,
            password_hash=hash_password(user.password),
            role=user.role,
            is_active=True,
            email_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email o nombre",
        )
    except Exception as e:
        db.rollback()
        if isinstance(e, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}",
        )


@router.post("/login", response_model=schemas.TokenResponse)
async def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión — crea Access_log y devuelve token compatible."""
    try:
        db_user = db.query(models.User).filter(models.User.email == credentials.email).first()
        if not db_user or not verify_password(credentials.password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Crear token Access_log (mismo mecanismo que /login legacy)
        hora_actual = time.time_ns()
        cadena = f"{credentials.email}-{hora_actual}"
        token_hash = bcrypt.hashpw(cadena.encode("utf-8"), bcrypt.gensalt())

        db_acceso = models.Access_log(
            id=token_hash.decode("utf-8"),
            last_login=datetime.utcnow(),
            user_id=db_user.id,
        )
        db.add(db_acceso)
        db.commit()
        db.refresh(db_acceso)

        return {"access_token": db_acceso.id, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión: {str(e)}",
        )

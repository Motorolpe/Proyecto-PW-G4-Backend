from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Access_log

router = APIRouter(prefix="/admin", tags=["Admin"])


def verificar_admin(token: str, db: Session):
    access = db.query(Access_log).filter(Access_log.id == token).first()

    if not access:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id == access.id_user).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    return user


@router.post("/users")
def crear_usuario(
    name: str,
    email: str,
    password: str,
    role: str,
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    verificar_admin(token, db)

    nuevo = User(
        name=name,
        email=email,
        password_hash=password,
        role=role
    )

    db.add(nuevo)
    db.commit()

    return {"msg": "Usuario creado"}


@router.put("/users/{user_id}")
def editar_usuario(
    user_id: int,
    name: str,
    email: str,
    role: str,
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    verificar_admin(token, db)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.name = name
    user.email = email
    user.role = role

    db.commit()

    return {"msg": "Usuario actualizado"}


@router.delete("/users/{user_id}")
def eliminar_usuario(
    user_id: int,
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    verificar_admin(token, db)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user)
    db.commit()

    return {"msg": "Usuario eliminado"}
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Access_log
from uuid import UUID
from models import Access_log, Alert, Expense, Budget



router = APIRouter(prefix="/admin", tags=["Admin"])


def verificar_admin(token: str, db: Session):
    access = db.query(Access_log).filter(Access_log.id == token).first()

    if not access:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id == access.user_id).first()

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
        full_name=name,
        email=email,
        password_hash=password,
        role=role
    )

    db.add(nuevo)
    db.commit()

    return {"msg": "Usuario creado"}


@router.put("/users/{user_id}")
def editar_usuario(
    user_id: UUID,
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

    user.full_name = name
    user.email = email
    user.role = role

    db.commit()

    return {"msg": "Usuario actualizado"}


@router.delete("/users/{user_id}")
def eliminar_usuario(
    user_id: UUID,
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    verificar_admin(token, db)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 🔥 Borrar primero los registros relacionados
    db.query(Access_log).filter(Access_log.user_id == user.id).delete()
    db.query(Alert).filter(Alert.user_id == user.id).delete()
    db.query(Expense).filter(Expense.user_id == user.id).delete()
    db.query(Budget).filter(Budget.user_id == user.id).delete()

    # 🔥 Ahora sí borrar usuario
    db.delete(user)
    db.commit()

    return {"msg": "Usuario eliminado correctamente"}
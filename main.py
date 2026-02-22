from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from routers import usuario, egresos

from database import get_db
from models import User

app = FastAPI()

app.include_router(usuario.router)
app.include_router(egresos.router)

@app.get("/login")
async def login(correo: str, contra: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(
        User.email == correo,
        User.password_hash == contra
        ).first()

    if not usuario:
        return {"msg": "Usuario no encontrado"}

    if usuario.password_hash != contra:
        return {"msg": "Contraseña incorrecta"}

    return {
        "msg": "Login exitoso",
        "data": usuario
    }
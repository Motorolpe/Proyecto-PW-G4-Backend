import datetime
import time

import bcrypt
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from routers import usuario, egresos, categorias
from routers import budgets
from routers import admin



from database import get_db
from models import Access_log, User



app = FastAPI()



origins = (
    "*"
)

# Configurar CORS para permitir solicitudes del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuario.router)
app.include_router(egresos.router)
app.include_router(categorias.router)

class LoginRequest(BaseModel):
    username: str
    password: str


class LogoutRequest(BaseModel):
    token: str


class LogoutRequest(BaseModel):
    token: str

@app.post("/login")
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == login_request.username).first()

    if not usuario or not bcrypt.checkpw(
        login_request.password.encode("utf-8"), usuario.password_hash.encode("utf-8")
    ):
        return {"msg": "Usuario no encontrado"}

    hora_actual = time.time_ns()
    cadena_a_encriptar = f"{login_request.username}-{str(hora_actual)}"
    cadena_hasheada = bcrypt.hashpw(cadena_a_encriptar.encode("utf-8"), bcrypt.gensalt())

    db_acceso = Access_log(
        id=cadena_hasheada.decode("utf-8"),
        last_login=datetime.datetime.utcnow(),
        user_id=usuario.id,
    )
    db.add(db_acceso)
    db.commit()
    db.refresh(db_acceso)

    db.refresh(usuario)

    return {
        "msg": "Login exitoso",
        "data": usuario,
        "token": db_acceso.id
    }

@app.delete("/logout")
async def logout(logout_request: LogoutRequest, db : Session = Depends(get_db)):
    db_accesos = db.query(Access_log).filter(Access_log.id == logout_request.token).first() 
    if not db_accesos:
        return {
            "msg" : "Token no existe"
        }
    
    db.delete(db_accesos)
    db.commit()
    return {
        "msg" : "Logout exitoso"
    }

app.include_router(budgets.router)
app.include_router(admin.router)

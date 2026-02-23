import time
import datetime
import bcrypt
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from routers import usuario, egresos

from database import get_db
from models import User, Access_log

app = FastAPI()

origins = (
    "*"
)

app.add_middleware(
    CORSMiddleware,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=origins
)

app.include_router(usuario.router)
app.include_router(egresos.router)

class LoginRequest(BaseModel):
    username: str 
    password: str 

class LogoutRequest(BaseModel):
    token: str

@app.post("/login")
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(
        User.email == login_request.username,
        User.password_hash == login_request.password
        ).first()

    if not usuario:
        return {"msg": "Usuario no encontrado"}
    
    #Creacion de token
    hora_actual = time.time_ns()
    cadena_a_encriptar = f"{login_request.username}-{str(hora_actual)}" 
    cadena_hasheada = bcrypt.hashpw(
        cadena_a_encriptar.encode("utf-8"), 
        bcrypt.gensalt()
        )
    
    db_acceso = Access_log(
        id = cadena_hasheada.decode("utf-8"), #Convierte bytes a string
        last_login = datetime.datetime.now(),
        user_id = usuario.id
    )
    db.add(db_acceso) #Guarda el acceso en db
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
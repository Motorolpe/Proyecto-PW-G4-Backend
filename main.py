import datetime
import time

import bcrypt
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Access_log, User

# Inicializar aplicación FastAPI
app = FastAPI(
    title="Proyecto PW G4 - Sistema de Gestión de Gastos",
    description="API Backend para gestión de gastos y presupuestos",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configurar CORS para permitir solicitudes del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


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
        "token": db_acceso.id,
    }


@app.delete("/logout")
async def logout(logout_request: LogoutRequest, db: Session = Depends(get_db)):
    db_accesos = db.query(Access_log).filter(Access_log.id == logout_request.token).first()
    if not db_accesos:
        return {
            "msg": "Token no existe",
        }

    db.delete(db_accesos)
    db.commit()
    return {
        "msg": "Logout exitoso",
    }

# ============== Health Check Routes ==============
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "API Proyecto PW G4 - Sistema de Gestión de Gastos",
        "version": "1.0.0",
        "status": "online",
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "database": "connected"}

# ============== Include Routers ==============
from routers import usuario, egresos, budgets
from routers import categorias
from routers import auth

# Legacy prefixes (repo original)
app.include_router(usuario.router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(egresos.router, prefix="/egresos", tags=["Egresos"])
app.include_router(categorias.router, prefix="/categorias", tags=["Categorías"])
app.include_router(budgets.router)

# Frontend/alias prefixes (mismas rutas, distinto path)
app.include_router(usuario.router, prefix="/users", tags=["Users"])
app.include_router(egresos.router, prefix="/expenses", tags=["Expenses"])
app.include_router(categorias.router, prefix="/categories", tags=["Categories"])

# Auth (JWT register/login)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
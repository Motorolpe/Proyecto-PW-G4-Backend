from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

import models

# Crear tablas (si no existen)
Base.metadata.create_all(bind=engine)

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
from routers import usuario, egresos, auth, users, expenses, budgets, categories

# Prefijos para compatibilidad con el frontend actual
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(usuario.router, prefix="/api/v1", tags=["Usuarios"])
app.include_router(egresos.router, prefix="/api/v1", tags=["Egresos"])

# Rutas de compatibilidad con el branch original (sin prefijo) para no romper llamados legados
app.include_router(auth.router)
app.include_router(usuario.router)
app.include_router(egresos.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
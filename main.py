from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

# Importar modelos para que SQLAlchemy los reconozca
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
    allow_origins=["*"],  # Cambiar en producción a ["http://localhost:5173"] o el origen del frontend
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
from routers import auth, users, expenses, budgets, categories

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

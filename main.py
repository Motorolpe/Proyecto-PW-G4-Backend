from fastapi import FastAPI
from routers import usuario, egresos

app = FastAPI()

app.include_router(usuario.router)
app.include_router(egresos.router)
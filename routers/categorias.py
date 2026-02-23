from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel

from database import get_db
from models import Category
from security import verify_token

router = APIRouter(prefix="/categorias", tags=["Categorías"])

@router.get("/", dependencies=[Depends(verify_token)])
async def listar_categorias(db: Session = Depends(get_db)):
    categorias = db.query(Category).all()

    if not categorias:
        raise HTTPException(status_code=404, detail="No se encontraron categorías")
    
    return {
        "msg": "Listado de categorías",
        "data": categorias
    }
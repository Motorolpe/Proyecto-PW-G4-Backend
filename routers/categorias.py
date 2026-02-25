from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models import Category
import schemas
from database import get_db
from security import verify_token

router = APIRouter(prefix="/categorias", tags=["Categorías"])

@router.post("", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
async def crear_categoria(category: schemas.CategoryCreate, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    existente = db.query(Category).filter(Category.name == category.name).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La categoría ya existe")

    nueva = Category(
        name=category.name,
        description=category.description,
        created_at=datetime.utcnow(),
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
async def obtener_categoria(category_id: UUID, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    categoria = db.query(Category).filter(Category.id == category_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.put("/{category_id}", response_model=schemas.CategoryResponse)
async def actualizar_categoria(category_id: UUID, category_update: schemas.CategoryUpdate, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    categoria = db.query(Category).filter(Category.id == category_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if category_update.name:
        categoria.name = category_update.name
    if category_update.description is not None:
        categoria.description = category_update.description

    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_categoria(category_id: UUID, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    categoria = db.query(Category).filter(Category.id == category_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(categoria)
    db.commit()
    return None


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

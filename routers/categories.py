from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[schemas.CategoryResponse])
async def list_categories(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Listar todas las categorías"""
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories


@router.post("", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: schemas.CategoryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear nueva categoría"""
    db_category = db.query(models.Category).filter(models.Category.name == category.name).first()

    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría ya existe",
        )

    new_category = models.Category(
        name=category.name,
        description=category.description,
        created_at=datetime.utcnow(),
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.get("/{category_id}", response_model=schemas.CategoryResponse)
async def get_category(category_id: UUID, db: Session = Depends(get_db)):
    """Obtener categoría por ID"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    return category


@router.put("/{category_id}", response_model=schemas.CategoryResponse)
async def update_category(
    category_id: UUID,
    category_update: schemas.CategoryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar categoría"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if category_update.name:
        category.name = category_update.name
    if category_update.description is not None:
        category.description = category_update.description

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar categoría"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(category)
    db.commit()
    return None

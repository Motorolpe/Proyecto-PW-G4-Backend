from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from uuid import UUID

from database import get_db
from models import Expense
from schemas import EgresoType
from security import verify_token

router = APIRouter(prefix="/egresos", tags=["Egresos"])

@router.get("/usuario/{usuario_id}", dependencies=[Depends(verify_token)])
async def listar_egresos(usuario_id: UUID, db: Session = Depends(get_db)):

    lista = db.query(Expense).filter(
        Expense.user_id == usuario_id).order_by(
        Expense.expense_date.desc()).all()

    return {
        "msg": "Listado de egresos",
        "data": lista
    }

@router.get("/grafico/categoria/{usuario_id}", dependencies=[Depends(verify_token)])
async def grafico_por_categoria(usuario_id: UUID, db: Session = Depends(get_db)):

    resultados = db.query(Expense.category_id, func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == usuario_id
    ).group_by(Expense.category_id).all()

    data = [
        {
            "category_id": r.category_id,
            "total": float(r.total)
        }
        for r in resultados
    ]

    return {
        "msg": "Totales por categoria",
        "data": data
    }

@router.get("/grafico/mensual/{usuario_id}", dependencies=[Depends(verify_token)])
async def grafico_mensual(usuario_id: UUID, db: Session = Depends(get_db)):

    resultados = db.query(extract("month", Expense.expense_date).label("mes"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == usuario_id
    ).group_by("mes").order_by("mes").all()

    data = [
        {
            "mes": int(r.mes),
            "total": float(r.total)
        }
        for r in resultados
    ]

    return {
        "msg": "Totales por mes",
        "data": data
    }

@router.post("/crear", dependencies=[Depends(verify_token)])
async def crear_egreso(egreso: EgresoType, db: Session = Depends(get_db)):
    nuevo_egreso = Expense(
        amount = egreso.amount,
        expense_date = egreso.expense_date,
        description = egreso.description,
        is_recurring = egreso.is_recurring,
        created_at = egreso.created_at,
        updated_at = egreso.updated_at,
        user_id = egreso.user_id,
        category_id = egreso.category_id
    )

    db.add(nuevo_egreso)
    db.commit()
    db.refresh(nuevo_egreso)

    return {
        "msg": "Egreso creado correctamente",
        "data": nuevo_egreso
    }
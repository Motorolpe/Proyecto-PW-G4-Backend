from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from uuid import UUID

from database import get_db
from models import Expense

router = APIRouter(prefix="/egresos", tags=["Egresos"])

@router.get("/usuario/{usuario_id}")
def listar_egresos(usuario_id: UUID, db: Session = Depends(get_db)):

    lista = db.query(Expense).filter(
        Expense.user_id == usuario_id).order_by(
        Expense.expense_date.desc()).all()

    return {
        "msg": "Listado de egresos",
        "data": lista
    }

@router.get("/grafico/categoria/{usuario_id}")
def grafico_por_categoria(usuario_id: UUID, db: Session = Depends(get_db)):

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

@router.get("/grafico/mensual/{usuario_id}")
def grafico_mensual(usuario_id: UUID, db: Session = Depends(get_db)):

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
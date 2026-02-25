from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload

import models
from database import get_db
from schemas import EgresoType
from security import verify_token

# Sin prefix: main.py lo registra con /egresos y /expenses
router = APIRouter()


def _require_user_id(token: str, db: Session) -> UUID:
    access = db.query(models.Access_log).filter(models.Access_log.id == token).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return access.user_id

@router.post("/crear", dependencies=[Depends(verify_token)])
@router.post("/", dependencies=[Depends(verify_token)])
async def crear_egreso(egreso: EgresoType, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    user_id = _require_user_id(token, db)
    # Permitir que el body traiga user_id pero validar que coincida
    if egreso.user_id and str(egreso.user_id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear gastos para otros usuarios")

    nuevo_egreso = models.Expense(
        amount=egreso.amount,
        expense_date=egreso.expense_date,
        description=egreso.description,
        is_recurring=egreso.is_recurring,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        user_id=user_id,
        category_id=egreso.category_id,
    )

    db.add(nuevo_egreso)
    db.commit()
    db.refresh(nuevo_egreso)

    return {
        "msg": "Egreso creado correctamente",
        "data": nuevo_egreso,
    }


@router.put("/editar/{egreso_id}", dependencies=[Depends(verify_token)])
async def editar_egreso(egreso_id: UUID, egreso: EgresoType, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    user_id = _require_user_id(token, db)
    egreso_db = db.query(models.Expense).filter(models.Expense.id == egreso_id).first()
    if not egreso_db:
        return {"msg": "Egreso no encontrado"}

    if egreso_db.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para editar este gasto")

    egreso_db.amount = egreso.amount
    egreso_db.expense_date = egreso.expense_date
    egreso_db.description = egreso.description
    egreso_db.is_recurring = egreso.is_recurring
    egreso_db.updated_at = datetime.utcnow()
    egreso_db.category_id = egreso.category_id

    db.commit()
    db.refresh(egreso_db)

    return {"msg": "Egreso editado correctamente", "data": egreso_db}

@router.get("/", dependencies=[Depends(verify_token)])
async def listar_egresos(
    skip: int = 0,
    limit: int = 50,
    category_id: UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    amount_min: float | None = Query(None),
    amount_max: float | None = Query(None),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
):
    """Listado con filtros opcionales (equiv. expenses)."""
    user_id = _require_user_id(token, db)

    query = db.query(models.Expense).filter(models.Expense.user_id == user_id)
    if category_id:
        query = query.filter(models.Expense.category_id == category_id)
    if date_from:
        query = query.filter(models.Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(models.Expense.expense_date <= date_to)
    if amount_min is not None:
        query = query.filter(models.Expense.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(models.Expense.amount <= amount_max)

    expenses = query.order_by(models.Expense.expense_date.desc()).offset(skip).limit(limit).all()
    return expenses


@router.get("/usuario/{usuario_id}", dependencies=[Depends(verify_token)])
async def listar_egresos_por_usuario(usuario_id: UUID, db: Session = Depends(get_db)):

    resultados_db = db.query(models.Expense, models.Category).join(models.Category, models.Expense.category_id == models.Category.id
    ).filter(
        models.Expense.user_id == usuario_id
    ).order_by(
        models.Expense.expense_date.desc()
    ).all()

    lista = []

    for expense, category in resultados_db:
        lista.append({
            "id": expense.id,
            "description": expense.description,
            "amount": expense.amount,
            "expense_date": expense.expense_date,
            "category": category.name  
        })

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

    data = []
    for r in resultados:
        data.append({
            "category_id": r.category_id,
            "total": float(r.total)
        })
        
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

    data = []
    for r in resultados:
        data.append({
            "mes": int(r.mes),
            "total": float(r.total)
        })

    return {
        "msg": "Totales por mes",
        "data": data
    }

@router.get("/{user_id}/atipicos", dependencies=[Depends(verify_token)])
def obtener_gastos_atipicos(user_id: str, db: Session = Depends(get_db)):
    gastos = db.query(Expense).options(
        joinedload(Expense.categories)).filter(
        Expense.user_id == user_id).all()

    total_gastos = len(gastos)
    
    #Que haya un minimo de gastos por analizar
    if total_gastos < 6:
        return {
            "data": []
        }

    suma_total = 0
    for g in gastos:
        suma_total += g.amount

    promedio_general = suma_total/total_gastos

    resultado = []

    for gasto in gastos:
        flags = []
        mensaje = ""
        es_monto_inusual = False
        if gasto.amount > promedio_general * 1.5:
            es_monto_inusual = True
            flags.append("MONTO_INUSUAL")

        contador_categoria = 0
        for g in gastos:
            if g.category_id == gasto.category_id:
                contador_categoria += 1

        es_categoria_poco_frecuente = False
        if contador_categoria <= 3:
            es_categoria_poco_frecuente = True
            flags.append("CATEGORIA_POCO_FRECUENTE")

        if es_monto_inusual and es_categoria_poco_frecuente:
            mensaje = "Este gasto es mayor al promedio habitual y pertenece a una categoría que usas con poca frecuencia."
        elif es_monto_inusual:
            mensaje = "Este gasto supera significativamente tu promedio habitual."
        elif es_categoria_poco_frecuente:
            mensaje = "Esta categoría no es común dentro de tus gastos habituales."

        if len(flags) > 0:
            resultado.append({
                "id": gasto.id,
                "fecha": gasto.expense_date,
                "descripcion": gasto.description,
                "categoria": gasto.categories.name,
                "monto": gasto.amount,
                "flags": flags,
                "mensaje" : mensaje
            })

    return {
        "data": resultado
    }


# ===== Extra endpoints equivalentes a expenses =====

@router.get("/{expense_id}", response_model=None, dependencies=[Depends(verify_token)])
async def obtener_egreso(expense_id: UUID, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    user_id = _require_user_id(token, db)
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este gasto")
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_token)])
async def eliminar_egreso(expense_id: UUID, db: Session = Depends(get_db), token: str = Depends(verify_token)):
    user_id = _require_user_id(token, db)
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    if expense.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para eliminar este gasto")
    db.delete(expense)
    db.commit()
    return None
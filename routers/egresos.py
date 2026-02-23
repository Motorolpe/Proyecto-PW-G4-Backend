from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from uuid import UUID

from database import get_db
from models import Category, Expense
from schemas import EgresoType
from security import verify_token

router = APIRouter(prefix="/egresos", tags=["Egresos"])

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

@router.get("/usuario/{usuario_id}", dependencies=[Depends(verify_token)])
async def listar_egresos(usuario_id: UUID, db: Session = Depends(get_db)):

    resultados_db = db.query(Expense, Category).join(Category, Expense.category_id == Category.id
                    ).filter(Expense.user_id == usuario_id
                    ).order_by(Expense.expense_date.desc()).all()

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

    resultados_db = db.query(Category.name,func.sum(Expense.amount).label("total")
                    ).join(Category, Expense.category_id == Category.id
                    ).filter(Expense.user_id == usuario_id
                    ).group_by(Category.name).all()

    data = []
    for r in resultados_db:
        data.append({
            "category_name": r.name,
            "total": float(r.total)
        })
        
    return {
        "msg": "Totales por categoria",
        "data": data
    }

@router.get("/grafico/mensual/{usuario_id}", dependencies=[Depends(verify_token)])
async def grafico_mensual(usuario_id: UUID, db: Session = Depends(get_db)):

    resultados_db = db.query(extract("month", Expense.expense_date).label("mes"), func.sum(Expense.amount).label("total")
                    ).filter(Expense.user_id == usuario_id
                    ).group_by("mes"
                    ).order_by("mes").all()

    data = []
    for r in resultados_db:
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

@router.put("/editar/{egreso_id}", dependencies=[Depends(verify_token)])
async def editar_egreso(egreso_id: UUID, egreso: EgresoType, db: Session = Depends(get_db)):
    egreso_db = db.query(Expense).filter(Expense.id == egreso_id).first()

    if not egreso_db:
        return {
            "msg": "Egreso no encontrado"
        }

    egreso_db.amount = egreso.amount
    egreso_db.expense_date = egreso.expense_date
    egreso_db.description = egreso.description
    egreso_db.is_recurring = egreso.is_recurring
    egreso_db.updated_at = egreso.updated_at
    egreso_db.category_id = egreso.category_id

    db.commit()
    db.refresh(egreso_db)

    return {
        "msg": "Egreso editado correctamente",
        "data": egreso_db
    }
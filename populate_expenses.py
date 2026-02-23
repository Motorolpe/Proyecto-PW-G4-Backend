import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models

# Crear datos de prueba para gastos

def crear_gastos_prueba():
    db: Session = SessionLocal()
    try:
        # Obtener usuarios y categorías existentes
        usuarios = db.query(models.User).all()
        categorias = db.query(models.Category).all()
        if not usuarios or not categorias:
            print("No hay usuarios o categorías para crear gastos de prueba.")
            return

        for usuario in usuarios:
            for categoria in categorias:
                for i in range(3):
                    gasto = models.Expense(
                        amount=round(100 + i * 10, 2),
                        description=f"Gasto de prueba {i+1} para {usuario.full_name} en {categoria.name}",
                        is_recurring=False,
                        user_id=usuario.id,
                        category_id=categoria.id,
                        expense_date=datetime.utcnow() - timedelta(days=i*5),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(gasto)
        db.commit()
        print("Gastos de prueba creados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error al crear gastos de prueba: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_gastos_prueba()

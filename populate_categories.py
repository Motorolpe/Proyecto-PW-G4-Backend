from datetime import datetime
from database import SessionLocal
import models

def crear_categorias():
    db = SessionLocal()
    try:
        categorias = [
            {"name": "Servicios", "description": "Gastos de servicios"},
            {"name": "Vivienda", "description": "Gastos de vivienda"},
            {"name": "Transporte", "description": "Gastos de transporte"},
            {"name": "Alimentos", "description": "Gastos de alimentos"},
        ]
        for cat in categorias:
            nueva = models.Category(
                name=cat["name"],
                description=cat["description"],
                created_at=datetime.utcnow()
            )
            db.add(nueva)
        db.commit()
        print("Categorías creadas correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error al crear categorías: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_categorias()

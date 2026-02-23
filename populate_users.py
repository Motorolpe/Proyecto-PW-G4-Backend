from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from database import SessionLocal
import models

# Poblar usuarios en meses pasados

def poblar_usuarios():
    db: Session = SessionLocal()
    try:
        usuarios = [
            {"full_name": "usuario_enero", "email": "enero@example.com", "role": "user", "mes": 1},
            {"full_name": "usuario_febrero", "email": "febrero@example.com", "role": "user", "mes": 2},
            {"full_name": "usuario_marzo", "email": "marzo@example.com", "role": "user", "mes": 3},
            {"full_name": "usuario_abril", "email": "abril@example.com", "role": "admin", "mes": 4},
            {"full_name": "usuario_mayo", "email": "mayo@example.com", "role": "user", "mes": 5},
            {"full_name": "usuario_junio", "email": "junio@example.com", "role": "user", "mes": 6},
        ]
        year = datetime.utcnow().year
        for u in usuarios:
            fecha = datetime(year, u["mes"], 15)
            nuevo = models.User(
                id=str(uuid.uuid4()),
                full_name=u["full_name"],
                email=u["email"],
                password_hash=f"fakehash-{u['email']}",  # hash único
                role=u["role"],
                is_active=True,
                email_verified=True,
                created_at=fecha,
                updated_at=fecha,
            )
            db.add(nuevo)
        db.commit()
        print("Usuarios de prueba creados en meses pasados.")
    except Exception as e:
        db.rollback()
        print(f"Error al poblar usuarios: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    poblar_usuarios()

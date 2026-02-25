from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

#CADENA_CONEXION = "postgresql://gastos:gastos@localhost:5432/bd_gastos"
CADENA_CONEXION = os.getenv("DATABASE_URL")

engine = create_engine(CADENA_CONEXION)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = session() #Abre canal de comunicacion con la base de datos
    try:
        yield db #intenta comunicarse
    finally:
        db.close() #Cierra canal de comunicacion con la base de datos

import datetime
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Access_log
from database import get_db

async def verify_token(x_token : str = Header(...), db: Session = Depends(get_db)):
    db_query = db.query(Access_log).filter(Access_log.id == x_token)  
    db_acceso = db_query.first()
    if not db_acceso:
        raise HTTPException(
            status_code=403,
            detail={
                "msg": "Token invalido"
            }
        )

    db_query.update({
        "last_login": datetime.datetime.now()
    })
    db.commit()
    db.refresh(db_acceso)

    return x_token
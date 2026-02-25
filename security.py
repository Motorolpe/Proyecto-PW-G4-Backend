import datetime
from typing import Optional
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Access_log
from database import get_db

async def verify_token(
    x_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    # Acepta x-token o Authorization: Bearer <token>
    token = None
    if x_token:
        token = x_token
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    if not token:
        raise HTTPException(
            status_code=422,
            detail={"msg": "Token requerido (x-token o Authorization: Bearer)"}
        )

    db_query = db.query(Access_log).filter(Access_log.id == token)
    db_acceso = db_query.first()
    if not db_acceso:
        raise HTTPException(
            status_code=403,
            detail={"msg": "Token invalido"}
        )

    db_query.update({"last_login": datetime.datetime.now()})
    db.commit()
    db.refresh(db_acceso)

    return token
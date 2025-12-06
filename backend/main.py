import os
import re
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr, validator

from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, Text, insert, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------
# Konfiguracja DB
# ---------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://lostfound:lostfoundpass@postgres:5432/lostfound_db"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()

found_items = Table(
    "found_items",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("title", String(150)),
    Column("category", String(50)),
    Column("dominant_color", String(30)),
    Column("description", Text),
    Column("distinctive_marks", Text),
    Column("location_found", Text),
    Column("date_found", Date),
    Column("voivodeship", String(50)),
    Column("reporting_entity", String(100)),
)

# ---------------------------
# Mapowanie domen -> województwo (prototyp)
# ---------------------------
DOMAIN_GEO_MAP = {
    "um.warszawa.pl": {"voivodeship": "Mazowieckie", "city": "Warszawa"},
    "um.krakow.pl": {"voivodeship": "Małopolskie", "city": "Kraków"},
    "gdansk.gda.pl": {"voivodeship": "Pomorskie", "city": "Gdańsk"},
    "powiat.pila.pl": {"voivodeship": "Wielkopolskie", "city": "Piła"},
}

def resolve_location_from_email(email: str):
    domain = email.lower().split("@")[-1]
    if domain in DOMAIN_GEO_MAP:
        return DOMAIN_GEO_MAP[domain]
    for pattern, geo in DOMAIN_GEO_MAP.items():
        if domain.endswith(pattern):
            return geo
    return {"voivodeship": None, "city": None}

# ---------------------------
# Modele Pydantic
# ---------------------------
class LoginIn(BaseModel):
    email: EmailStr

class ItemIn(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=150)
    category: constr(strip_whitespace=True, min_length=1, max_length=50)
    dominant_color: constr(strip_whitespace=True, min_length=1, max_length=30)
    location_found: constr(strip_whitespace=True, min_length=1)
    date_found: Optional[date] = None
    description: Optional[str] = None
    distinctive_marks: Optional[str] = None

    @validator("date_found", pre=True, always=True)
    def set_default_date(cls, v):
        if v is None:
            return date.today()
        if isinstance(v, str):
            # oczekujemy ISO 'YYYY-MM-DD'
            return datetime.fromisoformat(v).date()
        return v

    @validator("date_found")
    def date_not_future(cls, v):
        if v > date.today():
            raise ValueError("date_found cannot be in the future")
        return v

# ---------------------------
# FastAPI + CORS
# ---------------------------
app = FastAPI(title="Central Lost&Found - Prototype")

origins = ["http://localhost:3000"]  # Next.js dev/standalone
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Endpoints
# ---------------------------
@app.post("/api/auth/login")
def login(payload: LoginIn):
    geo = resolve_location_from_email(payload.email)
    token = "dev-token"  # prototypowy token
    reporting_entity = payload.email.split("@")[-1]
    return {
        "token": token,
        "voivodeship": geo.get("voivodeship"),
        "city": geo.get("city"),
        "reporting_entity": reporting_entity
    }

@app.post("/api/items")
def create_item(item: ItemIn, email: Optional[str] = Query(None, description="email urzędnika")):
    # resolve reporting entity/voivodeship
    if email:
        geo = resolve_location_from_email(email)
        voivodeship = geo.get("voivodeship") or "Unknown"
        reporting_entity = email.split("@")[-1]
    else:
        voivodeship = "Unknown"
        reporting_entity = "Unknown"

    # prosta anonimizacja PESEL (11 cyfr)
    def sanitize(text):
        if not text:
            return text
        return re.sub(r"\b\d{11}\b", "[REDACTED]", text)

    item.description = sanitize(item.description)
    item.distinctive_marks = sanitize(item.distinctive_marks)

    try:
        with engine.begin() as conn:
            stmt = insert(found_items).values(
                title=item.title,
                category=item.category,
                dominant_color=item.dominant_color,
                description=item.description,
                distinctive_marks=item.distinctive_marks,
                location_found=item.location_found,
                date_found=item.date_found,
                voivodeship=voivodeship,
                reporting_entity=reporting_entity
            ).returning(found_items.c.id)
            res = conn.execute(stmt)
            new_id = res.scalar()
        return {"status": "ok", "id": str(new_id)}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export")
def export_all():
    try:
        with engine.connect() as conn:
            rows = conn.execute(select(found_items)).fetchall()
            items = [dict(r._mapping) for r in rows]
            # zamień date na iso string
            for it in items:
                if isinstance(it.get("date_found"), date):
                    it["date_found"] = it["date_found"].isoformat()
        return {"count": len(items), "items": items}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

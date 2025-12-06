import os
import re
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, Date, Text, insert, select
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError


# ---------------------------
# Sessions (in-memory)
# ---------------------------
SESSIONS = {}   # token -> session data


# ---------------------------
# DB config
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
# Email → region map
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
    # match subdomains
    for pattern, geo in DOMAIN_GEO_MAP.items():
        if domain.endswith(pattern):
            return geo
    return {"voivodeship": None, "city": None}


# ---------------------------
# Pydantic models
# ---------------------------
class LoginIn(BaseModel):
    email: EmailStr


class ItemIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, strip_whitespace=True)
    category: str = Field(..., min_length=1, max_length=50, strip_whitespace=True)
    dominant_color: str = Field(..., min_length=1, max_length=30, strip_whitespace=True)
    location_found: str = Field(..., min_length=1, strip_whitespace=True)
    date_found: Optional[date] = None
    description: Optional[str] = None
    distinctive_marks: Optional[str] = None

    @field_validator("date_found")
    def normalize_date(cls, v):
        if v is None:
            return date.today()
        if isinstance(v, str):
            return datetime.fromisoformat(v).date()
        return v

    @field_validator("date_found")
    def cannot_be_future(cls, v):
        if v > date.today():
            raise ValueError("date_found cannot be in the future")
        return v


# ---------------------------
# FastAPI
# ---------------------------
app = FastAPI(title="Central Lost&Found - Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# Endpoints
# ---------------------------

# LOGIN
@app.post("/api/auth/login")
def login(payload: LoginIn):
    geo = resolve_location_from_email(payload.email)

    token = str(uuid.uuid4())
    reporting_entity = payload.email.split("@")[-1]

    SESSIONS[token] = {
        "email": payload.email,
        "voivodeship": geo.get("voivodeship"),
        "city": geo.get("city"),
        "reporting_entity": reporting_entity,
    }

    return {
        "token": token,
        "voivodeship": geo.get("voivodeship"),
        "city": geo.get("city"),
        "reporting_entity": reporting_entity,
    }


# CREATE ITEM
@app.post("/api/items")
def create_item(
    item: ItemIn,
    token: Optional[str] = Header(None)
):
    if not token or token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    session = SESSIONS[token]

    email = session["email"]
    voivodeship = session["voivodeship"] or "Unknown"
    reporting_entity = session["reporting_entity"]

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
                reporting_entity=reporting_entity,
            ).returning(found_items.c.id)

            new_id = conn.execute(stmt).scalar()

        return {"status": "ok", "id": str(new_id)}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# EXPORT ALL
@app.get("/api/export")
def export_all():
    try:
        with engine.connect() as conn:
            rows = conn.execute(select(found_items)).fetchall()
            items = [dict(r._mapping) for r in rows]

            for it in items:
                if isinstance(it.get("date_found"), date):
                    it["date_found"] = it["date_found"].isoformat()

        return {"count": len(items), "items": items}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
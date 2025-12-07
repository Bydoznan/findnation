import os
import re
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, constr, validator

from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, Text, insert, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError

from xml.etree.ElementTree import Element, tostring

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
# Mapowanie domen -> województwo
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
# XML utilities
# ---------------------------
def dict_to_xml(tag: str, data: dict) -> str:
    root = Element(tag)
    for key, value in data.items():
        child = Element(str(key))
        child.text = str(value)
        root.append(child)
    return tostring(root, encoding="unicode")

def auto_response(data, root: str, accept: str):
    """Zwraca XML lub JSON zależnie od nagłówka Accept."""
    if accept and "application/xml" in accept.lower():
        return Response(content=dict_to_xml(root, data), media_type="application/xml")
    return data

# ---------------------------
# Modele Pydantic
# ---------------------------
class LoginIn(BaseModel):
    email: EmailStr

class ItemIn(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=150)
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

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Helpers
# ---------------------------
def row_to_dict(row):
    d = dict(row._mapping)
    if isinstance(d.get("date_found"), date):
        d["date_found"] = d["date_found"].isoformat()
    return d


# ============================================================
# ENDPOINTY
# ============================================================

@app.post("/api/auth/login")
def login(payload: LoginIn):
    geo = resolve_location_from_email(payload.email)
    token = "dev-token"
    return {
        "token": token,
        "voivodeship": geo.get("voivodeship"),
        "city": geo.get("city"),
        "reporting_entity": payload.email.split("@")[-1]
    }

@app.post("/api/items")
def create_item(item: ItemIn, email: Optional[str] = Query(None)):
    if email:
        geo = resolve_location_from_email(email)
        voivodeship = geo.get("voivodeship") or "Unknown"
        reporting_entity = email.split("@")[-1]
    else:
        voivodeship = "Unknown"
        reporting_entity = "Unknown"

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
                dominant_color=item.dominant_color,
                description=item.description,
                distinctive_marks=item.distinctive_marks,
                location_found=item.location_found,
                date_found=item.date_found,
                voivodeship=voivodeship,
                reporting_entity=reporting_entity
            ).returning(found_items.c.id)
            new_id = conn.execute(stmt).scalar()
        return {"status": "ok", "id": str(new_id)}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# NOWE GET-y dla tabeli + XML negotiation
# ============================================================

@app.get("/api/items")
def get_items(
    request: Request,
    voivodeship: Optional[str] = None,
    color: Optional[str] = Query(None, alias="dominant_color"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 50,
    offset: int = 0
):
    accept = request.headers.get("accept")
    try:
        stmt = select(found_items)

        if voivodeship:
            stmt = stmt.where(found_items.c.voivodeship == voivodeship)
        if color:
            stmt = stmt.where(found_items.c.dominant_color == color)
        if date_from:
            stmt = stmt.where(found_items.c.date_found >= date_from)
        if date_to:
            stmt = stmt.where(found_items.c.date_found <= date_to)

        stmt = stmt.limit(limit).offset(offset)

        with engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
            items = [row_to_dict(r) for r in rows]

        result = {"count": len(items), "items": items}
        return auto_response(result, "items", accept)

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/items/{item_id}")
def get_item_by_id(request: Request, item_id: str):
    accept = request.headers.get("accept")
    try:
        stmt = select(found_items).where(found_items.c.id == item_id)
        with engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Item not found")
            return auto_response(row_to_dict(row), "item", accept)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/items/search")
def search_items(request: Request, q: str):
    accept = request.headers.get("accept")
    try:
        stmt = select(found_items).where(
            found_items.c.title.ilike(f"%{q}%") |
            found_items.c.description.ilike(f"%{q}%") |
            found_items.c.distinctive_marks.ilike(f"%{q}%")
        )
        with engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        result = {"count": len(rows), "items": [row_to_dict(r) for r in rows]}
        return auto_response(result, "search", accept)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export")
def export_all(request: Request):
    accept = request.headers.get("accept")
    try:
        with engine.connect() as conn:
            rows = conn.execute(select(found_items)).fetchall()
            items = [row_to_dict(r) for r in rows]

        return auto_response({"count": len(items), "items": items}, "items", accept)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

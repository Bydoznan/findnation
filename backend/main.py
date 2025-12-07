import os
import re
import uuid
from datetime import date, datetime
from typing import Optional
import requests
import xml.etree.ElementTree as ET

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, Date, Text, insert, select
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import Response





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
    
@app.get("/api/import/bip")
def import_bip(url: str):
    """
    Importuje dane z plików XML BIP (RSS, Atom lub własny format XML).
    Zapisuje rekordy do found_items.
    """
    # -----------------------
    # Pobierz XML
    # -----------------------
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        xml_data = response.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot download XML: {e}")

    # -----------------------
    # Parsowanie XML
    # -----------------------
    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {e}")

    imported_ids = []

    # -----------------------
    # RSS 2.0
    # -----------------------
    if root.tag.lower().endswith("rss"):
        items = root.findall(".//item")
        for it in items:
            title = it.findtext("title") or "No title"
            desc = it.findtext("description") or ""
            pub_date = it.findtext("pubDate")

            _id = save_imported_item(title, desc, pub_date)
            if _id:
                imported_ids.append(_id)

    # -----------------------
    # ATOM
    # -----------------------
    elif "feed" in root.tag.lower():
        entries = root.findall(".//entry")
        for it in entries:
            title = it.findtext("title") or "No title"
            desc = it.findtext("summary") or it.findtext("content") or ""
            pub_date = it.findtext("updated") or it.findtext("published")

            _id = save_imported_item(title, desc, pub_date)
            if _id:
                imported_ids.append(_id)

    # -----------------------
    # CUSTOM XML (fallback)
    # -----------------------
    else:
        rows = root.findall(".//row")
        for it in rows:
            title = it.findtext("title") or it.findtext("name") or "No title"
            desc = it.findtext("description") or ""
            pub_date = it.findtext("date")

            _id = save_imported_item(title, desc, pub_date)
            if _id:
                imported_ids.append(_id)

    return {
        "imported_count": len(imported_ids),
        "ids": imported_ids
    }


def save_imported_item(title, description, pub_date):
    """
    Normalizuje dane i zapisuje do found_items.
    """
    # normalizacja daty
    try:
        if pub_date:
            d = datetime.fromisoformat(pub_date.replace("Z", "")).date()
        else:
            d = date.today()
    except:
        d = date.today()

    try:
        with engine.begin() as conn:
            stmt = insert(found_items).values(
                title=title,
                dominant_color="Unknown",
                description=description,
                distinctive_marks=None,
                location_found="BIP Import",
                date_found=d,
                voivodeship="Unknown",
                reporting_entity="BIP Import",
            ).returning(found_items.c.id)

            result = conn.execute(stmt)
            return str(result.scalar())

    except Exception as e:
        print("DB error:", e)
        return None
    
@app.get("/api/metadata.xml")
def get_metadata_xml():
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<dcat:Dataset
    xmlns:dcat="http://www.w3.org/ns/dcat#"
    xmlns:dct="http://purl.org/dc/terms/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema#">

    <dct:title>Rzeczy znalezione – zbiór danych</dct:title>
    <dct:description>Zestaw danych zawierający zgłoszenia rzeczy znalezionych z samorządów w Polsce. Dane dostępne są w formacie JSON oraz CSV.</dct:description>

    <dct:publisher>
        <dct:Agent>
            <dct:title>Jednostki samorządu terytorialnego</dct:title>
        </dct:Agent>
    </dct:publisher>

    <dct:issued>2025-02-15</dct:issued>
    <dct:modified>2025-02-15</dct:modified>

    <dcat:keyword>zguby</dcat:keyword>
    <dcat:keyword>rzeczy znalezione</dcat:keyword>

    <dcat:distribution>
        <dcat:Distribution>
            <dct:title>Dane JSON – wszystkie zgłoszenia</dct:title>
            <dcat:accessURL>http://localhost:8000/api/export</dcat:accessURL>
            <dcat:downloadURL>http://localhost:8000/api/export</dcat:downloadURL>
            <dct:format>application/json</dct:format>
        </dcat:Distribution>
    </dcat:distribution>

    <dcat:distribution>
        <dcat:Distribution>
            <dct:title>Przykładowe dane CSV</dct:title>
            <dcat:accessURL>http://localhost:8000/api/sample.csv</dcat:accessURL>
            <dcat:downloadURL>http://localhost:8000/api/sample.csv</dcat:downloadURL>
            <dct:format>text/csv</dct:format>
        </dcat:Distribution>
    </dcat:distribution>
</dcat:Dataset>'''

    return Response(content=xml_content, media_type="application/xml")

@app.get("/api/sample.csv")
def get_sample_csv():
    csv_content = (
        "title,dominant_color,description,distinctive_marks,location_found,date_found,voivodeship,reporting_entity\n"
        "Parasolka czarna,Czarny,Parasolka znaleziona w autobusie,Brak,Przystanek Dworzec Główny,2025-02-14,Mazowieckie,um.warszawa.pl\n"
        "Plecak niebieski,Niebieski,Plecak szkolny,Naklejka z psem,Ul. Długa 12,2025-02-13,Małopolskie,um.krakow.pl\n"
        "Portfel brązowy,Brązowy,Portfel znaleziony w kawiarni,Inicjały A.K.,Kawiarnia Centralna,2025-02-11,Pomorskie,gdansk.gda.pl\n"
    )
    return Response(content=csv_content, media_type="text/csv")
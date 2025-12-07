import os
import re
import uuid
from datetime import date, datetime
from typing import Optional
import requests
import xml.etree.ElementTree as ET

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, Date, Text, insert, select
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import Response


# -------------------------------------------------------------------
# DATABASE CONNECTION  (RENAMED)
# -------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://findnation:findnationpass@postgres:5432/findnation_db"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()

found_items = Table(
    "found_items",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("title", String(150)),
    Column("description", Text),
    Column("location_found", Text),
    Column("dominant_color", String(30)),
    Column("date_found", Date),
    Column("email", String(200)),
    Column("voivodeship", String(50)),
    Column("reporting_entity", String(100)),
)

# Create table automatically if missing
metadata.create_all(engine)


# -------------------------------------------------------------------
# MAP EMAIL DOMAIN → VOIVODESHIP
# -------------------------------------------------------------------
DOMAIN_GEO_MAP = {
    "um.warszawa.pl": {"voivodeship": "Mazowieckie"},
    "um.krakow.pl": {"voivodeship": "Małopolskie"},
    "gdansk.gda.pl": {"voivodeship": "Pomorskie"},
    "powiat.pila.pl": {"voivodeship": "Wielkopolskie"},
}

def resolve_voivodeship(email: str):
    domain = email.lower().split("@")[-1]
    for d, geo in DOMAIN_GEO_MAP.items():
        if domain == d or domain.endswith(d):
            return geo["voivodeship"]
    return "Unknown"


# -------------------------------------------------------------------
# INPUT MODEL FOR ITEM CREATION
# -------------------------------------------------------------------
class ItemIn(BaseModel):
    email: EmailStr
    title: str
    description: Optional[str] = None
    location_found: str
    dominant_color: str
    date_found: Optional[date] = None

    @field_validator("date_found")
    def normalize_date(cls, v):
        if not v:
            return date.today()
        if isinstance(v, str):
            return datetime.fromisoformat(v).date()
        return v


# -------------------------------------------------------------------
# FASTAPI SETUP (RENAMED)
# -------------------------------------------------------------------
app = FastAPI(title="FindNation – Central Lost & Found Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# CREATE ITEM
# -------------------------------------------------------------------
@app.post("/api/items")
def create_item(item: ItemIn):

    voivodeship = resolve_voivodeship(item.email)
    reporting_entity = item.email.split("@")[-1]

    # Remove potential PESEL numbers
    def sanitize(text):
        if not text:
            return text
        return re.sub(r"\b\d{11}\b", "[REDACTED]", text)

    item.description = sanitize(item.description)

    try:
        with engine.begin() as conn:
            stmt = insert(found_items).values(
                id=uuid.uuid4(),
                title=item.title,
                description=item.description,
                location_found=item.location_found,
                dominant_color=item.dominant_color,
                date_found=item.date_found,
                email=item.email,
                voivodeship=voivodeship,
                reporting_entity=reporting_entity,
            ).returning(found_items.c.id)

            new_id = conn.execute(stmt).scalar()

        return {"status": "ok", "id": str(new_id)}

    except SQLAlchemyError as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------------------
# EXPORT ALL ITEMS (Open Data)
# -------------------------------------------------------------------
@app.get("/api/export")
def export_all():
    try:
        with engine.connect() as conn:
            rows = conn.execute(select(found_items)).fetchall()
            items = [dict(r._mapping) for r in rows]

        for it in items:
            if isinstance(it["date_found"], date):
                it["date_found"] = it["date_found"].isoformat()

        return {"count": len(items), "items": items}

    except SQLAlchemyError as e:
        raise HTTPException(500, str(e))


# -------------------------------------------------------------------
# IMPORT FROM BIP XML
# -------------------------------------------------------------------
@app.get("/api/import/bip")
def import_bip(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        xml_data = response.content
    except Exception as e:
        raise HTTPException(400, f"Cannot download XML: {e}")

    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        raise HTTPException(400, f"Invalid XML: {e}")

    imported_ids = []

    def save(title, desc, pub_date):
        try:
            d = datetime.fromisoformat(
                pub_date.replace("Z", "")
            ).date() if pub_date else date.today()
        except:
            d = date.today()

        try:
            with engine.begin() as conn:
                stmt = insert(found_items).values(
                    id=uuid.uuid4(),
                    title=title,
                    description=desc,
                    location_found="BIP Import",
                    dominant_color="Unknown",
                    date_found=d,
                    email="bip@import",
                    voivodeship="Unknown",
                    reporting_entity="BIP Import",
                ).returning(found_items.c.id)

                return str(conn.execute(stmt).scalar())
        except:
            return None

    # RSS
    if root.tag.lower().endswith("rss"):
        for it in root.findall(".//item"):
            imported_ids.append(save(
                it.findtext("title") or "No title",
                it.findtext("description") or "",
                it.findtext("pubDate")
            ))

    # ATOM
    elif "feed" in root.tag.lower():
        for it in root.findall(".//entry"):
            imported_ids.append(save(
                it.findtext("title") or "No title",
                it.findtext("summary") or it.findtext("content") or "",
                it.findtext("updated") or it.findtext("published")
            ))

    # CUSTOM
    else:
        for it in root.findall(".//row"):
            imported_ids.append(save(
                it.findtext("title") or it.findtext("name") or "No title",
                it.findtext("description") or "",
                it.findtext("date")
            ))

    imported_ids = [i for i in imported_ids if i]

    return {"imported_count": len(imported_ids), "ids": imported_ids}


# -------------------------------------------------------------------
# METADATA (DCAT)
# -------------------------------------------------------------------
@app.get("/api/metadata.xml")
def get_metadata_xml():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<dcat:Dataset xmlns:dcat="http://www.w3.org/ns/dcat#" xmlns:dct="http://purl.org/dc/terms/">
    <dct:title>FindNation – Dataset of Found Items</dct:title>
    <dct:description>Zgłoszenia rzeczy znalezionych w polskich samorządach.</dct:description>

    <dcat:distribution>
        <dcat:Distribution>
            <dct:title>Dane JSON</dct:title>
            <dcat:accessURL>http://localhost:8000/api/export</dcat:accessURL>
            <dct:format>application/json</dct:format>
        </dcat:Distribution>
    </dcat:distribution>
</dcat:Dataset>
"""
    return Response(content=xml, media_type="application/xml")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import requests
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from bs4 import BeautifulSoup

SOURCE_URL = os.getenv("SOURCE_URL", "https://emasantam.id/harga-emas-antam-harian/")
APP_TOKEN = os.getenv("APP_TOKEN")
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "12"))
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "3"))
CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "300"))

ID_MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
}
JKT_TZ = timezone(timedelta(hours=7))

app = FastAPI(title="lm-api", description="Harga emas ANTAM API", version="1.0.0", docs_url=None, redoc_url=None)
security = HTTPBearer(auto_error=True)

def auth_guard(creds: HTTPAuthorizationCredentials = Depends(security)):
    if not APP_TOKEN:
        raise HTTPException(status_code=500, detail="APP_TOKEN not set")
    if creds.scheme.lower() != "bearer" or creds.credentials != APP_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return True

@dataclass
class HargaPayload:
    source_url: str
    fetched_at_utc: str
    harga_tanggal_text: Optional[str]
    harga_tanggal_iso_jkt: Optional[str]
    harga_idr: Optional[int]
    note: Optional[str]

def http_get(url: str) -> requests.Response:
    last_err = None
    for attempt in range(HTTP_RETRIES):
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_err = e
            time.sleep(1.5 ** attempt)
    raise last_err

def to_int_idr(text: str) -> Optional[int]:
    if not text: return None
    import re
    m = re.search(r"Rp\.?\s*([0-9\.\,]+)", text, flags=re.I)
    val = m.group(1) if m else text
    val = val.replace(".", "").replace(",", "")
    return int(val) if val.isdigit() else None

def parse_id_date(text: str) -> Optional[datetime]:
    if not text: return None
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text, flags=re.I)
    if not m: return None
    d, mon_name, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    mon = ID_MONTHS.get(mon_name)
    return datetime(y, mon, d, 0, 0, 0, tzinfo=JKT_TZ) if mon else None

def parse_fields(html: str):
    soup = BeautifulSoup(html, "html.parser")
    notes = []
    harga_el = soup.select_one("div.harga-hari-ini") or soup.select_one('div[title*="ANTAM 1 gram"]')
    harga_text = harga_el.get_text(strip=True) if harga_el else None
    if harga_text: notes.append("harga via selector")
    harga_idr = to_int_idr(harga_text) if harga_text else None
    tgl_el = soup.select_one("div.harga-tanggal")
    tgl_text = tgl_el.get_text(strip=True) if tgl_el else None
    if tgl_text: notes.append("tanggal via selector")
    tgl_iso = parse_id_date(tgl_text).isoformat() if tgl_text and parse_id_date(tgl_text) else None
    return tgl_text, tgl_iso, harga_idr, harga_text, " | ".join(notes)

_cache = {"ts": 0.0, "data": None}
def get_cached(): return _cache["data"] if _cache["data"] and (time.time() - _cache["ts"]) <= CACHE_TTL_SEC else None
def set_cache(payload): _cache.update(ts=time.time(), data=payload)

@app.get("/health")
def health(): return {"ok": True, "service": "lm-api", "source_url": SOURCE_URL}

@app.get("/harga")
def get_harga(_: bool = Depends(auth_guard)):
    cached = get_cached()
    if cached:
        return JSONResponse({
            "harga_tanggal_text": cached.harga_tanggal_text,
            "harga_idr": cached.harga_idr,
            "source_url": cached.source_url,
            "fetched_at_utc": cached.fetched_at_utc,
            "note": cached.note
        })
    resp = http_get(SOURCE_URL)
    tgl_text, tgl_iso, harga_idr, harga_text, note = parse_fields(resp.text)
    payload = HargaPayload(
        source_url=SOURCE_URL,
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
        harga_tanggal_text=tgl_text,
        harga_tanggal_iso_jkt=tgl_iso,
        harga_idr=harga_idr,
        note=note,
    )
    set_cache(payload)
    return JSONResponse({
        "harga_tanggal_text": payload.harga_tanggal_text,
        "harga_idr": payload.harga_idr,
        "source_url": payload.source_url,
        "fetched_at_utc": payload.fetched_at_utc,
        "note": payload.note
    })

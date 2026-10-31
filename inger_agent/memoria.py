"""Memoria a largo plazo (eventos) y escritura controlada de borradores (SQLite local)."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import hashlib


class MemoriaPersistente:
    def __init__(self, ruta: str | Path):
        self.ruta = str(ruta)
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.ruta) as cx:
            cx.execute("CREATE TABLE IF NOT EXISTS memoria (id INTEGER PRIMARY KEY, hilo TEXT NOT NULL, caso_id TEXT, intencion TEXT NOT NULL, resumen TEXT NOT NULL, creado TEXT NOT NULL)")
            cx.execute("CREATE TABLE IF NOT EXISTS borradores (id INTEGER PRIMARY KEY, clave TEXT UNIQUE NOT NULL, hilo TEXT NOT NULL, caso_id TEXT NOT NULL, contenido TEXT NOT NULL, creado TEXT NOT NULL)")

    def recordar(self, hilo: str, caso_id: str | None, intencion: str, resumen: str) -> None:
        with sqlite3.connect(self.ruta) as cx:
            cx.execute("INSERT INTO memoria (hilo,caso_id,intencion,resumen,creado) VALUES (?,?,?,?,?)",
                       (hilo, caso_id, intencion, resumen[:500], datetime.now(timezone.utc).isoformat()))

    def recuerdos(self, hilo: str, limite: int = 5) -> list[dict]:
        with sqlite3.connect(self.ruta) as cx:
            rows = cx.execute("SELECT caso_id,intencion,resumen,creado FROM memoria WHERE hilo=? ORDER BY id DESC LIMIT ?", (hilo, limite)).fetchall()
        return [dict(zip(("caso_id","intencion","resumen","creado"), row)) for row in rows]

    def guardar_borrador(self, hilo: str, caso_id: str, contenido: str, solicitud: str) -> dict:
        clave = hashlib.sha256(f"{hilo}|{caso_id}|{solicitud}".encode()).hexdigest()
        stamp = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.ruta) as cx:
            cx.execute("INSERT OR IGNORE INTO borradores (clave,hilo,caso_id,contenido,creado) VALUES (?,?,?,?,?)",
                       (clave, hilo, caso_id, contenido[:4000], stamp))
            row = cx.execute("SELECT id,creado FROM borradores WHERE clave=?",(clave,)).fetchone()
        return {"borrador_id": row[0], "caso_id": caso_id,"creado": row[1],"idempotente": True}

    def borradores(self, hilo: str) -> list[dict]:
        with sqlite3.connect(self.ruta) as cx:
            rows = cx.execute("SELECT id,caso_id,contenido,creado FROM borradores WHERE hilo=? ORDER BY id",(hilo,)).fetchall()
        return [dict(zip(("id","caso_id","contenido","creado"), row)) for row in rows]

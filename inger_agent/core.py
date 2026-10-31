"""Dominio y herramientas deterministas verificables sin acceso a redes."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any

CASO_RX = re.compile(r"\bCASO[\s-]?(\d{3,6})\b", re.IGNORECASE)


def normalizar_id(texto: str) -> str | None:
    m = CASO_RX.search(texto or "")
    return f"CASO-{m.group(1)}" if m else None


def clasificar_intencion(texto: str) -> str:
    s = texto.casefold()
    if any(p in s for p in ("guardar borrador", "guarda borrador", "registrar borrador", "registra borrador")):
        return "borrador"
    if any(p in s for p in ("norma", "procedimiento", "protocolo", "documento", "regulación", "reglamento")):
        return "normativa"
    if any(p in s for p in ("prioriz", "prioridad", "ordenar casos", "qué casos revisar", "requieren revisión", "revisión administrativa")):
        return "priorizacion"
    if any(p in s for p in ("pendiente", "inconsistencia", "sin resolver", "falta", "no realizado", "espera")):
        return "pendientes"
    return "sintesis"


@dataclass(frozen=True)
class Fragmento:
    fuente_id: str
    titulo: str
    texto: str
    caso_id: str | None
    categoria: str
    anio: int | None = None

    def como_dict(self) -> dict[str, Any]:
        return {"fuente_id": self.fuente_id, "titulo": self.titulo, "texto": self.texto,
                "caso_id": self.caso_id, "categoria": self.categoria, "anio": self.anio}


class RepositorioDemo:
    def __init__(self, data_dir: str | Path):
        data_dir = Path(data_dir)
        self.casos = {x["caso_id"]: x for x in json.loads((data_dir / "casos_demo.json").read_text(encoding="utf-8"))["casos"]}
        self.documentos = json.loads((data_dir / "documentos_demo.json").read_text(encoding="utf-8"))["documentos"]
        self.reglas = json.loads((data_dir / "reglas_demo.json").read_text(encoding="utf-8"))["reglas"]
        self.fragmentos = self._construir()

    def _construir(self) -> list[Fragmento]:
        fragments = []
        for cid, c in self.casos.items():
            y = c["anio"]
            seguimiento = (f"{cid}. Alta: {c['fecha_alta']}. Control: {c['fecha_control']}. "
                           f"Motivo: {c['motivo_control']}. Gestiones: " + "; ".join(
                               f"{g['fecha']} [{g['estado']}] {g['descripcion']}" for g in c["gestiones"]))
            fragments.append(Fragmento(f"ORT-{y}-{cid}", f"Ortogeriatría {y} (ficticia)", seguimiento, cid, "seguimiento", y))
            inter = c["interconsulta"]
            fragments.append(Fragmento(f"INT-{cid}", "Interconsultas y traslados (ficticio)",
                f"{cid}. Interconsulta: estado={inter['estado']}; fecha={inter.get('fecha') or 'sin dato'}; "
                f"observaciones={inter.get('observaciones') or 'sin dato'}; traslado estado={c['traslado']['estado']}; "
                f"motivo={c['traslado']['motivo']}; días de espera registrados="
                f"{c['dias_espera_registrados'] if c['dias_espera_registrados'] is not None else 'sin dato'}.",
                cid, "interconsulta_traslado", y))
        for d in self.documentos:
            fragments.append(Fragmento(d["fuente_id"],d["titulo"],d["texto"],None,"normativa_demo",None))
        return fragments

    def por_caso(self, caso_id: str) -> list[Fragmento]:
        return [f for f in self.fragmentos if f.caso_id == caso_id]

    def por_tipo(self, categoria: str) -> list[Fragmento]:
        return [f for f in self.fragmentos if f.categoria == categoria]

    def evaluacion_administrativa(self, caso_id: str) -> dict[str, Any]:
        """Aplica solo las reglas SIMULADAS publicadas, sin interpretar riesgo clínico."""
        caso = self.casos.get(caso_id)
        if caso is None:
            return {"caso_id": caso_id, "estado": "no_encontrado", "reglas_activadas": []}
        activadas = []
        for regla in self.reglas:
            campo = regla["campo"]
            if campo == "interconsulta.estado":
                activo = caso["interconsulta"]["estado"] == regla["valor"]
            elif campo == "traslado.estado":
                activo = caso["traslado"]["estado"] in regla["valores"]
            elif campo == "gestiones.estado":
                activo = any(g["estado"] == regla["valor"] for g in caso["gestiones"])
            else:
                raise ValueError(f"Regla desconocida {campo}")
            if activo:
                activadas.append({"id": regla["id"], "descripcion": regla["descripcion"]})
        return {"caso_id": caso_id, "estado": "revision_administrativa_sugerida" if activadas else "sin_criterios_activados",
                "reglas_activadas": activadas,
                "advertencia": "Reglas simuladas: NO constituyen priorización clínica ni reglas aprobadas por INGER."}

    def evaluacion_general(self) -> list[dict[str, Any]]:
        return [self.evaluacion_administrativa(cid) for cid in sorted(self.casos)]


def referencia_conversacional(texto: str) -> bool:
    """Elipsis explícita: permite continuidad SIN adivinar el caso en preguntas generales."""
    s = texto.casefold()
    return any(x in s for x in ("sus pendientes", "del mismo caso", "ese caso", "este caso", "¿y los pendientes", "y sus gestiones", "¿y su traslado"))


def evaluar_permiso_escritura(rol: str, texto: str) -> tuple[bool, str]:
    if rol != "gestor_demo":
        return False, "Acceso denegado: la escritura de borradores exige rol gestor_demo."
    if clasificar_intencion(texto) != "borrador":
        return False, "Escritura denegada: se requiere solicitud explícita de guardar borrador."
    return True, "Permitido: borrador local de demostración; no modifica fuentes originales."

"""Recuperación híbrida: filtro exacto + similitud semántica (FAISS real en modo Groq).

El recuperador léxico es SOLO una alternativa offline para pruebas sin descargas.
"""
from __future__ import annotations
from .core import Fragmento, RepositorioDemo
import re
import numpy as np


def _palabras(s: str) -> set[str]:
    return {x for x in re.findall(r"[\wáéíóúñ]{3,}", s.casefold())}


class Buscador:
    def __init__(self, repo: RepositorioDemo, semantico: bool = True):
        self.repo = repo
        self.semantico = semantico
        self.index = None
        self.modelo = None
        if semantico:
            try:
                import faiss
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("Instale requirements.txt: faltan FAISS o sentence-transformers.") from exc
            self.faiss = faiss
            self.modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            vectores = self.modelo.encode([f"{f.titulo}. {f.texto}" for f in repo.fragmentos], convert_to_numpy=True).astype("float32")
            faiss.normalize_L2(vectores)
            self.index = faiss.IndexFlatIP(vectores.shape[1])
            self.index.add(vectores)

    def buscar(self, pregunta: str, caso_id: str | None = None, categoria: str | None = None, k: int = 5) -> list[Fragmento]:
        # Reglas estrictas: un filtro por caso o por documentos evita contaminación cruzada.
        permitidos = [i for i,f in enumerate(self.repo.fragmentos)
                      if (caso_id is None or f.caso_id == caso_id) and (categoria is None or f.categoria == categoria)]
        if not permitidos:
            return []
        if caso_id:
            # Una ficha exacta debe incluir ambos registros, no solo el top-k semántico.
            return [self.repo.fragmentos[i] for i in permitidos]
        if self.semantico:
            q = self.modelo.encode([pregunta], convert_to_numpy=True).astype("float32")
            self.faiss.normalize_L2(q)
            # Indices del corpus completo; se filtran permisos antes de devolver.
            # Búsqueda sobre todos, con sobre-recuperación hasta abarcar el universo.
            scores, ids = self.index.search(q, len(self.repo.fragmentos))
            resultados = [(float(score), int(idx)) for score,idx in zip(scores[0],ids[0])
                          if int(idx) in permitidos and float(score) >= 0.18]
            return [self.repo.fragmentos[i] for _,i in resultados[:k]]
        tokens = _palabras(pregunta)
        resultados = sorted(permitidos,
                           key=lambda i: len(tokens & _palabras(self.repo.fragmentos[i].titulo + " " + self.repo.fragmentos[i].texto)), reverse=True)
        return [self.repo.fragmentos[i] for i in resultados[:k] if len(tokens & _palabras(self.repo.fragmentos[i].titulo + " " + self.repo.fragmentos[i].texto)) > 0]

    def recordar_semantico(self, recuerdos: list[dict], pregunta: str, k: int = 3) -> list[dict]:
        if not recuerdos: return []
        if not self.semantico:
            return recuerdos[:k]
        q = self.modelo.encode([pregunta], convert_to_numpy=True).astype("float32")
        vs = self.modelo.encode([x["resumen"] for x in recuerdos], convert_to_numpy=True).astype("float32")
        self.faiss.normalize_L2(q)
        self.faiss.normalize_L2(vs)
        sim = (vs @ q[0]).tolist()
        return [recuerdos[i] for i in sorted(range(len(sim)),key=lambda i: sim[i],reverse=True)[:k]]

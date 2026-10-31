"""LangGraph: planificación adaptativa -> herramientas -> Groq -> QA -> memoria.

Requiere dependencias de requirements.txt y GROQ_API_KEY para modo real.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sqlite3
from typing import Annotated, TypedDict
from .core import RepositorioDemo, normalizar_id, clasificar_intencion, evaluar_permiso_escritura, referencia_conversacional
from .memoria import MemoriaPersistente
from .recuperacion import Buscador
from .prompts import prompt_sistema


class AgenteINGER:
    def __init__(self, raiz: str | Path, modo: str = "groq"):
        self.raiz = Path(raiz)
        self.repo = RepositorioDemo(self.raiz / "data")
        self.modo = modo
        if modo not in ("groq", "demo"):
            raise ValueError("modo debe ser 'groq' o 'demo'")
        if modo == "groq" and not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("Falta GROQ_API_KEY; configúrela en variable de entorno o secreto de Colab.")
        if modo == "groq" and os.getenv("LANGSMITH_TRACING", "false").lower() == "true" and not os.getenv("LANGSMITH_API_KEY"):
            raise RuntimeError("LANGSMITH_TRACING=true requiere LANGSMITH_API_KEY.")
        self.raiz.joinpath("var").mkdir(exist_ok=True)
        self.memoria = MemoriaPersistente(self.raiz / "var" / "memoria.sqlite")
        self.buscador = Buscador(self.repo, semantico=(modo == "groq"))
        from pydantic import BaseModel, Field
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
        from langgraph.graph import StateGraph, START, END
        from langgraph.graph.message import add_messages
        from langgraph.checkpoint.sqlite import SqliteSaver

        class CasoArgs(BaseModel):
            caso_id: str = Field(description="Código ficticio CASO-001, CASO-002, etc.")

        class ConsultaArgs(BaseModel):
            pregunta: str = Field(description="Consulta que se recupera de la base demo")
            caso_id: str | None = Field(default=None, description="Filtro de ID caso")
            categoria: str | None = Field(default=None, description="Filtrar categoría o None")

        class BorradorArgs(BaseModel):
            hilo: str
            caso_id: str
            contenido: str
            solicitud: str
            rol: str

        @tool("consultar_caso", args_schema=CasoArgs)
        def consultar_caso(caso_id: str) -> str:
            """Consulta registros sintéticos por identificador exacto."""
            datos = [x.como_dict() for x in self.repo.por_caso(caso_id)]
            return json.dumps(datos, ensure_ascii=False)

        @tool("buscar_contexto", args_schema=ConsultaArgs)
        def buscar_contexto(pregunta: str, caso_id: str | None = None, categoria: str | None = None) -> str:
            """Realiza recuperación híbrida: filtros exactos y FAISS semántico."""
            return json.dumps([x.como_dict() for x in self.buscador.buscar(pregunta, caso_id, categoria, k=5)], ensure_ascii=False)

        @tool("evaluar_reglas", args_schema=CasoArgs)
        def evaluar_reglas(caso_id: str) -> str:
            """Evalúa solo reglas administrativas simuladas; no clasificación clínica."""
            return json.dumps(self.repo.evaluacion_administrativa(caso_id), ensure_ascii=False)

        @tool("guardar_borrador", args_schema=BorradorArgs)
        def guardar_borrador(hilo: str, caso_id: str, contenido: str, solicitud: str, rol: str) -> str:
            """Guarda un borrador local separado. Exige rol y orden explícita."""
            permitido, motivo = evaluar_permiso_escritura(rol, solicitud)
            if not permitido:
                return json.dumps({"permitido":False,"mensaje":motivo}, ensure_ascii=False)
            if caso_id not in self.repo.casos:
                return json.dumps({"permitido":False,"mensaje":"Caso no encontrado"}, ensure_ascii=False)
            resultado = self.memoria.guardar_borrador(hilo, caso_id, contenido, solicitud)
            return json.dumps({"permitido":True, **resultado}, ensure_ascii=False)

        self.herramientas = {t.name:t for t in (consultar_caso,buscar_contexto,evaluar_reglas,guardar_borrador)}

        if modo == "groq":
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), max_retries=2)
        else:
            self.llm = None

        class Estado(TypedDict, total=False):
            messages: Annotated[list[BaseMessage], add_messages]
            pregunta: str
            hilo: str
            rol: str
            caso_id: str | None
            intencion: str
            plan: list[str]
            evidencia: list[dict]
            memorias: list[dict]
            reglas: list[dict]
            respuesta: str
            escritura: dict | None

        def planificar(s: Estado) -> dict:
            pregunta = s["pregunta"]
            caso_id = normalizar_id(pregunta)
            intencion = clasificar_intencion(pregunta)
            if caso_id is None and referencia_conversacional(pregunta):
                for rec in self.memoria.recuerdos(s["hilo"], limite=8):
                    if rec["caso_id"]:
                        caso_id = rec["caso_id"]
                        break
            plan = ["Identificar tarea y permisos", "Recuperar evidencias", "Aplicar reglas simuladas si corresponde",
                    "Generar respuesta fundamentada", "Controlar salida", "Guardar memoria"]
            if intencion == "borrador": plan.insert(4,"Guardar borrador con permiso")
            return {"caso_id":caso_id, "intencion":intencion,"plan":plan,"evidencia":[],"reglas":[],
                    "escritura":None,"respuesta":""}

        def recuperar_casos(s: Estado) -> dict:
            cid = s.get("caso_id")
            if cid:
                # Ejecuta herramienta Pydantic formal de consulta exacta.
                evidencias = json.loads(self.herramientas["consultar_caso"].invoke({"caso_id":cid}))
            elif s["intencion"] == "priorizacion":
                evidencias = [f.como_dict() for f in self.repo.fragmentos if f.caso_id]
            else:
                evidencias = json.loads(self.herramientas["buscar_contexto"].invoke(
                    {"pregunta":s["pregunta"],"caso_id":None,"categoria":None}))
            reglas=[]
            if s["intencion"] == "priorizacion":
                ids = [cid] if cid else sorted(self.repo.casos)
                reglas=[json.loads(self.herramientas["evaluar_reglas"].invoke({"caso_id":x})) for x in ids]
            recuerdos = self.buscador.recordar_semantico(self.memoria.recuerdos(s["hilo"]), s["pregunta"])
            return {"evidencia":evidencias[:16], "reglas":reglas,"memorias":recuerdos}

        def recuperar_normas(s: Estado) -> dict:
            evidencias = json.loads(self.herramientas["buscar_contexto"].invoke(
                {"pregunta":s["pregunta"],"caso_id":None,"categoria":"normativa_demo"}))
            return {"evidencia":evidencias,"memorias":self.memoria.recuerdos(s["hilo"],3)}

        def generar(s: Estado) -> dict:
            if not s.get("evidencia"):
                resp = "No existen antecedentes suficientes en las fuentes consultadas."
            else:
                memoria = s.get("memorias", [])
                payload = {"consulta":s["pregunta"],"caso_id":s.get("caso_id"),
                           "evidencia":s["evidencia"],"reglas_administrativas_simuladas":s.get("reglas",[]),
                           "memorias_anteriores":memoria[:3]}
                if self.modo == "demo":
                    fuentes = ", ".join(sorted({x["fuente_id"] for x in s["evidencia"]}))
                    resp = (f"DEMOSTRACIÓN SIN GROQ API | {s['intencion']} | "
                            f"Caso: {s.get('caso_id') or 'consulta general'}. "
                            f"Se recuperaron {len(s['evidencia'])} fragmentos. Fuentes: {fuentes}. ")
                    if s.get("reglas"): resp += "Reglas simuladas: " + json.dumps(s["reglas"],ensure_ascii=False)
                else:
                    llm_answer = self.llm.invoke([
                        SystemMessage(content=prompt_sistema(s["intencion"])),
                        HumanMessage(content=json.dumps(payload, ensure_ascii=False))
                    ])
                    resp = str(llm_answer.content)
            return {"respuesta":resp,"messages":[AIMessage(content=resp)]}

        def escribir(s: Estado) -> dict:
            if not s.get("caso_id"):
                return {"escritura":{"permitido":False,"mensaje":"Especifique un ID CASO-NNN para guardar borrador."}}
            resultado = json.loads(self.herramientas["guardar_borrador"].invoke({
                "hilo":s["hilo"],"caso_id":s["caso_id"],"contenido":s["respuesta"],
                "solicitud":s["pregunta"],"rol":s["rol"]}))
            return {"escritura":resultado}

        def verificar(s: Estado) -> dict:
            r = s["respuesta"]
            fuentes = sorted({x["fuente_id"] for x in s.get("evidencia",[])})
            r += "\n\nFuentes recuperadas (verificar correspondencia): " + (", ".join(fuentes) if fuentes else "Ninguna")
            if s.get("escritura") is not None:
                r += "\nResultado de escritura controlada: " + json.dumps(s["escritura"],ensure_ascii=False)
            r += "\nAviso: datos ficticios; requiere validación humana; no implica decisión clínica."
            return {"respuesta":r}

        def memorizar(s: Estado) -> dict:
            self.memoria.recordar(s["hilo"],s.get("caso_id"),s["intencion"],
                f"Intención={s['intencion']}; caso={s.get('caso_id')}; fuentes="+
                ",".join(x["fuente_id"] for x in s.get("evidencia",[])[:6]))
            return {}

        g=StateGraph(Estado)
        g.add_node("planificar",planificar)
        g.add_node("consultar_registros",recuperar_casos)
        g.add_node("consultar_documentos",recuperar_normas)
        g.add_node("generar_con_groq",generar)
        g.add_node("escribir_borrador",escribir)
        g.add_node("verificar_y_citar",verificar)
        g.add_node("guardar_memoria",memorizar)
        g.add_edge(START,"planificar")
        g.add_conditional_edges("planificar",lambda s:"documentos" if s["intencion"] == "normativa" else "casos",
                                {"documentos":"consultar_documentos","casos":"consultar_registros"})
        g.add_edge("consultar_registros","generar_con_groq")
        g.add_edge("consultar_documentos","generar_con_groq")
        g.add_conditional_edges("generar_con_groq",lambda s:"escritura" if s["intencion"] == "borrador" else "salida",
                                {"escritura":"escribir_borrador","salida":"verificar_y_citar"})
        g.add_edge("escribir_borrador","verificar_y_citar")
        g.add_edge("verificar_y_citar","guardar_memoria")
        g.add_edge("guardar_memoria",END)
        self._conn = sqlite3.connect(str(self.raiz / "var" / "grafo.sqlite"), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self.grafo = g.compile(checkpointer=SqliteSaver(self._conn))
        self.HumanMessage = HumanMessage

    def preguntar(self, pregunta: str, hilo: str = "demo-01", rol: str = "lector_demo") -> dict:
        if not pregunta.strip(): raise ValueError("La pregunta no puede estar vacía")
        if not hilo.strip(): raise ValueError("El hilo no puede estar vacío")
        config={"configurable":{"thread_id":hilo},"recursion_limit":16}
        entrada={"pregunta":pregunta,"hilo":hilo,"rol":rol,"messages":[self.HumanMessage(content=pregunta)],
                 "caso_id":None,"intencion":"","plan":[],"evidencia":[],"reglas":[],"memorias":[],
                 "escritura":None,"respuesta":""}
        resultado = self.grafo.invoke(entrada,config=config)
        return {k:resultado.get(k) for k in ("pregunta","caso_id","intencion","plan","respuesta","escritura")}

    def cerrar(self):
        self._conn.close()

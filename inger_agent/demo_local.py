"""Motor offline verificable sin dependencias LangGraph/Groq, SOLO para tests previos."""
from pathlib import Path
from .core import RepositorioDemo,normalizar_id,clasificar_intencion,evaluar_permiso_escritura,referencia_conversacional
from .recuperacion import Buscador
from .memoria import MemoriaPersistente

class DemoLocal:
    def __init__(self, raiz: str | Path):
        self.raiz=Path(raiz)
        self.repo=RepositorioDemo(self.raiz / "data")
        self.buscador=Buscador(self.repo,semantico=False)
        self.memoria=MemoriaPersistente(self.raiz / "var" / "offline.sqlite")

    def preguntar(self, texto: str, hilo: str="offline-01", rol: str="lector_demo") -> dict:
        intencion=clasificar_intencion(texto); cid=normalizar_id(texto)
        if cid is None and referencia_conversacional(texto):
            for rec in self.memoria.recuerdos(hilo, 8):
                if rec["caso_id"]:
                    cid=rec["caso_id"]
                    break
        if intencion == "normativa":
            evidencias=self.buscador.buscar(texto,categoria="normativa_demo")
        elif cid:
            evidencias=self.repo.por_caso(cid)
        elif intencion=="priorizacion":
            evidencias=[f for f in self.repo.fragmentos if f.caso_id]
        else:
            evidencias=self.buscador.buscar(texto)
        reglas = self.repo.evaluacion_general() if intencion == "priorizacion" and not cid else (
            [self.repo.evaluacion_administrativa(cid)] if intencion == "priorizacion" and cid else [])
        resultado_escritura = None
        if intencion == "borrador":
            permitido,motivo=evaluar_permiso_escritura(rol,texto)
            if not cid: permitido,motivo = False, "Especifique CASO-NNN."
            if permitido and cid not in self.repo.casos: permitido,motivo=False,"Caso no encontrado."
            resultado_escritura= self.memoria.guardar_borrador(hilo,cid,"BORRADOR FICTICIO - sin contenido clínico",texto) if permitido else {"permitido":False,"mensaje":motivo}
        respuesta = (f"DEMO OFFLINE SIN GROQ/LANGSMITH · Ruta {intencion}. "
                     + (f"Se recuperaron {len(evidencias)} fragmentos." if evidencias else "No existen antecedentes suficientes en las fuentes consultadas."))
        if reglas: respuesta += " Reglas simuladas: " + str(reglas)
        respuesta += " Fuentes: " + ", ".join(f.fuente_id for f in evidencias)
        self.memoria.recordar(hilo,cid,intencion,respuesta)
        return {"pregunta":texto,"caso_id":cid,"intencion":intencion,
                "fuentes":[f.fuente_id for f in evidencias],"reglas":reglas,
                "respuesta":respuesta,"escritura":resultado_escritura}

"""CLI para demostrar secuencias adaptativas en video o Colab."""
from __future__ import annotations
import argparse
from pathlib import Path
import os

RAIZ = Path(__file__).resolve().parent

def iniciar(modo="groq"):
    if modo == "offline":
        from inger_agent.demo_local import DemoLocal
        return DemoLocal(RAIZ)
    from inger_agent.grafo import AgenteINGER
    return AgenteINGER(RAIZ, modo=modo)


def main():
    ap=argparse.ArgumentParser(description="Agente ficticio INGER (no procesa pacientes reales)")
    ap.add_argument("--modo",choices=["groq","demo","offline"],default="offline")
    ap.add_argument("--hilo",default="demo-inger-01")
    ap.add_argument("--rol",choices=["lector_demo","gestor_demo"],default="lector_demo")
    ap.add_argument("--escenarios",action="store_true",help="Ejecución guiada para el video")
    ap.add_argument("--pregunta",default=None)
    args=ap.parse_args()
    agente=iniciar(args.modo)
    if args.escenarios:
        preguntas=[
            "Resume las gestiones e interconsulta del CASO-001",
            "¿Y sus pendientes?",
            "¿Qué casos requieren revisión administrativa según las reglas simuladas?",
            "¿Qué dice el procedimiento simulado sobre trazabilidad?",
            "Guarda borrador de seguimiento para CASO-001"
        ]
    elif args.pregunta:
        preguntas=[args.pregunta]
    else:
        print("Escriba 'salir' para terminar.")
        preguntas=None
    try:
        if preguntas is not None:
            for i,p in enumerate(preguntas,1):
                print(f"\n{'='*18} ESCENARIO {i} {'='*18}\nCONSULTA: {p}")
                r=agente.preguntar(p,hilo=args.hilo,rol=args.rol)
                print("RUTA:",r["intencion"],"\nRESPUESTA:\n",r["respuesta"])
                if r.get("escritura") is not None: print("ESCRITURA:",r["escritura"])
        else:
            while True:
                p=input("\nConsulta> ").strip()
                if p.lower() in ("salir","exit","q"):break
                r=agente.preguntar(p,hilo=args.hilo,rol=args.rol)
                print(r["respuesta"])
    finally:
        if hasattr(agente,"cerrar"): agente.cerrar()

if __name__ == "__main__": main()

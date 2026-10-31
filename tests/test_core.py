"""Pruebas completamente locales: no necesitan claves, Groq ni LangSmith."""
import sys
import tempfile
import shutil
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from inger_agent.core import normalizar_id,clasificar_intencion,RepositorioDemo,evaluar_permiso_escritura
from inger_agent.recuperacion import Buscador
from inger_agent.memoria import MemoriaPersistente
from inger_agent.demo_local import DemoLocal

class PruebaDominio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo=RepositorioDemo(RAIZ/'data')

    def test_id_normalizado(self):
        self.assertEqual(normalizar_id('Consulta caso-001'), 'CASO-001')
        self.assertIsNone(normalizar_id('¿Qué pacientes?'))

    def test_planificacion_adaptativa(self):
        self.assertEqual(clasificar_intencion('¿Qué pendientes tiene CASO-001?'),'pendientes')
        self.assertEqual(clasificar_intencion('¿Qué establece el procedimiento?'),'normativa')
        self.assertEqual(clasificar_intencion('Guarda borrador para CASO-001'),'borrador')
        self.assertEqual(clasificar_intencion('Prioriza los casos'),'priorizacion')

    def test_regla_activada_pendiente(self):
        r=self.repo.evaluacion_administrativa('CASO-001')
        self.assertEqual(r['estado'],'revision_administrativa_sugerida')
        self.assertEqual({x['id'] for x in r['reglas_activadas']},{'R1','R2','R3'})

    def test_caso_sin_reglas_activadas(self):
        r=self.repo.evaluacion_administrativa('CASO-002')
        self.assertEqual(r['estado'],'sin_criterios_activados')

    def test_ausencia_no_equivale_pendiente(self):
        r=self.repo.evaluacion_administrativa('CASO-003')
        self.assertEqual(r['estado'],'sin_criterios_activados')

    def test_retrieval_solo_caso_solicitado(self):
        r=Buscador(self.repo,semantico=False)
        docs=r.buscar('traslado CASO-001',caso_id='CASO-001')
        self.assertEqual(len(docs),2)
        self.assertTrue(all(x.caso_id=='CASO-001' for x in docs))

    def test_recuperacion_documental_con_filtro(self):
        r=Buscador(self.repo,semantico=False)
        docs=r.buscar('tarea trazabilidad fuente',categoria='normativa_demo')
        self.assertTrue(len(docs)>=1)
        self.assertTrue(all(x.categoria=='normativa_demo' for x in docs))

    def test_control_de_acceso(self):
        self.assertFalse(evaluar_permiso_escritura('lector_demo','Guarda borrador CASO-001')[0])
        self.assertFalse(evaluar_permiso_escritura('gestor_demo','Dame resumen CASO-001')[0])
        self.assertTrue(evaluar_permiso_escritura('gestor_demo','Guarda borrador CASO-001')[0])

class PruebaPersistencia(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Path(self.temp.name)/'estado.sqlite'
        self.store=MemoriaPersistente(self.db)

    def tearDown(self): self.temp.cleanup()

    def test_memoria_multiturno_persistente(self):
        self.store.recordar('h1','CASO-001','sintesis','Consulta de prueba')
        reabierto=MemoriaPersistente(self.db)
        self.assertEqual(reabierto.recuerdos('h1')[0]['resumen'],'Consulta de prueba')
        self.assertEqual(reabierto.recuerdos('h2'),[])

    def test_borrador_idempotente_y_separado(self):
        a=self.store.guardar_borrador('h1','CASO-001','borrador','Guarda borrador')
        b=self.store.guardar_borrador('h1','CASO-001','borrador','Guarda borrador')
        self.assertEqual(a['borrador_id'],b['borrador_id'])
        self.assertEqual(len(self.store.borradores('h1')),1)

    def test_flujo_offline_multiturno(self):
        with tempfile.TemporaryDirectory() as d:
            raiz=Path(d)
            shutil.copytree(RAIZ/'data',raiz/'data')
            agent=DemoLocal(raiz)
            r1=agent.preguntar('Resume CASO-001',hilo='test')
            r2=agent.preguntar('¿Y sus pendientes?',hilo='test')
            self.assertEqual(r1['intencion'],'sintesis')
            self.assertEqual(r2['intencion'],'pendientes')
            self.assertEqual(r2['caso_id'],'CASO-001')
            self.assertEqual(len(agent.memoria.recuerdos('test')),2)
            r3=agent.preguntar('Guarda borrador CASO-001',hilo='test',rol='lector_demo')
            self.assertFalse(r3['escritura']['permitido'])
            r4=agent.preguntar('Guarda borrador CASO-001',hilo='test',rol='gestor_demo')
            self.assertIn('borrador_id',r4['escritura'])

if __name__=='__main__': unittest.main()

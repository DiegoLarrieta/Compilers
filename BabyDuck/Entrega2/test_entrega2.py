"""
test_entrega2.py - Pruebas del cubo semántico, del directorio de funciones y
de las validaciones semánticas de variables.

Se corre desde esta carpeta con:
    python -m unittest -v
"""

import glob
import os
import unittest

from cubo_semantico import (BOOL, CUBO, ERROR, FLOAT, INT, TIPOS,
                            tipo_resultante)
from directorio import DirectorioFunciones
from errores import ErrorBabyDuck, ErrorSemantico
from parser import analizar

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programas")


def leer(nombre):
    with open(os.path.join(CARPETA, nombre), encoding="utf-8") as archivo:
        return archivo.read()


class PruebasCubo(unittest.TestCase):
    def test_aritmeticos(self):
        for operador in ("+", "-", "*", "/"):
            with self.subTest(operador=operador):
                self.assertEqual(tipo_resultante(operador, INT, INT), INT)
                self.assertEqual(tipo_resultante(operador, INT, FLOAT), FLOAT)
                self.assertEqual(tipo_resultante(operador, FLOAT, INT), FLOAT)
                self.assertEqual(tipo_resultante(operador, FLOAT, FLOAT), FLOAT)

    def test_relacionales_regresan_bool(self):
        for operador in (">", "<", "!="):
            for izq in (INT, FLOAT):
                for der in (INT, FLOAT):
                    with self.subTest(operador=operador, izq=izq, der=der):
                        self.assertEqual(tipo_resultante(operador, izq, der), BOOL)

    def test_asignacion(self):
        self.assertEqual(tipo_resultante("=", INT, INT), INT)
        self.assertEqual(tipo_resultante("=", FLOAT, FLOAT), FLOAT)
        self.assertEqual(tipo_resultante("=", FLOAT, INT), FLOAT)   # int se promueve
        self.assertEqual(tipo_resultante("=", INT, FLOAT), ERROR)   # se perdería info

    def test_bool_no_se_puede_operar(self):
        for operador in CUBO:
            for otro in TIPOS:
                with self.subTest(operador=operador, otro=otro):
                    self.assertEqual(tipo_resultante(operador, BOOL, otro), ERROR)
                    self.assertEqual(tipo_resultante(operador, otro, BOOL), ERROR)

    def test_cubo_completo(self):
        """Todos los operadores tienen las 9 combinaciones de tipos."""
        self.assertEqual(set(CUBO), {"+", "-", "*", "/", ">", "<", "!=", "="})
        for operador in CUBO:
            for izq in TIPOS:
                self.assertEqual(set(CUBO[operador][izq]), set(TIPOS))


class PruebasDirectorio(unittest.TestCase):
    """Prueba la estructura de datos por separado, sin pasar por el parser."""

    def setUp(self):
        self.directorio = DirectorioFunciones()
        self.directorio.crear_programa("p")

    def test_variable_global(self):
        self.directorio.agregar_variable("a", INT)
        self.assertEqual(self.directorio.buscar_variable("a").tipo, INT)

    def test_variable_duplicada(self):
        self.directorio.agregar_variable("a", INT)
        with self.assertRaises(ErrorSemantico):
            self.directorio.agregar_variable("a", FLOAT)

    def test_local_tapa_a_global(self):
        self.directorio.agregar_variable("a", INT)
        self.directorio.crear_funcion("f")
        self.directorio.agregar_variable("a", FLOAT)
        self.assertEqual(self.directorio.buscar_variable("a").tipo, FLOAT)
        self.directorio.cerrar_funcion()
        self.assertEqual(self.directorio.buscar_variable("a").tipo, INT)

    def test_local_no_se_ve_desde_fuera(self):
        self.directorio.crear_funcion("f")
        self.directorio.agregar_variable("local", INT)
        self.directorio.cerrar_funcion()
        with self.assertRaises(ErrorSemantico):
            self.directorio.buscar_variable("local")

    def test_parametros_guardan_orden(self):
        self.directorio.crear_funcion("f")
        self.directorio.agregar_variable("x", INT, es_parametro=True)
        self.directorio.agregar_variable("y", FLOAT, es_parametro=True)
        funcion = self.directorio.buscar_funcion("f")
        self.assertEqual(funcion.parametros, [INT, FLOAT])
        self.assertTrue(funcion.variables.buscar("x").es_parametro)

    def test_funcion_duplicada(self):
        self.directorio.crear_funcion("f")
        self.directorio.cerrar_funcion()
        with self.assertRaises(ErrorSemantico):
            self.directorio.crear_funcion("f")

    def test_funcion_con_nombre_del_programa(self):
        with self.assertRaises(ErrorSemantico):
            self.directorio.crear_funcion("p")

    def test_programa_no_es_funcion_llamable(self):
        with self.assertRaises(ErrorSemantico):
            self.directorio.buscar_funcion("p")


class PruebasSemanticaConParser(unittest.TestCase):
    def test_directorio_de_alcances(self):
        directorio = analizar(leer("alcances.bd"))
        self.assertEqual(list(directorio.funciones), ["alcances", "acumula", "reporta"])

        globales = directorio.funciones["alcances"].variables
        self.assertEqual(
            [(v.nombre, v.tipo) for v in globales],
            [("total", INT), ("contador", INT), ("promedio", FLOAT)],
        )

        acumula = directorio.funciones["acumula"]
        self.assertEqual(acumula.parametros, [INT, FLOAT])
        self.assertEqual(
            [(v.nombre, v.tipo, v.es_parametro) for v in acumula.variables],
            [("valor", INT, True), ("peso", FLOAT, True),
             ("total", FLOAT, False), ("temporal", INT, False)],
        )
        self.assertEqual(len(directorio.funciones["reporta"].variables), 0)

    def test_al_terminar_el_alcance_es_global(self):
        directorio = analizar(leer("factorial.bd"))
        self.assertEqual(directorio.alcance_actual, "factorial")

    def test_cada_compilacion_empieza_limpia(self):
        analizar("program uno; var a : int; main { } end")
        directorio = analizar("program dos; var b : int; main { } end")
        self.assertEqual(list(directorio.funciones), ["dos"])

    def assertErrorSemantico(self, codigo, fragmento, linea=None):
        with self.assertRaises(ErrorSemantico) as contexto:
            analizar(codigo)
        self.assertIn(fragmento, str(contexto.exception))
        if linea is not None:
            self.assertEqual(contexto.exception.linea, linea)

    def test_archivos_con_error(self):
        self.assertErrorSemantico(leer("error_variable_duplicada.bd"), "'a' ya fue declarada", 3)
        self.assertErrorSemantico(leer("error_variable_no_declarada.bd"), "'b' no ha sido declarada", 4)
        self.assertErrorSemantico(leer("error_funcion_duplicada.bd"), "'f' ya fue declarada", 3)
        self.assertErrorSemantico(leer("error_funcion_no_declarada.bd"), "'calcula' no ha sido declarada", 4)
        self.assertErrorSemantico(leer("error_parametro_duplicado.bd"), "'x' ya fue declarada", 3)

    def test_duplicada_en_la_misma_lista(self):
        self.assertErrorSemantico("program p; var a, a : int; main { } end", "'a' ya fue declarada")

    def test_dos_parametros_iguales(self):
        self.assertErrorSemantico(
            "program p; void f(x : int, x : int) [ { } ]; main { } end", "'x' ya fue declarada"
        )

    def test_asignar_a_no_declarada(self):
        self.assertErrorSemantico("program p; main {\n x = 1;\n} end", "'x' no ha sido declarada", 2)

    def test_local_usada_en_main(self):
        codigo = "program p; void f() [ var t : int; { t = 1; } ]; main { t = 2; } end"
        self.assertErrorSemantico(codigo, "'t' no ha sido declarada")

    def test_local_de_otra_funcion(self):
        codigo = ("program p; void f() [ var t : int; { } ]; "
                  "void g() [ { t = 2; } ]; main { } end")
        self.assertErrorSemantico(codigo, "'t' no ha sido declarada")

    def test_llamar_funcion_declarada_despues(self):
        codigo = "program p; void f() [ { g(); } ]; void g() [ { } ]; main { } end"
        self.assertErrorSemantico(codigo, "'g' no ha sido declarada")

    def test_funcion_recursiva_si_se_permite(self):
        analizar("program p; void f(n : int) [ { f(n - 1); } ]; main { f(3); } end")

    def test_mismo_nombre_en_funciones_distintas(self):
        analizar("program p; void f(x : int) [ { } ]; void g(x : float) [ { } ]; main { } end")

    def test_variable_usada_en_print_if_while(self):
        for cuerpo in ("print(z);", "if (z > 1) { };", "while (z < 1) do { };", "f(z);"):
            with self.subTest(cuerpo=cuerpo):
                codigo = f"program p; void f(n : int) [ {{ }} ]; main {{ {cuerpo} }} end"
                self.assertErrorSemantico(codigo, "'z' no ha sido declarada")


class PruebasArchivos(unittest.TestCase):
    def test_todos_los_archivos_estan_clasificados(self):
        for ruta in sorted(glob.glob(os.path.join(CARPETA, "*.bd"))):
            nombre = os.path.basename(ruta)
            with self.subTest(archivo=nombre):
                if nombre.startswith("error_"):
                    with self.assertRaises(ErrorBabyDuck):
                        analizar(leer(nombre))
                else:
                    analizar(leer(nombre))


if __name__ == "__main__":
    unittest.main()

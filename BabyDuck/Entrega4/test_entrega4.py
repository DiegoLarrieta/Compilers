"""
test_entrega4.py - Pruebas de direcciones virtuales, estatutos no lineales y funciones.

Se corre desde esta carpeta con:
    python -m unittest -v
"""

import os
import unittest

from cubo_semantico import BOOL, FLOAT, INT
from errores import ErrorSemantico
from estructuras import Fila
from memoria import (BASES, CONSTANTE, GLOBAL, LETRERO, LOCAL, TAMANO, TEMPORAL,
                     MemoriaVirtual, Segmento, segmento_y_tipo)
from parser import analizar

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programas")
VARIABLES = "var a, b, c, d : int; x, y : float;"


def leer(nombre):
    with open(os.path.join(CARPETA, nombre), encoding="utf-8") as archivo:
        return archivo.read()


def compilar(codigo):
    compilacion = analizar(codigo)
    assert compilacion.generador.pilas_vacias(), "quedaron elementos en las pilas"
    return compilacion


def legibles(codigo):
    """Todos los cuádruplos del programa, con nombres."""
    return [c.como_tupla_legible() for c in compilar(codigo).cuadruplos]


def con_direcciones(codigo):
    """Todos los cuádruplos del programa, con direcciones."""
    return [c.como_tupla() for c in compilar(codigo).cuadruplos]


def main(cuerpo, extra=""):
    return legibles(f"program p; {VARIABLES} {extra} main {{ {cuerpo} }} end")


# ---------------------------------------------------------------------------
# Memoria virtual
# ---------------------------------------------------------------------------
class PruebasMemoria(unittest.TestCase):
    def test_rangos_no_se_enciman(self):
        rangos = sorted(BASES.values())
        for anterior, siguiente in zip(rangos, rangos[1:]):
            self.assertGreaterEqual(siguiente, anterior + TAMANO)

    def test_segmento_y_tipo_de_una_direccion(self):
        self.assertEqual(segmento_y_tipo(1000), (GLOBAL, INT))
        self.assertEqual(segmento_y_tipo(2999), (GLOBAL, FLOAT))
        self.assertEqual(segmento_y_tipo(3005), (LOCAL, INT))
        self.assertEqual(segmento_y_tipo(7000), (TEMPORAL, BOOL))
        self.assertEqual(segmento_y_tipo(10000), (CONSTANTE, LETRERO))
        with self.assertRaises(ValueError):
            segmento_y_tipo(999)

    def test_segmento_reparte_en_orden_por_tipo(self):
        segmento = Segmento(TEMPORAL)
        self.assertEqual([segmento.asignar(INT), segmento.asignar(FLOAT),
                          segmento.asignar(INT), segmento.asignar(BOOL)],
                         [5000, 6000, 5001, 7000])
        self.assertEqual(segmento.conteo(), {INT: 2, FLOAT: 1, BOOL: 1})

    def test_segmento_lleno(self):
        segmento = Segmento(GLOBAL)
        for _ in range(TAMANO):
            segmento.asignar(INT)
        with self.assertRaises(ErrorSemantico):
            segmento.asignar(INT)

    def test_constante_repetida_usa_la_misma_direccion(self):
        memoria = MemoriaVirtual()
        self.assertEqual(memoria.constante(5, INT), 8000)
        self.assertEqual(memoria.constante(7, INT), 8001)
        self.assertEqual(memoria.constante(5, INT), 8000)
        self.assertEqual(memoria.constante(5.0, FLOAT), 9000)
        self.assertEqual(memoria.constante("hola", LETRERO), 10000)
        self.assertEqual(memoria.valor_de_constante(8001), 7)


class PruebasDirecciones(unittest.TestCase):
    def test_globales_por_tipo(self):
        directorio = compilar(f"program p; {VARIABLES} main {{ }} end").directorio
        tabla = directorio.funciones["p"].variables
        self.assertEqual([(v.nombre, v.direccion) for v in tabla],
                         [("a", 1000), ("b", 1001), ("c", 1002), ("d", 1003),
                          ("x", 2000), ("y", 2001)])

    def test_locales_y_parametros_empiezan_en_cada_funcion(self):
        codigo = ("program p; var g : int; "
                  "void f(n : int, r : float) [ var i : int; { } ]; "
                  "void h(m : int) [ { } ]; main { } end")
        funciones = compilar(codigo).directorio.funciones
        self.assertEqual([(v.nombre, v.direccion) for v in funciones["f"].variables],
                         [("n", 3000), ("r", 4000), ("i", 3001)])
        self.assertEqual(funciones["f"].direcciones_parametros, [3000, 4000])
        self.assertEqual([(v.nombre, v.direccion) for v in funciones["h"].variables], [("m", 3000)])
        self.assertEqual(funciones["p"].variables.buscar("g").direccion, 1000)

    def test_cuadruplo_con_direcciones(self):
        cuadruplos = con_direcciones(f"program p; {VARIABLES} main {{ x = a + y * 2; }} end")
        self.assertEqual(cuadruplos[1:4], [
            ("*", 2001, 8000, 6000),     # y (float global) * 2 (constante int) -> temporal float
            ("+", 1000, 6000, 6001),     # a + t1 -> temporal float
            ("=", 6001, None, 2000),     # x = t2
        ])

    def test_temporal_segun_su_tipo(self):
        cuadruplos = con_direcciones(
            f"program p; {VARIABLES} main {{ a = b + c; y = x / 2.0; print(a > b); }} end")
        resultados = [c[3] for c in cuadruplos if c[0] in ("+", "/", ">")]
        self.assertEqual(resultados, [5000, 6000, 7000])

    def test_letreros_son_constantes(self):
        cuadruplos = con_direcciones('program p; main { print("hola", "hola", "adiós"); } end')
        self.assertEqual([c[3] for c in cuadruplos if c[0] == "print"], [10000, 10000, 10001])

    def test_negativo_de_constante(self):
        compilacion = compilar(f"program p; {VARIABLES} main {{ a = -3; }} end")
        asignacion = compilacion.cuadruplos[1]
        self.assertEqual(compilacion.memoria.valor_de_constante(asignacion.izquierdo), -3)

    def test_temporales_se_reinician_en_cada_alcance(self):
        codigo = ("program p; var g : int; void f() [ { g = g + 1; } ]; "
                  "main { g = g * 2; } end")
        cuadruplos = con_direcciones(codigo)
        self.assertEqual(cuadruplos[1], ("+", 1000, 8000, 5000))   # en f
        self.assertEqual(cuadruplos[4], ("*", 1000, 8001, 5000))   # en main, otra vez 5000

    def test_recursos_para_era(self):
        codigo = ("program p; var g : int; "
                  "void f(n : int, r : float) [ var i : int; { i = n + 1; r = r * 2.0; "
                  "if (i > 2) { }; } ]; main { } end")
        funcion = compilar(codigo).directorio.funciones["f"]
        self.assertEqual(funcion.recursos[LOCAL], {INT: 2, FLOAT: 1})
        self.assertEqual(funcion.recursos[TEMPORAL], {INT: 1, FLOAT: 1, BOOL: 1})


# ---------------------------------------------------------------------------
# Estatutos condicionales y cíclicos
# ---------------------------------------------------------------------------
class PruebasSaltos(unittest.TestCase):
    def test_fila_se_puede_rellenar_por_posicion(self):
        fila = Fila()
        for elemento in ("a", "b", "c"):
            fila.encolar(elemento)
        self.assertEqual(fila[1], "b")
        fila.desencolar()
        self.assertEqual(fila[0], "b")
        with self.assertRaises(IndexError):
            fila[5]

    def test_programa_empieza_con_goto_a_main(self):
        self.assertEqual(main(""), [("GOTO", None, None, 2), ("END", None, None, None)])

    def test_if_sin_else(self):
        self.assertEqual(main("if (a > b) { a = b; }; c = 1;"), [
            ("GOTO", None, None, 2),
            (">", "a", "b", "t1"),
            ("GOTOF", "t1", None, 5),         # si es falso, brinca el cuerpo
            ("=", "b", None, "a"),
            ("=", 1, None, "c"),               # 5
            ("END", None, None, None),
        ])

    def test_if_con_else(self):
        self.assertEqual(main("if (a > b) { a = b; } else { b = a; }; c = 1;"), [
            ("GOTO", None, None, 2),
            (">", "a", "b", "t1"),
            ("GOTOF", "t1", None, 6),          # falso -> inicio del else
            ("=", "b", None, "a"),
            ("GOTO", None, None, 7),           # fin del bloque verdadero -> después del if
            ("=", "a", None, "b"),             # 6
            ("=", 1, None, "c"),               # 7
            ("END", None, None, None),
        ])

    def test_while(self):
        self.assertEqual(main("while (a < 10) do { a = a + 1; }; b = a;"), [
            ("GOTO", None, None, 2),
            ("<", "a", 10, "t1"),              # 2: aquí regresa cada vuelta
            ("GOTOF", "t1", None, 7),
            ("+", "a", 1, "t2"),
            ("=", "t2", None, "a"),
            ("GOTO", None, None, 2),
            ("=", "a", None, "b"),             # 7
            ("END", None, None, None),
        ])

    def test_while_vacio(self):
        self.assertEqual(main("while (a < 1) do { };"), [
            ("GOTO", None, None, 2), ("<", "a", 1, "t1"), ("GOTOF", "t1", None, 5),
            ("GOTO", None, None, 2), ("END", None, None, None)])

    def test_anidados(self):
        self.assertEqual(main(
            "while (a < 3) do { if (b > 0) { b = b - 1; } else { c = c + 1; }; a = a + 1; };"), [
            ("GOTO", None, None, 2),
            ("<", "a", 3, "t1"),               # 2: regreso del while
            ("GOTOF", "t1", None, 14),         # sale del while
            (">", "b", 0, "t2"),
            ("GOTOF", "t2", None, 9),          # al else
            ("-", "b", 1, "t3"),
            ("=", "t3", None, "b"),
            ("GOTO", None, None, 11),          # brinca el else
            ("+", "c", 1, "t4"),               # 9: else
            ("=", "t4", None, "c"),
            ("+", "a", 1, "t5"),               # 11: después del if
            ("=", "t5", None, "a"),
            ("GOTO", None, None, 2),
            ("END", None, None, None),         # 14
        ])

    def test_ningun_salto_queda_pendiente(self):
        for nombre in ("ciclos.bd", "factorial.bd", "funciones.bd"):
            with self.subTest(archivo=nombre):
                for cuadruplo in compilar(leer(nombre)).cuadruplos:
                    if cuadruplo.operador in ("GOTO", "GOTOF", "GOSUB"):
                        self.assertIsInstance(cuadruplo.resultado, int)

    def test_condicion_no_bool(self):
        for cuerpo, fragmento in (("if (a) { };", "la condición del if"),
                                  ("while (a + 1) do { };", "la condición del while")):
            with self.subTest(cuerpo=cuerpo):
                with self.assertRaises(ErrorSemantico) as contexto:
                    main(cuerpo)
                self.assertIn(fragmento, str(contexto.exception))


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------
class PruebasFunciones(unittest.TestCase):
    def test_declaracion_inicio_y_endfunc(self):
        compilacion = compilar(
            "program p; var g : int; void f(n : int) [ { g = n; } ]; main { f(1); } end")
        self.assertEqual(compilacion.directorio.funciones["f"].inicio, 2)
        self.assertEqual([c.como_tupla_legible() for c in compilacion.cuadruplos], [
            ("GOTO", None, None, 4),
            ("=", "n", None, "g"),             # 2: inicio de f
            ("ENDFUNC", None, None, None),
            ("ERA", None, None, "f"),          # 4: inicio de main
            ("PARAM", 1, None, "n"),
            ("GOSUB", "f", None, 2),
            ("END", None, None, None),
        ])

    def test_param_usa_la_direccion_del_parametro(self):
        cuadruplos = con_direcciones(
            "program p; var a : int; void f(n : int, r : float) [ { } ]; "
            "main { f(a, 2.5); } end")
        self.assertIn(("PARAM", 1000, None, 3000), cuadruplos)
        self.assertIn(("PARAM", 9000, None, 4000), cuadruplos)

    def test_argumentos_con_expresiones(self):
        # 1: GOTO, 2: ENDFUNC de f (cuerpo vacío), 3 en adelante: main
        self.assertEqual(main("f(a + b * 2);", extra="void f(n : int) [ { } ];")[2:7], [
            ("ERA", None, None, "f"),
            ("*", "b", 2, "t1"),
            ("+", "a", "t1", "t2"),
            ("PARAM", "t2", None, "n"),
            ("GOSUB", "f", None, 2),
        ])

    def test_sin_parametros(self):
        self.assertEqual(main("f();", extra="void f() [ { } ];")[2:4],
                         [("ERA", None, None, "f"), ("GOSUB", "f", None, 2)])

    def test_recursion(self):
        compilacion = compilar(leer("funciones.bd"))
        inicio = compilacion.directorio.funciones["cuenta"].inicio
        self.assertIn(("GOSUB", "cuenta", None, inicio),
                      [c.como_tupla_legible() for c in compilacion.cuadruplos[inicio - 1:]])

    def test_int_se_puede_pasar_a_float(self):
        main("f(a);", extra="void f(r : float) [ { } ];")

    def assertErrorSemantico(self, cuerpo, extra, fragmento):
        with self.assertRaises(ErrorSemantico) as contexto:
            main(cuerpo, extra)
        self.assertIn(fragmento, str(contexto.exception))

    def test_float_no_se_puede_pasar_a_int(self):
        self.assertErrorSemantico("f(x);", "void f(n : int) [ { } ];",
                                  "el argumento 1 de 'f' debe ser int (se recibió float)")

    def test_bool_no_es_argumento(self):
        self.assertErrorSemantico("f(a > b);", "void f(n : int) [ { } ];",
                                  "debe ser int (se recibió bool)")

    def test_numero_de_argumentos(self):
        extra = "void f(n : int, m : int) [ { } ];"
        self.assertErrorSemantico("f(1);", extra, "espera 2 argumentos y recibió 1")
        self.assertErrorSemantico("f(1, 2, 3);", extra, "espera 2 argumentos y recibió 3")
        self.assertErrorSemantico("f();", extra, "espera 2 argumentos y recibió 0")
        self.assertErrorSemantico("g(1);", "void g() [ { } ];", "espera 0 argumentos y recibió 1")

    def test_archivos_con_error(self):
        for nombre, fragmento in (
            ("error_faltan_argumentos.bd", "espera 2 argumentos y recibió 1"),
            ("error_tipo_argumento.bd", "debe ser int (se recibió float)"),
        ):
            with self.subTest(archivo=nombre):
                with self.assertRaises(ErrorSemantico) as contexto:
                    analizar(leer(nombre))
                self.assertIn(fragmento, str(contexto.exception))
                self.assertEqual(contexto.exception.linea, 4)


class PruebasProgramas(unittest.TestCase):
    def test_factorial(self):
        compilacion = compilar(leer("factorial.bd"))
        texto = [c.texto_legible() for c in compilacion.cuadruplos]
        self.assertEqual(texto[0], "(GOTO, _, _, 15)")
        self.assertEqual(texto[5], "(GOTOF, t2, _, 12)")       # sale del while
        self.assertEqual(texto[10], "(GOTO, _, _, 4)")         # regresa a la condición
        self.assertEqual(texto[18:20], ["(PARAM, n, _, limite)", "(GOSUB, calcula, _, 2)"])
        self.assertEqual(texto[-1], "(END, _, _, _)")


if __name__ == "__main__":
    unittest.main()

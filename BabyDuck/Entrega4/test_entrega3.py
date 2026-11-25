"""
test_entrega3.py - Pruebas de las pilas, la fila y la generación de cuádruplos.

Entrega 4: los cuádruplos ahora usan direcciones virtuales. Estas pruebas
comparan la versión LEGIBLE de cada cuádruplo (con nombres), que es la misma
que se comparaba en la entrega 3, y solo miran el código de main (se quitan el
GOTO a main del inicio y el END del final). Las pruebas cuyo resultado cambió
por los saltos y las llamadas dicen "Entrega 4" en su comentario.

Se corre desde esta carpeta con:
    python -m unittest -v
"""

import glob
import os
import unittest

from errores import ErrorBabyDuck, ErrorSemantico
from estructuras import Fila, Pila
from parser import analizar

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programas")

VARIABLES = "var a, b, c, d : int; x, y : float;"


def leer(nombre):
    with open(os.path.join(CARPETA, nombre), encoding="utf-8") as archivo:
        return archivo.read()


def cuadruplos(cuerpo, extra=""):
    """Compila los estatutos dentro de un main y regresa los cuádruplos de main (legibles)."""
    compilacion = analizar(f"program p; {VARIABLES} {extra} main {{ {cuerpo} }} end")
    assert compilacion.generador.pilas_vacias(), "quedaron elementos en las pilas"
    todos = [cuadruplo.como_tupla_legible() for cuadruplo in compilacion.cuadruplos]
    inicio_main = todos[0][3]          # el cuádruplo 1 es (GOTO, _, _, inicio de main)
    return todos[inicio_main - 1:-1]   # sin el END final


class PruebasPila(unittest.TestCase):
    def test_lifo(self):
        pila = Pila()
        for elemento in (1, 2, 3):
            pila.meter(elemento)
        self.assertEqual(pila.tope(), 3)
        self.assertEqual([pila.sacar(), pila.sacar(), pila.sacar()], [3, 2, 1])
        self.assertTrue(pila.esta_vacia())

    def test_tope_no_saca(self):
        pila = Pila()
        pila.meter("x")
        pila.tope()
        self.assertEqual(len(pila), 1)

    def test_pila_vacia(self):
        pila = Pila()
        self.assertIsNone(pila.tope())
        with self.assertRaises(IndexError):
            pila.sacar()


class PruebasFila(unittest.TestCase):
    def test_fifo(self):
        fila = Fila()
        for elemento in (1, 2, 3):
            fila.encolar(elemento)
        self.assertEqual(fila.frente(), 1)
        self.assertEqual(list(fila), [1, 2, 3])
        self.assertEqual([fila.desencolar(), fila.desencolar(), fila.desencolar()], [1, 2, 3])
        self.assertTrue(fila.esta_vacia())

    def test_fila_vacia(self):
        fila = Fila()
        self.assertIsNone(fila.frente())
        with self.assertRaises(IndexError):
            fila.desencolar()


class PruebasExpresiones(unittest.TestCase):
    def test_asignacion_simple(self):
        self.assertEqual(cuadruplos("a = 5;"), [("=", 5, None, "a")])
        self.assertEqual(cuadruplos("a = b;"), [("=", "b", None, "a")])

    def test_suma(self):
        self.assertEqual(
            cuadruplos("a = b + c;"),
            [("+", "b", "c", "t1"), ("=", "t1", None, "a")],
        )

    def test_multiplicacion_antes_que_suma(self):
        self.assertEqual(
            cuadruplos("a = b + c * d;"),
            [("*", "c", "d", "t1"), ("+", "b", "t1", "t2"), ("=", "t2", None, "a")],
        )
        self.assertEqual(
            cuadruplos("a = b * c + d;"),
            [("*", "b", "c", "t1"), ("+", "t1", "d", "t2"), ("=", "t2", None, "a")],
        )

    def test_asociatividad_izquierda(self):
        # a - b - c  es  (a - b) - c,  no  a - (b - c)
        self.assertEqual(
            cuadruplos("d = a - b - c;"),
            [("-", "a", "b", "t1"), ("-", "t1", "c", "t2"), ("=", "t2", None, "d")],
        )
        # a / b * c  es  (a / b) * c
        self.assertEqual(
            cuadruplos("d = a / b * c;"),
            [("/", "a", "b", "t1"), ("*", "t1", "c", "t2"), ("=", "t2", None, "d")],
        )

    def test_parentesis_cambian_el_orden(self):
        self.assertEqual(
            cuadruplos("a = (b + c) * d;"),
            [("+", "b", "c", "t1"), ("*", "t1", "d", "t2"), ("=", "t2", None, "a")],
        )
        self.assertEqual(
            cuadruplos("a = b * (c + d);"),
            [("+", "c", "d", "t1"), ("*", "b", "t1", "t2"), ("=", "t2", None, "a")],
        )

    def test_parentesis_anidados(self):
        self.assertEqual(
            cuadruplos("a = ((b + c) * (d - a)) / b;"),
            [("+", "b", "c", "t1"), ("-", "d", "a", "t2"), ("*", "t1", "t2", "t3"),
             ("/", "t3", "b", "t4"), ("=", "t4", None, "a")],
        )

    def test_parentesis_redundantes(self):
        self.assertEqual(cuadruplos("a = ((b));"), [("=", "b", None, "a")])

    def test_relacional_va_al_final(self):
        self.assertEqual(
            cuadruplos("print(a + b > c * d);"),
            [("+", "a", "b", "t1"), ("*", "c", "d", "t2"), (">", "t1", "t2", "t3"),
             ("print", None, None, "t3")],
        )
        for operador in ("<", "!="):
            with self.subTest(operador=operador):
                self.assertEqual(cuadruplos(f"print(a {operador} b);")[0], (operador, "a", "b", "t1"))

    def test_ejemplo_largo(self):
        # A = B + C * (D - E / F) * H   (con a, b, c, d en lugar de las letras)
        self.assertEqual(
            cuadruplos("a = b + c * (d - a / b) * c;"),
            [("/", "a", "b", "t1"), ("-", "d", "t1", "t2"), ("*", "c", "t2", "t3"),
             ("*", "t3", "c", "t4"), ("+", "b", "t4", "t5"), ("=", "t5", None, "a")],
        )

    def test_menos_unario(self):
        self.assertEqual(cuadruplos("a = -5;"), [("=", -5, None, "a")])
        self.assertEqual(cuadruplos("x = -2.5;"), [("=", -2.5, None, "x")])
        self.assertEqual(
            cuadruplos("a = -b * c;"),
            [("neg", "b", None, "t1"), ("*", "t1", "c", "t2"), ("=", "t2", None, "a")],
        )
        self.assertEqual(
            cuadruplos("a = b - -c;"),
            [("neg", "c", None, "t1"), ("-", "b", "t1", "t2"), ("=", "t2", None, "a")],
        )

    def test_mas_unario_no_genera_nada(self):
        self.assertEqual(cuadruplos("a = +b;"), [("=", "b", None, "a")])

    def test_temporales_no_se_repiten(self):
        resultado = cuadruplos("a = b + c; d = a * b; a = c - d;")
        temporales = [cuadruplo[3] for cuadruplo in resultado if cuadruplo[0] != "="]
        self.assertEqual(temporales, ["t1", "t2", "t3"])

    def test_cada_compilacion_empieza_en_t1(self):
        cuadruplos("a = b + c;")
        self.assertEqual(cuadruplos("a = b + c;")[0][3], "t1")


class PruebasEstatutos(unittest.TestCase):
    def test_print(self):
        self.assertEqual(
            cuadruplos('print("hola", a, b + 1);'),
            [("print", None, None, '"hola"'), ("print", None, None, "a"),
             ("+", "b", 1, "t1"), ("print", None, None, "t1")],
        )

    def test_programa_vacio(self):
        self.assertEqual(cuadruplos(""), [])

    def test_estatutos_en_orden(self):
        self.assertEqual(
            cuadruplos("a = 1; b = 2; print(a);"),
            [("=", 1, None, "a"), ("=", 2, None, "b"), ("print", None, None, "a")],
        )

    def test_condicion_y_ciclo_dejan_pilas_limpias(self):
        # Entrega 4: ahora sí aparecen los saltos. main empieza en el cuádruplo 2.
        self.assertEqual(
            cuadruplos("if (a > b) { a = b; } else { b = a; };"),
            [(">", "a", "b", "t1"), ("GOTOF", "t1", None, 6), ("=", "b", None, "a"),
             ("GOTO", None, None, 7), ("=", "a", None, "b")],
        )
        self.assertEqual(
            cuadruplos("while (a < 10) do { a = a + 1; };"),
            [("<", "a", 10, "t1"), ("GOTOF", "t1", None, 7), ("+", "a", 1, "t2"),
             ("=", "t2", None, "a"), ("GOTO", None, None, 2)],
        )

    def test_argumentos_dejan_pilas_limpias(self):
        # Entrega 4: los argumentos ya generan ERA, PARAM y GOSUB.
        funcion = "void f(n : int, m : float) [ { } ];"
        self.assertEqual(cuadruplos("f(a + 1, x);", extra=funcion), [
            ("ERA", None, None, "f"), ("+", "a", 1, "t1"), ("PARAM", "t1", None, "n"),
            ("PARAM", "x", None, "m"), ("GOSUB", "f", None, 2)])

    def test_cuadruplos_dentro_de_funciones(self):
        # Entrega 4: GOTO a main al inicio, ENDFUNC al final de la función, END al
        # final del programa; los temporales se numeran desde t1 en cada alcance.
        compilacion = analizar(
            "program p; var g : int; void f(n : int) [ var t : int; { t = n * 2; g = t; } ]; "
            "main { g = 1; } end"
        )
        self.assertEqual(
            [cuadruplo.texto_legible() for cuadruplo in compilacion.cuadruplos],
            ["(GOTO, _, _, 6)", "(*, n, 2, t1)", "(=, t1, _, t)", "(=, t, _, g)",
             "(ENDFUNC, _, _, _)", "(=, 1, _, g)", "(END, _, _, _)"],
        )


class PruebasTipos(unittest.TestCase):
    def assertErrorSemantico(self, cuerpo, fragmento):
        with self.assertRaises(ErrorSemantico) as contexto:
            cuadruplos(cuerpo)
        self.assertIn(fragmento, str(contexto.exception))

    def tipos_de_traza(self, cuerpo):
        compilacion = analizar(f"program p; {VARIABLES} main {{ {cuerpo} }} end", con_traza=True)
        return compilacion.generador.traza

    def test_int_a_float_si(self):
        cuadruplos("x = a;")
        cuadruplos("x = a + b;")

    def test_float_a_int_no(self):
        self.assertErrorSemantico("a = x;", "no se puede asignar un valor float a 'a'")
        self.assertErrorSemantico("a = 2.5;", "no se puede asignar")
        self.assertErrorSemantico("a = b + x;", "no se puede asignar")   # int + float = float

    def test_tipo_del_temporal(self):
        traza = self.tipos_de_traza("x = a + y;")
        paso = next(p for p in traza if p["accion"] == "resolver +")
        self.assertEqual(paso["tipos"][-1], "float")
        traza = self.tipos_de_traza("a = b / c;")
        paso = next(p for p in traza if p["accion"] == "resolver /")
        self.assertEqual(paso["tipos"][-1], "int")

    def test_bool_no_se_asigna_ni_se_opera(self):
        self.assertErrorSemantico("a = b > c;", "no se puede asignar un valor bool")
        self.assertErrorSemantico("a = (b > c) + 1;", "tipos incompatibles: bool + int")
        self.assertErrorSemantico("print((a > b) < c);", "tipos incompatibles: bool < int")

    def test_condicion_debe_ser_bool(self):
        self.assertErrorSemantico("if (a) { };", "la condición del if")
        self.assertErrorSemantico("while (a + 1) do { };", "la condición del while")

    def test_archivos_con_error(self):
        for nombre, fragmento in (
            ("error_tipos_asignacion.bd", "no se puede asignar"),
            ("error_tipos_bool.bd", "tipos incompatibles"),
            ("error_condicion_no_bool.bd", "la condición del if"),
        ):
            with self.subTest(archivo=nombre):
                with self.assertRaises(ErrorSemantico) as contexto:
                    analizar(leer(nombre))
                self.assertIn(fragmento, str(contexto.exception))


class PruebasTraza(unittest.TestCase):
    def test_pilas_paso_a_paso(self):
        compilacion = analizar(f"program p; {VARIABLES} main {{ a = b + c * d; }} end",
                               con_traza=True)
        # Entrega 4: se omiten los pasos del GOTO a main y del END.
        pasos = [(p["accion"], p["operandos"], p["operadores"]) for p in compilacion.generador.traza
                 if "main" not in p["accion"] and p["accion"] != "fin"]
        self.assertEqual(pasos, [
            ("meter operando a", ["a"], []),
            ("meter operador =", ["a"], ["="]),
            ("meter operando b", ["a", "b"], ["="]),
            ("meter operador +", ["a", "b"], ["=", "+"]),
            ("meter operando c", ["a", "b", "c"], ["=", "+"]),
            ("meter operador *", ["a", "b", "c"], ["=", "+", "*"]),
            ("meter operando d", ["a", "b", "c", "d"], ["=", "+", "*"]),
            ("resolver *", ["a", "b", "t1"], ["=", "+"]),
            ("resolver +", ["a", "t2"], ["="]),
            ("generar asignación", [], []),
        ])


class PruebasArchivos(unittest.TestCase):
    def test_todos_los_archivos_estan_clasificados(self):
        for ruta in sorted(glob.glob(os.path.join(CARPETA, "*.bd"))):
            nombre = os.path.basename(ruta)
            with self.subTest(archivo=nombre):
                if nombre.startswith("error_"):
                    with self.assertRaises(ErrorBabyDuck):
                        analizar(leer(nombre))
                else:
                    compilacion = analizar(leer(nombre))
                    self.assertTrue(compilacion.generador.pilas_vacias())

    def test_archivo_de_expresiones(self):
        compilacion = analizar(leer("expresiones.bd"))
        # Entrega 4: dos cuádruplos más (GOTO a main y END) y vista legible.
        texto = [cuadruplo.texto_legible() for cuadruplo in compilacion.cuadruplos]
        self.assertEqual(len(texto), 35)
        self.assertEqual(texto[4:7], ["(*, b, c, t1)", "(+, a, t1, t2)", "(=, t2, _, d)"])
        self.assertEqual(texto[-2], "(print, _, _, t19)")


if __name__ == "__main__":
    unittest.main()

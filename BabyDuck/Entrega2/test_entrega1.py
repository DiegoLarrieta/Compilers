"""
test_entrega1.py - Plan de pruebas del scanner y del parser.

Se corre desde esta carpeta con:
    python -m unittest -v
"""

import os
import unittest

from errores import ErrorLexico, ErrorSintactico
from lexer import tokenizar
from parser import analizar

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programas")


def leer(nombre):
    with open(os.path.join(CARPETA, nombre), encoding="utf-8") as archivo:
        return archivo.read()


def tipos(codigo):
    """Solo los tipos de token, para comparar más fácil."""
    return [tipo for tipo, _, _ in tokenizar(codigo)]


def programa(cuerpo, variables="var a, b : int; x : float;"):
    """Envuelve estatutos en un programa completo."""
    return f"program p; {variables} main {{ {cuerpo} }} end"


class PruebasScanner(unittest.TestCase):
    def test_palabras_reservadas(self):
        codigo = "program main end var int float void print if else while do"
        self.assertEqual(
            tipos(codigo),
            ["PROGRAM", "MAIN", "END", "VAR", "INT", "FLOAT", "VOID", "PRINT",
             "IF", "ELSE", "WHILE", "DO"],
        )

    def test_identificador_que_empieza_como_reservada(self):
        # "iffy", "printer" y "main2" son identificadores, no palabras reservadas.
        self.assertEqual(tipos("iffy printer main2 _x x_1"), ["ID"] * 5)

    def test_reservadas_distinguen_mayusculas(self):
        self.assertEqual(tipos("Program IF"), ["ID", "ID"])

    def test_constantes(self):
        self.assertEqual(
            tokenizar('42 3.14 "hola mundo"'),
            [("CTE_INT", 42, 1), ("CTE_FLOAT", 3.14, 1), ("CTE_STRING", "hola mundo", 1)],
        )

    def test_flotante_no_se_parte_en_entero(self):
        self.assertEqual(tipos("10.5"), ["CTE_FLOAT"])

    def test_operadores_y_puntuacion(self):
        self.assertEqual(
            tipos("+ - * / = != > < ; , : ( ) { } [ ]"),
            ["PLUS", "MINUS", "TIMES", "DIVIDE", "ASSIGN", "NE", "GT", "LT",
             "SEMICOLON", "COMMA", "COLON", "LPAREN", "RPAREN", "LBRACE",
             "RBRACE", "LBRACKET", "RBRACKET"],
        )

    def test_sin_espacios(self):
        self.assertEqual(
            tipos("a=b+1;"), ["ID", "ASSIGN", "ID", "PLUS", "CTE_INT", "SEMICOLON"]
        )

    def test_cuenta_lineas(self):
        self.assertEqual([linea for _, _, linea in tokenizar("a\nb\n\nc")], [1, 2, 4])

    def test_caracter_invalido(self):
        with self.assertRaises(ErrorLexico) as contexto:
            tokenizar("a = 5 $ 3;")
        self.assertIn("$", str(contexto.exception))

    def test_string_sin_cerrar(self):
        with self.assertRaises(ErrorLexico):
            tokenizar('print("hola);')

    def test_admiracion_sola_no_es_token(self):
        with self.assertRaises(ErrorLexico):
            tokenizar("a ! b")


class PruebasParserValidos(unittest.TestCase):
    def test_programa_minimo(self):
        self.assertTrue(analizar("program p; main { } end"))

    def test_archivos_validos(self):
        for nombre in ("minimo.bd", "aritmetica.bd", "factorial.bd"):
            with self.subTest(archivo=nombre):
                self.assertTrue(analizar(leer(nombre)))

    def test_varias_declaraciones(self):
        self.assertTrue(analizar("program p; var a : int; b, c : float; d : int; main { } end"))

    def test_expresiones(self):
        casos = [
            "a = 1;",
            "a = a + b * 2 - 3 / b;",
            "a = (a + b) * (a - b);",
            "a = ((a));",
            "x = -a + +b;",
            "x = -3.5 * a;",
            "print(a > b);",
            "print(a + 1 != b * 2);",
        ]
        for caso in casos:
            with self.subTest(estatuto=caso):
                self.assertTrue(analizar(programa(caso)))

    def test_estatutos(self):
        casos = [
            'print("hola");',
            'print("a vale", a, a + b, "fin");',
            "if (a > b) { a = b; };",
            "if (a < b) { a = b; } else { b = a; };",
            "while (a < 10) do { a = a + 1; };",
            "while (a < 10) do { if (a != 5) { print(a); }; a = a + 1; };",
        ]
        for caso in casos:
            with self.subTest(estatuto=caso):
                self.assertTrue(analizar(programa(caso)))

    def test_funciones_y_llamadas(self):
        codigo = """
        program p;
        var a : int;
        void sin_params() [ { print("x"); } ];
        void con_params(n : int, f : float) [ var t : int; { t = n; } ];
        main {
            sin_params();
            con_params(a + 1, 2.5);
        }
        end
        """
        self.assertTrue(analizar(codigo))


class PruebasParserInvalidos(unittest.TestCase):
    def assertErrorSintaxis(self, codigo, linea=None):
        with self.assertRaises(ErrorSintactico) as contexto:
            analizar(codigo)
        if linea is not None:
            self.assertEqual(contexto.exception.linea, linea)

    def test_archivos_con_error(self):
        self.assertErrorSintaxis(leer("error_sintaxis.bd"), linea=4)
        self.assertErrorSintaxis(leer("error_falta_punto_y_coma.bd"), linea=5)
        with self.assertRaises(ErrorLexico):
            analizar(leer("error_lexico.bd"))

    def test_estructura_del_programa(self):
        casos = [
            "",                                   # archivo vacío
            "main { } end",                       # falta 'program id ;'
            "program p main { } end",             # falta ';'
            "program p; { } end",                 # falta 'main'
            "program p; main { }",                # falta 'end'
            "program p; main { } end end",        # sobra texto
            "program p; var ; main { } end",      # 'var' sin declaraciones
            "program p; var a int; main { } end", # falta ':'
            "program p; var a : string; main { } end",  # tipo inexistente
        ]
        for caso in casos:
            with self.subTest(codigo=caso):
                self.assertErrorSintaxis(caso)

    def test_estatutos_mal_escritos(self):
        casos = [
            "a = ;",                               # falta la expresión
            "a = 1",                               # falta ';'
            "a = (1 + 2;",                         # paréntesis sin cerrar
            "a = 1 + * 2;",                        # dos operadores seguidos
            "a = 1 > 2 > 3;",                      # solo se permite un relacional
            "a = -(a + b);",                       # el signo solo va antes de id o cte
            "print();",                            # print necesita al menos un elemento
            "if (a > b) { a = b; }",               # falta ';' al final del if
            "if a > b { a = b; };",                # faltan paréntesis
            "while (a < 10) { a = a + 1; };",      # falta 'do'
            "print(a); b",                        # estatuto incompleto
            "var c : int;",                        # declaración dentro del cuerpo
        ]
        for caso in casos:
            with self.subTest(estatuto=caso):
                self.assertErrorSintaxis(programa(caso))

    def test_funcion_mal_escrita(self):
        casos = [
            "program p; void f() { } ; main { } end",        # faltan corchetes
            "program p; void f() [ { } ] main { } end",      # falta ';' tras ']'
            "program p; void f(a) [ { } ]; main { } end",    # parámetro sin tipo
            "program p; int f() [ { } ]; main { } end",      # solo existen funciones void
        ]
        for caso in casos:
            with self.subTest(codigo=caso):
                self.assertErrorSintaxis(caso)


if __name__ == "__main__":
    unittest.main()

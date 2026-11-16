"""
cuadruplos.py - Generación de código intermedio (cuádruplos) de BabyDuck.

Un cuádruplo es una instrucción muy simple con 4 campos:

    (operador, operando_izquierdo, operando_derecho, resultado)

Por ejemplo  a + b * c  se traduce a:

    1: (*, b, c, t1)
    2: (+, a, t1, t2)

donde t1 y t2 son TEMPORALES: variables que inventa el compilador para guardar
resultados intermedios.

Estructuras que usa el generador (están en estructuras.py):

    pila_operandos   (PilaO)   nombres de variables, constantes y temporales
    pila_tipos       (PTipos)  el tipo de cada operando; va en paralelo a PilaO
    pila_operadores  (POper)   operadores pendientes de resolver y fondos falsos
    fila             (Fila)    los cuádruplos generados, en orden

El parser llama a los métodos de esta clase desde los puntos neurálgicos.
"""

from cubo_semantico import BOOL, ERROR, FLOAT, INT, tipo_resultante
from errores import ErrorSemantico
from estructuras import Fila, Pila

# Marca que se mete a la pila de operadores al abrir un paréntesis.
FONDO_FALSO = "("

OPERADORES_MULT = ("*", "/")
OPERADORES_SUMA = ("+", "-")
OPERADORES_REL = (">", "<", "!=")


class Cuadruplo:
    """Una instrucción de código intermedio."""

    def __init__(self, operador, izquierdo, derecho, resultado):
        self.operador = operador
        self.izquierdo = izquierdo
        self.derecho = derecho
        self.resultado = resultado

    def como_tupla(self):
        return (self.operador, self.izquierdo, self.derecho, self.resultado)

    def __str__(self):
        # Un campo que no se usa (None) se muestra como "_".
        campos = ["_" if campo is None else str(campo) for campo in self.como_tupla()]
        return "(" + ", ".join(campos) + ")"

    __repr__ = __str__


class GeneradorCuadruplos:
    """Lleva las pilas y la fila, y sabe traducir cada construcción a cuádruplos."""

    def __init__(self, con_traza=False):
        self.pila_operandos = Pila()
        self.pila_tipos = Pila()
        self.pila_operadores = Pila()
        self.fila = Fila()
        self.temporales = 0
        # Si se pide, guarda una "foto" de las pilas después de cada acción.
        self.traza = [] if con_traza else None

    # ------------------------------------------------------------------
    # Apoyo
    # ------------------------------------------------------------------
    @property
    def cuadruplos(self):
        """Los cuádruplos generados, como lista."""
        return self.fila.como_lista()

    def _nuevo_temporal(self):
        """Regresa el siguiente temporal disponible: t1, t2, t3, ..."""
        self.temporales += 1
        return f"t{self.temporales}"

    def _generar(self, operador, izquierdo, derecho, resultado):
        cuadruplo = Cuadruplo(operador, izquierdo, derecho, resultado)
        self.fila.encolar(cuadruplo)
        return cuadruplo

    def _sacar_operando(self):
        """Saca un operando junto con su tipo (las dos pilas van en paralelo)."""
        return self.pila_operandos.sacar(), self.pila_tipos.sacar()

    def _anotar(self, accion, cuadruplo=None):
        if self.traza is not None:
            self.traza.append({
                "accion": accion,
                "operandos": self.pila_operandos.como_lista(),
                "tipos": self.pila_tipos.como_lista(),
                "operadores": self.pila_operadores.como_lista(),
                "cuadruplo": str(cuadruplo) if cuadruplo else "",
            })

    # ------------------------------------------------------------------
    # Expresiones
    # ------------------------------------------------------------------
    def meter_operando(self, operando, tipo):
        """Se leyó un id o una constante: va a PilaO y su tipo a PTipos."""
        self.pila_operandos.meter(operando)
        self.pila_tipos.meter(tipo)
        self._anotar(f"meter operando {operando}")

    def meter_operador(self, operador):
        """Se leyó un operador: queda pendiente en POper."""
        self.pila_operadores.meter(operador)
        self._anotar(f"meter operador {operador}")

    def meter_fondo_falso(self):
        """
        Se abrió un paréntesis. El fondo falso "tapa" los operadores que ya
        estaban pendientes, para que lo de adentro se resuelva primero.
        """
        self.pila_operadores.meter(FONDO_FALSO)
        self._anotar("meter fondo falso")

    def quitar_fondo_falso(self):
        """Se cerró el paréntesis: se quita la marca."""
        self.pila_operadores.sacar()
        self._anotar("quitar fondo falso")

    def resolver(self, operadores, linea=None):
        """
        Corazón del algoritmo. Si el operador del tope de POper es uno de
        `operadores`, se genera su cuádruplo:

            1. se saca el operador
            2. se sacan el operando derecho y el izquierdo (en ese orden,
               porque el derecho fue el último en entrar) con sus tipos
            3. se consulta el cubo semántico; si da ERROR, error de tipos
            4. se pide un temporal para el resultado y se genera el cuádruplo
            5. el temporal se mete a PilaO (y su tipo a PTipos), porque es el
               operando de la siguiente operación

        Se llama con ("*", "/") al terminar un factor, con ("+", "-") al
        terminar un término y con los relacionales al terminar la expresión.
        Ese orden es lo que respeta la precedencia de operadores.
        """
        if self.pila_operadores.tope() not in operadores:
            return
        operador = self.pila_operadores.sacar()
        derecho, tipo_derecho = self._sacar_operando()
        izquierdo, tipo_izquierdo = self._sacar_operando()

        tipo = tipo_resultante(operador, tipo_izquierdo, tipo_derecho)
        if tipo == ERROR:
            raise ErrorSemantico(
                f"tipos incompatibles: {tipo_izquierdo} {operador} {tipo_derecho}", linea
            )

        temporal = self._nuevo_temporal()
        cuadruplo = self._generar(operador, izquierdo, derecho, temporal)
        self.pila_operandos.meter(temporal)
        self.pila_tipos.meter(tipo)
        self._anotar(f"resolver {operador}", cuadruplo)

    def negar(self):
        """
        Menos unario (`-x`). Si el operando es una constante simplemente se
        cambia de signo; si es una variable se genera (neg, x, _, temporal).
        """
        operando, tipo = self._sacar_operando()
        if isinstance(operando, (int, float)):
            self.pila_operandos.meter(-operando)
            self.pila_tipos.meter(tipo)
            self._anotar("negar constante")
            return
        temporal = self._nuevo_temporal()
        cuadruplo = self._generar("neg", operando, None, temporal)
        self.pila_operandos.meter(temporal)
        self.pila_tipos.meter(tipo)
        self._anotar("negar", cuadruplo)

    # ------------------------------------------------------------------
    # Estatutos lineales
    # ------------------------------------------------------------------
    def asignar(self, linea=None):
        """
        Fin de `id = expresion`. En las pilas están: el destino (abajo), el
        valor de la expresión (arriba) y "=" en POper. Genera (=, valor, _, id).
        """
        self.pila_operadores.sacar()                      # el "="
        valor, tipo_valor = self._sacar_operando()
        destino, tipo_destino = self._sacar_operando()
        if tipo_resultante("=", tipo_destino, tipo_valor) == ERROR:
            raise ErrorSemantico(
                f"no se puede asignar un valor {tipo_valor} a '{destino}', que es {tipo_destino}",
                linea,
            )
        cuadruplo = self._generar("=", valor, None, destino)
        self._anotar("generar asignación", cuadruplo)

    def imprimir_expresion(self):
        """Un elemento de print que es expresión: genera (print, _, _, valor)."""
        valor, _ = self._sacar_operando()
        cuadruplo = self._generar("print", None, None, valor)
        self._anotar("generar print", cuadruplo)

    def imprimir_letrero(self, texto):
        """Un elemento de print que es letrero: genera (print, _, _, "texto")."""
        cuadruplo = self._generar("print", None, None, f'"{texto}"')
        self._anotar("generar print", cuadruplo)

    # ------------------------------------------------------------------
    # Estatutos que se completan en la siguiente entrega
    # ------------------------------------------------------------------
    def verificar_condicion(self, estatuto, linea=None):
        """
        Condición de un if o un while. Ya se generaron los cuádruplos de la
        expresión; aquí se saca su resultado y se valida que sea booleano.
        (El salto GOTOF que usa este resultado es parte de la siguiente entrega.)
        """
        _, tipo = self._sacar_operando()
        if tipo != BOOL:
            raise ErrorSemantico(
                f"la condición del {estatuto} debe ser una comparación (se recibió {tipo})", linea
            )
        self._anotar(f"verificar condición del {estatuto}")

    def descartar_argumento(self):
        """
        Argumento de una llamada a función. Sus cuádruplos ya se generaron; el
        resultado se saca de la pila. (PARAM / GOSUB son de la siguiente entrega.)
        """
        self._sacar_operando()
        self._anotar("sacar argumento")

    # ------------------------------------------------------------------
    # Despliegue
    # ------------------------------------------------------------------
    def pilas_vacias(self):
        """Al terminar de compilar no debe quedar nada pendiente en las pilas."""
        return (self.pila_operandos.esta_vacia() and self.pila_tipos.esta_vacia()
                and self.pila_operadores.esta_vacia())

    def como_texto(self):
        """La fila de cuádruplos numerada, un cuádruplo por renglón."""
        return "\n".join(f"{numero:>3}: {cuadruplo}"
                         for numero, cuadruplo in enumerate(self.fila, start=1))

    def traza_como_texto(self):
        """Tabla con el contenido de las pilas después de cada acción."""
        def celda(valores):
            return " ".join(str(valor) for valor in valores) or "-"

        renglones = [("ACCIÓN", "PilaO", "PTipos", "POper", "CUÁDRUPLO")]
        for paso in self.traza or []:
            renglones.append((paso["accion"], celda(paso["operandos"]), celda(paso["tipos"]),
                              celda(paso["operadores"]), paso["cuadruplo"]))
        anchos = [max(len(renglon[i]) for renglon in renglones) for i in range(5)]
        return "\n".join(
            "  ".join(campo.ljust(ancho) for campo, ancho in zip(renglon, anchos)).rstrip()
            for renglon in renglones
        )


def tipo_de_constante(valor):
    """Tipo BabyDuck de una constante numérica de Python."""
    return FLOAT if isinstance(valor, float) else INT

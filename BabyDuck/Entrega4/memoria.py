"""
memoria.py - Distribución de direcciones virtuales de BabyDuck.

En los cuádruplos ya no aparecen nombres ("a", "t1", 5) sino DIRECCIONES
VIRTUALES: números enteros que dicen en qué segmento de memoria vive el dato y
de qué tipo es. La máquina virtual (siguiente entrega) solo verá números.

Distribución (1000 direcciones por cada combinación segmento-tipo):

    Segmento      int           float         bool          letrero
    -----------   -----------   -----------   -----------   -------------
    Global        1000 - 1999   2000 - 2999
    Local         3000 - 3999   4000 - 4999
    Temporal      5000 - 5999   6000 - 6999   7000 - 7999
    Constante     8000 - 8999   9000 - 9999                 10000 - 10999

Decisiones:
  * Con ver la dirección se sabe el segmento y el tipo (basta comparar rangos),
    así la máquina virtual no necesita guardar el tipo aparte.
  * Global: variables declaradas en el `var` del programa. Viven todo el programa.
  * Local: parámetros y variables de una función. Cada llamada tendrá su propia
    copia, por eso el contador se reinicia al empezar cada función.
  * Temporal: resultados intermedios. También son locales a la función (o a main):
    el contador se reinicia al empezar cada función y al empezar main.
  * bool solo existe como temporal (resultado de > < !=); no hay variables bool.
  * Constante: cada valor distinto recibe UNA dirección y se reutiliza
    (tabla de constantes). Los letreros de print son constantes de texto.
"""

from cubo_semantico import BOOL, FLOAT, INT
from errores import ErrorSemantico

LETRERO = "letrero"
TAMANO = 1000

GLOBAL = "global"
LOCAL = "local"
TEMPORAL = "temporal"
CONSTANTE = "constante"

# (segmento, tipo) -> dirección base
BASES = {
    (GLOBAL, INT): 1000, (GLOBAL, FLOAT): 2000,
    (LOCAL, INT): 3000, (LOCAL, FLOAT): 4000,
    (TEMPORAL, INT): 5000, (TEMPORAL, FLOAT): 6000, (TEMPORAL, BOOL): 7000,
    (CONSTANTE, INT): 8000, (CONSTANTE, FLOAT): 9000, (CONSTANTE, LETRERO): 10000,
}


def segmento_y_tipo(direccion):
    """Inverso de BASES: dada una dirección, ¿de qué segmento y tipo es?"""
    for (segmento, tipo), base in BASES.items():
        if base <= direccion < base + TAMANO:
            return segmento, tipo
    raise ValueError(f"la dirección {direccion} no pertenece a ningún segmento")


class Segmento:
    """Contadores de UN segmento (uno por tipo). Reparte direcciones en orden."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.tipos = [tipo for (segmento, tipo) in BASES if segmento == nombre]
        self.reiniciar()

    def reiniciar(self):
        self.usadas = {tipo: 0 for tipo in self.tipos}

    def asignar(self, tipo):
        """Regresa la siguiente dirección libre de ese tipo."""
        if self.usadas[tipo] >= TAMANO:
            raise ErrorSemantico(f"se acabó la memoria {self.nombre} para datos {tipo} "
                                 f"(máximo {TAMANO})")
        direccion = BASES[(self.nombre, tipo)] + self.usadas[tipo]
        self.usadas[tipo] += 1
        return direccion

    def conteo(self):
        """Cuántas direcciones de cada tipo se han usado (para ERA)."""
        return dict(self.usadas)


class MemoriaVirtual:
    """Los cuatro segmentos y la tabla de constantes de un programa."""

    def __init__(self):
        self.globales = Segmento(GLOBAL)
        self.locales = Segmento(LOCAL)
        self.temporales = Segmento(TEMPORAL)
        self.constantes = Segmento(CONSTANTE)
        # (tipo, valor) -> dirección. Un mismo valor siempre usa la misma dirección.
        self.tabla_constantes = {}

    def variable(self, tipo, es_global):
        """Dirección para una variable (o parámetro) recién declarada."""
        return (self.globales if es_global else self.locales).asignar(tipo)

    def temporal(self, tipo):
        return self.temporales.asignar(tipo)

    def constante(self, valor, tipo):
        """Dirección de una constante; si el valor ya existía, se reutiliza."""
        llave = (tipo, valor)
        if llave not in self.tabla_constantes:
            self.tabla_constantes[llave] = self.constantes.asignar(tipo)
        return self.tabla_constantes[llave]

    def valor_de_constante(self, direccion):
        for (_, valor), dir_constante in self.tabla_constantes.items():
            if dir_constante == direccion:
                return valor
        return None

    def nuevo_alcance(self):
        """Empieza una función (o main): locales y temporales vuelven a cero."""
        self.locales.reiniciar()
        self.temporales.reiniciar()

    def tabla_constantes_como_texto(self):
        lineas = []
        for (tipo, valor), direccion in sorted(self.tabla_constantes.items(), key=lambda x: x[1]):
            mostrado = f'"{valor}"' if tipo == LETRERO else valor
            lineas.append(f"  {direccion:>6}  {tipo:<8} {mostrado}")
        return "\n".join(lineas)

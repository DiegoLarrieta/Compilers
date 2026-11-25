"""
directorio.py - Directorio de Funciones y Tablas de Variables de BabyDuck.

Estructuras (todas son tablas hash, es decir, `dict` de Python):

    DirectorioFunciones
      └── funciones : dict  nombre -> Funcion          (una entrada por alcance)
            Funcion
              ├── nombre, tipo ("programa" o "void")
              ├── parametros : list de tipos           (la "firma", en orden)
              ├── direcciones_parametros : list        (dirección de cada parámetro)
              ├── inicio     : número del primer cuádruplo de la función
              ├── recursos   : cuántas direcciones de cada tipo necesita (para ERA)
              └── variables  : TablaVariables
                    └── dict  nombre -> Variable(nombre, tipo, es_parametro, direccion)

Entrega 4: cada variable recibe su DIRECCIÓN VIRTUAL al declararse (ver
memoria.py). Las globales van al segmento global y las de una función
(incluidos sus parámetros) al segmento local.

¿Por qué diccionarios?
  * Lo que más hace el compilador con estas tablas es BUSCAR por nombre
    ("¿ya existe esta variable?", "¿de qué tipo es?"). En un dict eso cuesta
    O(1) en promedio, contra O(n) de una lista.
  * Los nombres son únicos dentro de su alcance, igual que las llaves de un dict.
  * Python conserva el orden de inserción, así que al imprimir las tablas salen
    en el orden en que se declararon.

Los parámetros además se guardan en una LISTA, porque ahí el orden sí importa:
al llamar a la función, el primer argumento corresponde al primer parámetro.

El alcance global se guarda como una entrada más del directorio, con el nombre
del programa como llave.
"""

from errores import ErrorSemantico
from memoria import CONSTANTE, GLOBAL, LOCAL, TEMPORAL, MemoriaVirtual

TIPO_PROGRAMA = "programa"
TIPO_VOID = "void"


class Variable:
    """Un renglón de la tabla de variables."""

    def __init__(self, nombre, tipo, es_parametro=False, direccion=None):
        self.nombre = nombre
        self.tipo = tipo
        self.es_parametro = es_parametro
        self.direccion = direccion

    def __repr__(self):
        return f"Variable({self.nombre!r}, {self.tipo!r}, {self.direccion})"


class TablaVariables:
    """Variables de UN alcance (el global o el de una función)."""

    def __init__(self):
        self.variables = {}

    def existe(self, nombre):
        return nombre in self.variables

    def agregar(self, nombre, tipo, es_parametro=False, direccion=None):
        """Inserta la variable. El que llama ya validó que no esté repetida."""
        variable = Variable(nombre, tipo, es_parametro, direccion)
        self.variables[nombre] = variable
        return variable

    def buscar(self, nombre):
        """Regresa la Variable o None si no está en esta tabla."""
        return self.variables.get(nombre)

    def __len__(self):
        return len(self.variables)

    def __iter__(self):
        return iter(self.variables.values())


class Funcion:
    """Un renglón del directorio de funciones."""

    def __init__(self, nombre, tipo):
        self.nombre = nombre
        self.tipo = tipo
        self.parametros = []            # tipos de los parámetros, en orden
        self.direcciones_parametros = []  # dirección de cada parámetro, en orden
        self.inicio = None              # número del primer cuádruplo (para GOSUB)
        self.recursos = {}              # {"local": {...}, "temporal": {...}} (para ERA)
        self.variables = TablaVariables()

    def __repr__(self):
        return f"Funcion({self.nombre!r}, {self.tipo!r}, params={self.parametros})"


class DirectorioFunciones:
    """
    Directorio de funciones. También recuerda cuál es el alcance que se está
    compilando en este momento (`alcance_actual`), para saber en qué tabla caen
    las variables que se van declarando.
    """

    def __init__(self, memoria=None):
        self.funciones = {}
        self.nombre_programa = None
        self.alcance_actual = None
        self.memoria = memoria or MemoriaVirtual()

    # -- Creación de alcances ------------------------------------------------
    def crear_programa(self, nombre):
        """Registra el alcance global. Es la primera entrada del directorio."""
        self.nombre_programa = nombre
        self.funciones[nombre] = Funcion(nombre, TIPO_PROGRAMA)
        self.alcance_actual = nombre

    def crear_funcion(self, nombre, linea=None):
        """Registra una función nueva y la vuelve el alcance actual."""
        if nombre == self.nombre_programa:
            raise ErrorSemantico(
                f"la función '{nombre}' no puede llamarse igual que el programa", linea
            )
        if nombre in self.funciones:
            raise ErrorSemantico(f"la función '{nombre}' ya fue declarada", linea)
        self.funciones[nombre] = Funcion(nombre, TIPO_VOID)
        self.alcance_actual = nombre
        # Sus locales y temporales empiezan desde la base de su segmento.
        self.memoria.nuevo_alcance()

    def cerrar_funcion(self):
        """
        Al terminar una función se guarda cuánta memoria local y temporal usó
        (lo necesita ERA para reservar su espacio) y se regresa al alcance global.
        """
        funcion = self.funciones[self.alcance_actual]
        funcion.recursos = {LOCAL: self.memoria.locales.conteo(),
                            TEMPORAL: self.memoria.temporales.conteo()}
        self.alcance_actual = self.nombre_programa

    def empezar_main(self):
        """main usa el alcance global, pero sus temporales empiezan de cero."""
        self.alcance_actual = self.nombre_programa
        self.memoria.nuevo_alcance()

    def cerrar_programa(self):
        """Recursos del alcance global: variables globales y temporales de main."""
        programa = self.funciones[self.nombre_programa]
        programa.recursos = {GLOBAL: self.memoria.globales.conteo(),
                             TEMPORAL: self.memoria.temporales.conteo(),
                             CONSTANTE: self.memoria.constantes.conteo()}

    # -- Variables -----------------------------------------------------------
    def agregar_variable(self, nombre, tipo, linea=None, es_parametro=False):
        """
        Agrega una variable al alcance actual.

        Validación: no puede haber dos variables con el mismo nombre en el
        mismo alcance (un parámetro cuenta como variable local). Sí se permite
        que una variable local se llame igual que una global: la local la tapa.
        """
        funcion = self.funciones[self.alcance_actual]
        if funcion.variables.existe(nombre):
            donde = "global" if self.alcance_actual == self.nombre_programa else (
                f"en la función '{self.alcance_actual}'"
            )
            raise ErrorSemantico(f"la variable '{nombre}' ya fue declarada ({donde})", linea)
        es_global = self.alcance_actual == self.nombre_programa
        direccion = self.memoria.variable(tipo, es_global)
        funcion.variables.agregar(nombre, tipo, es_parametro, direccion)
        if es_parametro:
            funcion.parametros.append(tipo)
            funcion.direcciones_parametros.append(direccion)

    def buscar_variable(self, nombre, linea=None):
        """
        Busca una variable primero en el alcance actual y después en el global.
        Lanza ErrorSemantico si no existe en ninguno de los dos.
        """
        for alcance in (self.alcance_actual, self.nombre_programa):
            variable = self.funciones[alcance].variables.buscar(nombre)
            if variable is not None:
                return variable
        raise ErrorSemantico(f"la variable '{nombre}' no ha sido declarada", linea)

    # -- Funciones -----------------------------------------------------------
    def buscar_funcion(self, nombre, linea=None):
        """Regresa la Funcion que se quiere llamar o lanza ErrorSemantico."""
        funcion = self.funciones.get(nombre)
        if funcion is None or funcion.tipo == TIPO_PROGRAMA:
            raise ErrorSemantico(f"la función '{nombre}' no ha sido declarada", linea)
        return funcion

    # -- Despliegue ----------------------------------------------------------
    def como_texto(self):
        """Regresa el directorio completo en texto, para mostrarlo en consola."""
        lineas = []
        for funcion in self.funciones.values():
            if funcion.tipo == TIPO_PROGRAMA:
                lineas.append(f"[global] programa '{funcion.nombre}'")
            else:
                firma = ", ".join(funcion.parametros) or "sin parámetros"
                lineas.append(f"[función] {funcion.tipo} {funcion.nombre}({firma})"
                              f"  inicia en el cuádruplo {funcion.inicio}")
            if funcion.recursos:
                lineas.append("    recursos: " + _recursos_como_texto(funcion.recursos))
            if len(funcion.variables) == 0:
                lineas.append("    (sin variables)")
            for variable in funcion.variables:
                clase = "parámetro" if variable.es_parametro else "variable"
                lineas.append(f"    {variable.nombre:<12} {variable.tipo:<6} {variable.direccion:>6}  {clase}")
        return "\n".join(lineas)


def _recursos_como_texto(recursos):
    """{"local": {"int": 2, "float": 0}, ...} -> "local int=2 float=0 | ..." (sin ceros)."""
    partes = []
    for segmento, conteo in recursos.items():
        usados = " ".join(f"{tipo}={n}" for tipo, n in conteo.items() if n)
        partes.append(f"{segmento} {usados or '-'}")
    return " | ".join(partes)

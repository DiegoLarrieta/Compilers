"""
cuadruplos.py - Generación de código intermedio (cuádruplos) de BabyDuck.

Un cuádruplo es una instrucción con 4 campos:

    (operador, operando_izquierdo, operando_derecho, resultado)

Entrega 4: los operandos ya no son nombres sino DIRECCIONES VIRTUALES (ver
memoria.py). Por ejemplo, con a=1000, b=1001, c=1002 (globales int):

    a = b + c * 2;   ->   (*, 1002, 8000, 5000)    (*, c, 2, t1)
                          (+, 1001, 5000, 5001)    (+, b, t1, t2)
                          (=, 5001, _, 1000)       (=, t2, _, a)

La columna de la derecha es la versión "legible" del mismo cuádruplo: se
guarda junto con el cuádruplo solo para mostrarlo y depurarlo.

Estructuras que usa el generador (están en estructuras.py):

    pila_operandos   (PilaO)   direcciones de variables, constantes y temporales
    pila_tipos       (PTipos)  el tipo de cada operando; va en paralelo a PilaO
    pila_operadores  (POper)   operadores pendientes de resolver y fondos falsos
    pila_saltos      (PSaltos) números de cuádruplos con un salto pendiente de
                               rellenar, o a los que hay que regresar (while)
    fila             (Fila)    los cuádruplos generados, en orden

Operadores nuevos de esta entrega:

    (GOTO,    _,         _, destino)   salto incondicional
    (GOTOF,   condición, _, destino)   salta si la condición es falsa
    (ERA,     _,         _, función)   reserva la memoria de la función
    (PARAM,   argumento, _, parámetro) copia el argumento al parámetro
    (GOSUB,   función,   _, inicio)    salta a la función y guarda el regreso
    (ENDFUNC, _,         _, _)         fin de la función: regresa
    (END,     _,         _, _)         fin del programa

El parser llama a los métodos de esta clase desde los puntos neurálgicos.
"""

from cubo_semantico import BOOL, ERROR, FLOAT, INT, tipo_resultante
from errores import ErrorSemantico
from estructuras import Fila, Pila
from memoria import CONSTANTE, LETRERO, MemoriaVirtual, segmento_y_tipo

# Marca que se mete a la pila de operadores al abrir un paréntesis.
FONDO_FALSO = "("

OPERADORES_MULT = ("*", "/")
OPERADORES_SUMA = ("+", "-")
OPERADORES_REL = (">", "<", "!=")

PENDIENTE = None   # destino de un salto que todavía no se conoce


class Cuadruplo:
    """Una instrucción de código intermedio (con direcciones) y su versión legible."""

    def __init__(self, operador, izquierdo, derecho, resultado, legible):
        self.operador = operador
        self.izquierdo = izquierdo
        self.derecho = derecho
        self.resultado = resultado
        self.legible = list(legible)    # (operador, izq, der, res) con nombres

    def como_tupla(self):
        return (self.operador, self.izquierdo, self.derecho, self.resultado)

    def como_tupla_legible(self):
        return tuple(self.legible)

    def rellenar(self, destino):
        """Completa el destino de un salto que se generó pendiente."""
        self.resultado = destino
        self.legible[3] = destino

    @staticmethod
    def _texto(campos):
        return "(" + ", ".join("_" if campo is None else str(campo) for campo in campos) + ")"

    def __str__(self):
        return self._texto(self.como_tupla())

    def texto_legible(self):
        return self._texto(self.legible)

    __repr__ = __str__


class GeneradorCuadruplos:
    """Lleva las pilas, la fila y la memoria, y traduce cada construcción a cuádruplos."""

    def __init__(self, memoria=None, con_traza=False):
        self.memoria = memoria or MemoriaVirtual()
        self.pila_operandos = Pila()
        self.pila_tipos = Pila()
        self.pila_operadores = Pila()
        self.pila_saltos = Pila()
        self.pila_llamadas = Pila()   # [función, argumentos recibidos] de cada llamada abierta
        self.fila = Fila()
        self.nombres = {}             # dirección -> nombre legible (en el alcance actual)
        self.temporales = 0           # para nombrar t1, t2, ... dentro del alcance
        # Si se pide, guarda una "foto" de las pilas después de cada acción.
        self.traza = [] if con_traza else None

    # ------------------------------------------------------------------
    # Apoyo
    # ------------------------------------------------------------------
    @property
    def cuadruplos(self):
        """Los cuádruplos generados, como lista."""
        return self.fila.como_lista()

    @property
    def siguiente(self):
        """Número que tendrá el próximo cuádruplo (se numeran desde 1)."""
        return len(self.fila) + 1

    def nombre(self, direccion):
        return self.nombres.get(direccion, direccion)

    def nuevo_alcance(self):
        """Empieza una función o main: los temporales se vuelven a nombrar desde t1."""
        self.temporales = 0

    def _nuevo_temporal(self, tipo):
        direccion = self.memoria.temporal(tipo)
        self.temporales += 1
        self.nombres[direccion] = f"t{self.temporales}"
        return direccion

    def _generar(self, operador, izquierdo, derecho, resultado, legible=None):
        if legible is None:
            legible = (operador,) + tuple(
                None if campo is None else self.nombre(campo)
                for campo in (izquierdo, derecho, resultado)
            )
        cuadruplo = Cuadruplo(operador, izquierdo, derecho, resultado, legible)
        self.fila.encolar(cuadruplo)
        return cuadruplo

    def _rellenar(self, numero, destino):
        """El cuádruplo `numero` (contando desde 1) era un salto pendiente."""
        self.fila[numero - 1].rellenar(destino)

    def _sacar_operando(self):
        """Saca un operando junto con su tipo (las dos pilas van en paralelo)."""
        return self.pila_operandos.sacar(), self.pila_tipos.sacar()

    def _anotar(self, accion, cuadruplo=None):
        if self.traza is not None:
            self.traza.append({
                "accion": accion,
                "operandos": [self.nombre(d) for d in self.pila_operandos.como_lista()],
                "direcciones": self.pila_operandos.como_lista(),
                "tipos": self.pila_tipos.como_lista(),
                "operadores": self.pila_operadores.como_lista(),
                "saltos": self.pila_saltos.como_lista(),
                "cuadruplo": cuadruplo.texto_legible() if cuadruplo else "",
            })

    # ------------------------------------------------------------------
    # Expresiones (entrega 3, ahora con direcciones)
    # ------------------------------------------------------------------
    def meter_operando(self, direccion, tipo, nombre):
        """Se leyó un id: su dirección va a PilaO y su tipo a PTipos."""
        self.nombres[direccion] = nombre
        self.pila_operandos.meter(direccion)
        self.pila_tipos.meter(tipo)
        self._anotar(f"meter operando {nombre}")

    def meter_constante(self, valor, tipo):
        """Se leyó una constante: se busca (o se crea) su dirección en la tabla de constantes."""
        direccion = self.memoria.constante(valor, tipo)
        self.nombres[direccion] = valor
        self.pila_operandos.meter(direccion)
        self.pila_tipos.meter(tipo)
        self._anotar(f"meter constante {valor}")

    def meter_operador(self, operador):
        """Se leyó un operador: queda pendiente en POper."""
        self.pila_operadores.meter(operador)
        self._anotar(f"meter operador {operador}")

    def meter_fondo_falso(self):
        """Se abrió un paréntesis: el fondo falso tapa los operadores pendientes."""
        self.pila_operadores.meter(FONDO_FALSO)
        self._anotar("meter fondo falso")

    def quitar_fondo_falso(self):
        """Se cerró el paréntesis: se quita la marca."""
        self.pila_operadores.sacar()
        self._anotar("quitar fondo falso")

    def resolver(self, operadores, linea=None):
        """
        Si el operador del tope de POper es uno de `operadores`, se genera su
        cuádruplo: se saca el operador, el operando derecho y el izquierdo (con
        sus tipos), se consulta el cubo semántico, se pide un TEMPORAL del tipo
        resultante (su dirección depende del tipo) y ese temporal se mete a PilaO.
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

        temporal = self._nuevo_temporal(tipo)
        cuadruplo = self._generar(operador, izquierdo, derecho, temporal)
        self.pila_operandos.meter(temporal)
        self.pila_tipos.meter(tipo)
        self._anotar(f"resolver {operador}", cuadruplo)

    def negar(self):
        """
        Menos unario (`-x`). Si el operando es una constante se usa la constante
        con el signo cambiado; si es una variable se genera (neg, x, _, temporal).
        """
        operando, tipo = self._sacar_operando()
        if segmento_y_tipo(operando)[0] == CONSTANTE:
            valor = -self.memoria.valor_de_constante(operando)
            direccion = self.memoria.constante(valor, tipo)
            self.nombres[direccion] = valor
            self.pila_operandos.meter(direccion)
            self.pila_tipos.meter(tipo)
            self._anotar("negar constante")
            return
        temporal = self._nuevo_temporal(tipo)
        cuadruplo = self._generar("neg", operando, None, temporal)
        self.pila_operandos.meter(temporal)
        self.pila_tipos.meter(tipo)
        self._anotar("negar", cuadruplo)

    # ------------------------------------------------------------------
    # Estatutos lineales
    # ------------------------------------------------------------------
    def asignar(self, linea=None):
        """Fin de `id = expresion`: genera (=, valor, _, destino)."""
        self.pila_operadores.sacar()                      # el "="
        valor, tipo_valor = self._sacar_operando()
        destino, tipo_destino = self._sacar_operando()
        if tipo_resultante("=", tipo_destino, tipo_valor) == ERROR:
            raise ErrorSemantico(
                f"no se puede asignar un valor {tipo_valor} a '{self.nombre(destino)}', "
                f"que es {tipo_destino}",
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
        """Un letrero es una constante de texto: también tiene dirección."""
        direccion = self.memoria.constante(texto, LETRERO)
        self.nombres[direccion] = f'"{texto}"'
        cuadruplo = self._generar("print", None, None, direccion)
        self._anotar("generar print", cuadruplo)

    # ------------------------------------------------------------------
    # Estatutos no lineales: if / else / while
    # ------------------------------------------------------------------
    def generar_gotof(self, estatuto, linea=None):
        """
        Fin de la condición de un if o un while. Se saca su resultado, se valida
        que sea booleano y se genera (GOTOF, resultado, _, ???). El destino aún
        no se conoce (es lo que sigue después del cuerpo), así que el número de
        este cuádruplo se guarda en PSaltos para rellenarlo después.
        """
        resultado, tipo = self._sacar_operando()
        if tipo != BOOL:
            raise ErrorSemantico(
                f"la condición del {estatuto} debe ser una comparación (se recibió {tipo})", linea
            )
        cuadruplo = self._generar("GOTOF", resultado, None, PENDIENTE)
        self.pila_saltos.meter(self.siguiente - 1)
        self._anotar(f"GOTOF pendiente ({estatuto})", cuadruplo)

    def generar_else(self):
        """
        Se leyó `else`. Al terminar el bloque verdadero hay que brincar el bloque
        falso: se genera (GOTO, _, _, ???). El GOTOF pendiente ya se puede
        rellenar: si la condición es falsa se brinca justo aquí, al inicio del else.
        """
        cuadruplo = self._generar("GOTO", None, None, PENDIENTE)
        falso = self.pila_saltos.sacar()
        self._rellenar(falso, self.siguiente)
        self.pila_saltos.meter(self.siguiente - 1)
        self._anotar(f"GOTO pendiente; rellenar {falso} con {self.siguiente}", cuadruplo)

    def terminar_if(self):
        """Fin del if: el salto pendiente (GOTOF, o el GOTO del else) brinca aquí."""
        pendiente = self.pila_saltos.sacar()
        self._rellenar(pendiente, self.siguiente)
        self._anotar(f"rellenar {pendiente} con {self.siguiente}")

    def marcar_inicio_ciclo(self):
        """Antes de la condición del while: aquí hay que regresar en cada vuelta."""
        self.pila_saltos.meter(self.siguiente)
        self._anotar(f"guardar regreso {self.siguiente}")

    def terminar_ciclo(self):
        """
        Fin del cuerpo del while: se genera (GOTO, _, _, regreso) para volver a
        evaluar la condición, y el GOTOF pendiente se rellena con lo que sigue.
        """
        falso = self.pila_saltos.sacar()
        regreso = self.pila_saltos.sacar()
        cuadruplo = self._generar("GOTO", None, None, regreso)
        self._rellenar(falso, self.siguiente)
        self._anotar(f"GOTO {regreso}; rellenar {falso} con {self.siguiente}", cuadruplo)

    # ------------------------------------------------------------------
    # Programa y funciones
    # ------------------------------------------------------------------
    def generar_goto_main(self):
        """Primer cuádruplo del programa: brincar las funciones e ir a main."""
        cuadruplo = self._generar("GOTO", None, None, PENDIENTE, ("GOTO", None, None, None))
        self.pila_saltos.meter(self.siguiente - 1)
        self._anotar("GOTO main pendiente", cuadruplo)

    def empezar_main(self):
        """Se llegó a main: el GOTO del primer cuádruplo brinca aquí."""
        self._rellenar(self.pila_saltos.sacar(), self.siguiente)
        self.nuevo_alcance()
        self._anotar(f"rellenar GOTO main con {self.siguiente}")

    def terminar_programa(self):
        self._anotar("fin", self._generar("END", None, None, None))

    def empezar_funcion(self, funcion):
        """Primer estatuto de la función: GOSUB va a brincar a este cuádruplo."""
        funcion.inicio = self.siguiente
        self.nuevo_alcance()

    def terminar_funcion(self):
        self._anotar("fin de función", self._generar("ENDFUNC", None, None, None))

    def generar_era(self, funcion):
        """
        Empieza una llamada: (ERA, _, _, función) le dice a la máquina virtual
        que reserve memoria para la función (cuánta, lo dice su entrada en el
        directorio). Se abre un registro de la llamada para contar argumentos.
        """
        self.pila_llamadas.meter([funcion, 0])
        cuadruplo = self._generar("ERA", None, None, funcion.nombre)
        self._anotar(f"ERA {funcion.nombre}", cuadruplo)

    def generar_param(self, linea=None):
        """
        Se terminó un argumento: su valor está en el tope de PilaO. Se valida
        contra el tipo del parámetro que le toca (con la regla de asignación del
        cubo) y se genera (PARAM, argumento, _, dirección del parámetro).
        """
        argumento, tipo = self._sacar_operando()
        llamada = self.pila_llamadas.tope()
        funcion, k = llamada
        llamada[1] += 1
        if k >= len(funcion.parametros):
            return   # sobran argumentos: el error se reporta en GOSUB, ya con el total
        tipo_parametro = funcion.parametros[k]
        if tipo_resultante("=", tipo_parametro, tipo) == ERROR:
            raise ErrorSemantico(
                f"el argumento {k + 1} de '{funcion.nombre}' debe ser {tipo_parametro} "
                f"(se recibió {tipo})", linea,
            )
        parametro = funcion.direcciones_parametros[k]
        nombre_parametro = [v.nombre for v in funcion.variables if v.es_parametro][k]
        cuadruplo = self._generar(
            "PARAM", argumento, None, parametro,
            ("PARAM", self.nombre(argumento), None, nombre_parametro),
        )
        self._anotar(f"PARAM {k + 1}", cuadruplo)

    def generar_gosub(self, linea=None):
        """Fin de la llamada: se valida el número de argumentos y se genera GOSUB."""
        funcion, recibidos = self.pila_llamadas.sacar()
        esperados = len(funcion.parametros)
        if recibidos != esperados:
            raise ErrorSemantico(
                f"la función '{funcion.nombre}' espera {esperados} argumento"
                f"{'' if esperados == 1 else 's'} y recibió {recibidos}", linea,
            )
        cuadruplo = self._generar("GOSUB", funcion.nombre, None, funcion.inicio)
        self._anotar(f"GOSUB {funcion.nombre}", cuadruplo)

    # ------------------------------------------------------------------
    # Despliegue
    # ------------------------------------------------------------------
    def pilas_vacias(self):
        """Al terminar de compilar no debe quedar nada pendiente en ninguna pila."""
        return all(pila.esta_vacia() for pila in (
            self.pila_operandos, self.pila_tipos, self.pila_operadores,
            self.pila_saltos, self.pila_llamadas))

    def como_texto(self, legible=True):
        """La fila numerada: con direcciones y, al lado, la versión con nombres."""
        renglones = [(numero, str(c), c.texto_legible())
                     for numero, c in enumerate(self.fila, start=1)]
        if not renglones:
            return ""
        ancho = max(len(direcciones) for _, direcciones, _ in renglones)
        return "\n".join(
            f"{numero:>3}: {direcciones:<{ancho}}    {nombres}" if legible
            else f"{numero:>3}: {direcciones}"
            for numero, direcciones, nombres in renglones
        )

    def traza_como_texto(self):
        """Tabla con el contenido de las pilas después de cada acción."""
        def celda(valores):
            return " ".join(str(valor) for valor in valores) or "-"

        renglones = [("ACCIÓN", "PilaO", "PTipos", "POper", "PSaltos", "CUÁDRUPLO")]
        for paso in self.traza or []:
            renglones.append((paso["accion"], celda(paso["operandos"]), celda(paso["tipos"]),
                              celda(paso["operadores"]), celda(paso["saltos"]), paso["cuadruplo"]))
        anchos = [max(len(renglon[i]) for renglon in renglones) for i in range(6)]
        return "\n".join(
            "  ".join(campo.ljust(ancho) for campo, ancho in zip(renglon, anchos)).rstrip()
            for renglon in renglones
        )


def tipo_de_constante(valor):
    """Tipo BabyDuck de una constante numérica de Python."""
    return FLOAT if isinstance(valor, float) else INT


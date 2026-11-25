"""
estructuras.py - Pila y Fila que usa el generador de cuádruplos.

Las dos envuelven estructuras que ya trae Python, pero exponen SOLO las
operaciones propias de cada una. Así el resto del compilador no puede, por
ejemplo, sacar un elemento de en medio de la pila por accidente.

  Pila (LIFO: el último que entra es el primero que sale)
      Se usa para operandos, tipos y operadores. Una expresión se resuelve
      "de adentro hacia afuera": lo último que se leyó es lo primero que se
      necesita, y eso es exactamente una pila.
      Implementación: `list` de Python -> meter y sacar del final cuestan O(1).

  Fila (FIFO: el primero que entra es el primero que sale)
      Guarda los cuádruplos. Se generan en orden y en ese mismo orden se van a
      ejecutar, así que solo se agrega al final y se recorre desde el inicio.
      Implementación (entrega 4): una `list` más un índice al frente.
        * agregar al final -> append, O(1)
        * sacar del frente -> se mueve el índice, O(1) (no se recorre la lista)
        * consultar o rellenar el cuádruplo número i -> acceso por índice, O(1)
      En la entrega 3 era un `deque`, pero un deque cuesta O(n) para llegar a
      un elemento de en medio, y ahora los saltos (GOTO, GOTOF) se generan con
      destino pendiente y hay que regresar a RELLENARLOS por su número.
"""


class Pila:
    """Pila LIFO."""

    def __init__(self):
        self._elementos = []

    def meter(self, elemento):
        """push: pone un elemento en el tope."""
        self._elementos.append(elemento)

    def sacar(self):
        """pop: quita y regresa el elemento del tope."""
        if self.esta_vacia():
            raise IndexError("se intentó sacar de una pila vacía")
        return self._elementos.pop()

    def tope(self):
        """top: regresa el elemento del tope SIN quitarlo (None si está vacía)."""
        return self._elementos[-1] if self._elementos else None

    def esta_vacia(self):
        return not self._elementos

    def como_lista(self):
        """Copia del contenido, del fondo al tope (para mostrar o depurar)."""
        return list(self._elementos)

    def __len__(self):
        return len(self._elementos)

    def __repr__(self):
        return f"Pila({self._elementos})"


class Fila:
    """Fila FIFO que además permite consultar y rellenar un elemento por posición."""

    def __init__(self):
        self._elementos = []
        self._frente = 0        # posición del primer elemento que no se ha desencolado

    def encolar(self, elemento):
        """enqueue: agrega un elemento al final de la fila."""
        self._elementos.append(elemento)

    def desencolar(self):
        """dequeue: quita y regresa el elemento del frente."""
        if self.esta_vacia():
            raise IndexError("se intentó desencolar de una fila vacía")
        elemento = self._elementos[self._frente]
        self._frente += 1
        return elemento

    def frente(self):
        """Regresa el primer elemento SIN quitarlo (None si está vacía)."""
        return None if self.esta_vacia() else self._elementos[self._frente]

    def __getitem__(self, posicion):
        """Elemento en la posición dada (0 = el frente), O(1)."""
        if not 0 <= posicion < len(self):
            raise IndexError(f"la fila no tiene la posición {posicion}")
        return self._elementos[self._frente + posicion]

    def esta_vacia(self):
        return len(self) == 0

    def como_lista(self):
        """Copia del contenido, del frente al final."""
        return self._elementos[self._frente:]

    def __len__(self):
        return len(self._elementos) - self._frente

    def __iter__(self):
        return iter(self.como_lista())

    def __repr__(self):
        return f"Fila({self.como_lista()})"

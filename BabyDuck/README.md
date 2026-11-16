# BabyDuck

Compilador del mini-lenguaje BabyDuck en Python con [PLY](https://www.dabeaz.com/ply/).
Cada entrega está en su propia carpeta y es independiente: trae todo el código
que necesita para correr, más su documento (`documentacion.html`).

| Carpeta    | Entrega                                   | Qué agrega                                                        |
|------------|-------------------------------------------|-------------------------------------------------------------------|
| `Entrega0` | Léxico y gramática                        | Expresiones regulares, tokens y gramática (solo documento)        |
| `Entrega1` | Scanner y parser                          | `lexer.py`, `parser.py`, plan de pruebas                          |
| `Entrega2` | Semántica de variables y cubo semántico   | `cubo_semantico.py`, `directorio.py`, puntos neurálgicos          |
| `Entrega3` | Código de expresiones y estatutos lineales| `estructuras.py` (pilas y fila), `cuadruplos.py`                  |

## Instalación

```bash
cd BabyDuck
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uso

```bash
cd Entrega3
../.venv/bin/python main.py programas/expresiones.bd            # cuádruplos
../.venv/bin/python main.py programas/precedencia.bd --traza    # pilas paso a paso
../.venv/bin/python main.py programas/factorial.bd --tablas     # directorio de funciones
../.venv/bin/python -m unittest -v                              # pruebas
```

Las entregas 1 y 2 se usan igual (`main.py` y `python -m unittest` dentro de su carpeta).

## Documentación

`docs/` tiene la fuente de los documentos. `docs/build.py` los arma y sustituye
los marcadores `{{...}}` por la salida real del código, así el documento nunca
muestra algo distinto a lo que el compilador produce:

```bash
.venv/bin/python docs/build.py
```

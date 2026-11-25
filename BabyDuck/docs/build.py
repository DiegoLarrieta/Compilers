"""
build.py - Arma la documentación (un HTML por entrega).

Cada `EntregaN/documentacion.html` se arma con:
    docs/estilo.css + docs/entregaN.html (el contenido) + docs/diagramas.js

El contenido puede incluir marcadores que se sustituyen por datos REALES, para
que el documento nunca muestre una salida distinta a la que da el código:

    {{archivo:Entrega3/programas/x.bd}}     contenido de un archivo
    {{cmd:Entrega3|main.py programas/x.bd}} salida de correr python en esa carpeta
    {{gramatica:Entrega1}}                  gramática que PLY registró en esa entrega

Uso (desde la carpeta BabyDuck):
    .venv/bin/python docs/build.py
"""

import html
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(RAIZ, "docs")

ENTREGAS = [
    ("Entrega 0", "Léxico y gramática", "Expresiones regulares, tokens y gramática libre de contexto de BabyDuck."),
    ("Entrega 1", "Scanner y parser", "Selección de herramienta, scanner y parser en Python con PLY, y plan de pruebas."),
    ("Entrega 2", "Semántica de variables", "Cubo semántico, directorio de funciones, tablas de variables y sus puntos neurálgicos."),
    ("Entrega 3", "Cuádruplos", "Pilas, fila y traducción de expresiones y estatutos lineales a cuádruplos."),
    ("Entrega 4", "Estatutos, funciones y direcciones virtuales",
     "Cuádruplos de if, else y while; declaración e invocación de funciones; direcciones virtuales."),
]

FUENTES = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
           'family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600'
           '&family=Space+Grotesk:wght@500;600;700&display=swap">')


def leer(*partes):
    with open(os.path.join(*partes), encoding="utf-8") as archivo:
        return archivo.read()


def correr(carpeta, argumentos):
    """Corre python en la carpeta de una entrega y regresa lo que imprimió."""
    proceso = subprocess.run(
        [sys.executable] + argumentos, cwd=os.path.join(RAIZ, carpeta),
        capture_output=True, text=True,
    )
    return (proceso.stdout + proceso.stderr).strip("\n")


def gramatica(carpeta):
    """Le pide a PLY las producciones registradas y las acomoda en BNF."""
    salida = correr(carpeta, ["-c", "import parser\nfor p in parser._parser.productions[1:]: print(p)"])
    lineas, anterior = [], None
    for produccion in salida.splitlines():
        izquierda, derecha = produccion.split(" -> ")
        derecha = derecha.replace("<empty>", "ε")
        if izquierda == "empty":
            continue
        derecha = derecha.replace("empty", "ε")
        if izquierda != anterior:
            if anterior is not None:
                lineas.append("")
            lineas.append(f"{izquierda} ::= {derecha}")
        else:
            lineas.append(" " * len(izquierda) + f"   | {derecha}")
        anterior = izquierda
    return "\n".join(lineas)


def sustituir(marcador):
    tipo, _, valor = marcador.group(1).partition(":")
    if tipo == "archivo":
        texto = leer(RAIZ, valor).rstrip("\n")
    elif tipo == "cmd":
        carpeta, _, argumentos = valor.partition("|")
        texto = correr(carpeta, argumentos.split())
    elif tipo == "gramatica":
        texto = gramatica(valor)
    else:
        raise ValueError(f"marcador desconocido: {marcador.group(0)}")
    return html.escape(texto, quote=False)


def construir(numero):
    nombre, titulo, resumen = ENTREGAS[numero]
    ruta = "".join(
        f'<li{" aria-current=\"step\"" if i == numero else ""}>{n} · {t}</li>'
        for i, (n, t, _) in enumerate(ENTREGAS)
    )
    cuerpo = re.sub(r"\{\{(.+?)\}\}", sustituir, leer(DOCS, f"entrega{numero}.html"))
    pagina = f"""<meta charset="utf-8">
<meta name="claude:viewport-fit-sides" content="cover">
<title>BabyDuck {nombre}</title>
{FUENTES}
<style>
{leer(DOCS, "estilo.css")}</style>
<main class="pagina">
<p class="eyebrow">TC3002B · Compiladores · Proyecto BabyDuck</p>
<h1>{nombre}: {titulo}</h1>
<p class="lead">{resumen}</p>
<ol class="ruta" aria-label="Entregas del proyecto">{ruta}</ol>
{cuerpo}
</main>
<script>
{leer(DOCS, "diagramas.js")}</script>
"""
    destino = os.path.join(RAIZ, f"Entrega{numero}", "documentacion.html")
    with open(destino, "w", encoding="utf-8") as archivo:
        archivo.write(pagina)
    print(f"{os.path.relpath(destino, RAIZ)}  ({len(pagina) // 1024} KB)")


# ---------------------------------------------------------------------------
# Versión formal para Canvas: portada + encabezado con logo, lista para PDF
# ---------------------------------------------------------------------------
ALUMNO = "Luis Diego Dominguez Larrieta A01275640"
MATRICULA = "A01275640"
PROFESORA = "Elda Quiroga"
MATERIA = "Desarrollo de aplicaciones avanzadas de ciencias computacionales"
CLAVE = "TC3002B"
# Fecha y subtítulo de la portada formal de cada entrega.
FECHAS = {3: "15 de noviembre del 2026", 4: "22 de noviembre del 2026"}
SUBTITULOS = {3: "código de expresiones y estatutos",
              4: "entrega #4"}
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def construir_formal(numero):
    """Genera EntregaN/<matrícula>_entregaN.html y, si hay Chrome, el PDF."""
    import base64

    nombre, titulo, _ = ENTREGAS[numero]
    with open(os.path.join(DOCS, "logo_tec.png"), "rb") as archivo:
        logo = "data:image/png;base64," + base64.b64encode(archivo.read()).decode()
    cuerpo = re.sub(r"\{\{(.+?)\}\}", sustituir, leer(DOCS, f"entrega{numero}.html"))
    pagina = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>{MATRICULA}_entrega{numero}</title>
<style>
{leer(DOCS, "formal.css")}</style></head><body>
<section class="portada">
<img src="{logo}" alt="Tecnológico de Monterrey">
<h1>{nombre}</h1>
<p>{ALUMNO}</p>
<p>Profesora: {PROFESORA}</p>
<p>{FECHAS[numero]}</p>
<p class="materia">{CLAVE}</p>
<p>{MATERIA}</p>
</section>
<table class="hoja"><thead><tr><td><img src="{logo}" alt=""></td></tr></thead>
<tbody><tr><td>
<p class="titulo">BabyDuck: {titulo} ({SUBTITULOS[numero]})</p>
{cuerpo}
</td></tr></tbody></table>
<script>
{leer(DOCS, "diagramas.js")}</script>
</body></html>
"""
    base = os.path.join(RAIZ, f"Entrega{numero}", f"{MATRICULA}_entrega{numero}")
    with open(base + ".html", "w", encoding="utf-8") as archivo:
        archivo.write(pagina)
    if os.path.exists(CHROME):
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={base}.pdf", "file://" + base + ".html"],
                       capture_output=True)
        print(os.path.relpath(base + ".pdf", RAIZ))


if __name__ == "__main__":
    if "--formal" in sys.argv:
        construir_formal(int(sys.argv[sys.argv.index("--formal") + 1]))
        sys.exit()
    for numero in range(len(ENTREGAS)):
        if os.path.exists(os.path.join(DOCS, f"entrega{numero}.html")):
            construir(numero)

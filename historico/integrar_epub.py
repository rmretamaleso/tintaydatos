#!/usr/bin/env python3
"""
integrar_epub.py — deja el pipeline listo para publicar EPUB junto al PDF.

Aplica cuatro cambios, cada uno verificando antes que el código sea el
esperado. Si algo no coincide, se detiene sin tocar nada más.

  1. R2_upload/subir_a_r2.py  tipo de contenido según la extensión
  2. catalogo.csv             columna nueva url_epub, después de urls
  3. publicar.py              escribe url_epub en la fila del catálogo
  4. generar_fichas.py        botón de descarga del EPUB en la ficha

Uso:
    python3 integrar_epub.py              # simula
    python3 integrar_epub.py --aplicar
"""
import csv
import io
import os
import shutil
import sys
from pathlib import Path

APLICAR = "--aplicar" in sys.argv
hechos, fallos = [], []


def editar(ruta, viejo, nuevo, etiqueta, marca):
    """`marca` es un fragmento que solo aparece si el cambio ya se aplicó.
    Comparar los primeros caracteres del texto nuevo no sirve: en varios
    parches el bloque empieza igual que el viejo y daría un falso positivo."""
    if not os.path.exists(ruta):
        fallos.append(f"{etiqueta}: no existe {ruta}")
        return
    s = open(ruta, encoding="utf-8").read()
    if marca in s:
        hechos.append(f"{etiqueta}: ya estaba aplicado")
        return
    if viejo not in s:
        fallos.append(f"{etiqueta}: no encontré el código esperado en {ruta}")
        return
    if APLICAR:
        shutil.copy(ruta, ruta + ".bak")
        open(ruta, "w", encoding="utf-8").write(s.replace(viejo, nuevo, 1))
    hechos.append(f"{etiqueta}: {'aplicado' if APLICAR else 'listo para aplicar'}")


# ---------------------------------------------------------------- 1
editar(
    "R2_upload/subir_a_r2.py",
    '    extra_args = {"ContentType": "application/pdf", "CacheControl": "public, max-age=31536000"}',
    '''    # El tipo se deduce de la extensión: un EPUB servido como application/pdf
    # hace que el navegador lo trate como binario en vez de abrir el lector.
    TIPOS = {".pdf": "application/pdf", ".epub": "application/epub+zip"}
    tipo = TIPOS.get(Path(ruta_local).suffix.lower(), "application/octet-stream")
    extra_args = {"ContentType": tipo, "CacheControl": "public, max-age=31536000"}''',
    "1 tipo de contenido", marca='"application/epub+zip"')

# ---------------------------------------------------------------- 2
def columna_catalogo(ruta="catalogo.csv"):
    if not os.path.exists(ruta):
        fallos.append(f"2 columna url_epub: no existe {ruta}")
        return
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    campos = list(filas[0].keys())
    if "url_epub" in campos:
        hechos.append("2 columna url_epub: ya existía")
        return
    if "urls" not in campos:
        fallos.append("2 columna url_epub: no encuentro la columna 'urls'")
        return
    nuevos = campos[:campos.index("urls") + 1] + ["url_epub"] + campos[campos.index("urls") + 1:]
    if APLICAR:
        shutil.copy(ruta, ruta + ".bak")
        salida = io.StringIO()
        w = csv.DictWriter(salida, fieldnames=nuevos, lineterminator="\n")
        w.writeheader()
        for f in filas:
            f.setdefault("url_epub", "")
            w.writerow(f)
        Path(ruta).write_text(salida.getvalue(), encoding="utf-8")
    hechos.append(f"2 columna url_epub: {'añadida' if APLICAR else 'lista para añadir'} "
                  f"tras 'urls' ({len(filas)} filas)")


columna_catalogo()

# ---------------------------------------------------------------- 3
editar(
    "publicar.py",
    """def actualizar_catalogo(cfg, pdfs, ruta_csv="catalogo.csv", notas=None,
                        piezas=None):""",
    """def actualizar_catalogo(cfg, pdfs, ruta_csv="catalogo.csv", notas=None,
                        piezas=None, epub=None):""",
    "3a firma de actualizar_catalogo", marca="piezas=None, epub=None")

editar(
    "publicar.py",
    """    fuente = cfg.get("fuente", {}).get("texto", "")""",
    """    # El EPUB va en su propia columna: una obra en varios volúmenes tiene
    # varios PDF pero un solo EPUB, así que no caben en el mismo campo.
    if "url_epub" in campos:
        destino["url_epub"] = f"{R2_BASE}/{Path(epub).name}" if epub else ""

    fuente = cfg.get("fuente", {}).get("texto", "")""",
    "3b escritura de url_epub", marca='destino["url_epub"]')

# ---------------------------------------------------------------- 4
editar(
    "generar_fichas.py",
    """    elif propia:
        botones = f'<a class="descarga" href="{e(enlaces[0])}">Descargar el PDF</a>'
    else:
        botones = f'<a class="descarga" href="{e(enlaces[0])}">Ver en la fuente</a>'""",
    """    elif propia:
        botones = f'<a class="descarga" href="{e(enlaces[0])}">Descargar el PDF</a>'
    else:
        botones = f'<a class="descarga" href="{e(enlaces[0])}">Ver en la fuente</a>'

    # El EPUB se ofrece aparte: es un solo archivo aunque el PDF vaya en varios
    # volúmenes, y es el formato que funciona en móvil y con lector de pantalla.
    if propia and (r.get("url_epub") or "").strip():
        botones += (f'\\n  <a class="descarga secundaria" href="{e(r["url_epub"])}">'
                    f'Descargar el EPUB</a>')""",
    "4a botón de EPUB", marca="Descargar el EPUB")

editar(
    "generar_fichas.py",
    """  .descarga:hover{{ background:#573d70; }}""",
    """  .descarga:hover{{ background:#573d70; }}
  .descarga.secundaria{{ background:transparent; color:#6B4C8C;
    border:1.5px solid #6B4C8C; margin-left:10px; }}
  .descarga.secundaria:hover{{ background:#e2d7ec; color:#573d70; }}""",
    "4b estilo del botón secundario", marca="descarga.secundaria")

# ---------------------------------------------------------------- informe
print("CAMBIOS")
for h in hechos:
    print("  ok   ", h)
for f in fallos:
    print("  FALLA", f)
print()
if fallos:
    print("Hay fallos: revisa esos archivos a mano antes de seguir.")
    sys.exit(1)
if not APLICAR:
    print("Simulación. Añade --aplicar para escribir (deja .bak de cada archivo).")
else:
    print("Aplicado. Falta a mano, en tinta.py:")
    print("  - subir el EPUB:      publicar.subir(salidas + [epub], dry_run=a.dry_run)")
    print("  - pasarlo al catálogo: publicar.actualizar_catalogo(..., epub=epub)")

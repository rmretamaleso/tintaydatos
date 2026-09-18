#!/usr/bin/env python3
"""
preparar_lote.py — dos cambios para poder generar los EPUB que faltan sin
tocar los PDF ya publicados.

  1. edicion.py  declara el idioma en los PDF nuevos, igual que hizo
                 parchear_pdfs.py con los 706 existentes
  2. tinta.py    opción --solo-epub: descarga, parsea y genera solo el EPUB,
                 sin maquetar PDF ni publicar nada

Uso:
    python3 preparar_lote.py              # simula
    python3 preparar_lote.py --aplicar
"""
import os
import shutil
import sys

APLICAR = "--aplicar" in sys.argv
hechos, fallos = [], []


def editar(ruta, viejo, nuevo, etiqueta, marca):
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
    "edicion.py",
    """    doc = SimpleDocTemplate(salida, pagesize=A5,
                            topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                            leftMargin=2.2 * cm, rightMargin=2 * cm,
                            title=obra["titulo"], author=obra["autor"])""",
    """    doc = SimpleDocTemplate(salida, pagesize=A5,
                            topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                            leftMargin=2.2 * cm, rightMargin=2 * cm,
                            title=obra["titulo"], author=obra["autor"])
    # Accesibilidad: sin /Lang, un lector de pantalla pronuncia el castellano
    # con las reglas del idioma del sistema. Y DisplayDocTitle hace que el
    # visor anuncie el título de la obra en vez del nombre del archivo.
    # ReportLab no puede etiquetar el PDF; esto es lo que sí permite.
    from reportlab.pdfbase.pdfdoc import PDFDictionary, PDFName, PDFString
    doc._doc.Catalog.Lang = PDFString("es-ES")
    doc._doc.Catalog.ViewerPreferences = PDFDictionary(
        {"DisplayDocTitle": PDFName("true")})""",
    "1 idioma en los PDF nuevos", marca="Catalog.Lang")

# ---------------------------------------------------------------- 2
editar(
    "tinta.py",
    """    ap.add_argument("--catalogo", default="catalogo.csv")""",
    """    ap.add_argument("--solo-epub", action="store_true",
                    help="genera solo el EPUB, sin maquetar PDF ni publicar")
    ap.add_argument("--catalogo", default="catalogo.csv")""",
    "2a opción --solo-epub", marca="--solo-epub")

editar(
    "tinta.py",
    """    if not (a.pdf or a.publicar):
        return True""",
    """    # Para las obras que ya tienen PDF publicado: se aprovecha la descarga y
    # el parseo, y se produce solo el EPUB. Así el lote no vuelve a maquetar
    # 706 PDF ni arriesga diferencias de composición con los que ya están.
    if a.solo_epub:
        generar_epub.generar(obra, f"epub/{slug}-tinta-y-datos.epub",
                             dominio=cfg.get("catalogo_campos", {}).get("dominio"))
        return True

    if not (a.pdf or a.publicar):
        return True""",
    "2b flujo de --solo-epub", marca="a.solo_epub")

print("CAMBIOS")
for h in hechos:
    print("  ok   ", h)
for f in fallos:
    print("  FALLA", f)
print()
if fallos:
    sys.exit(1)
print("Simulación. Añade --aplicar para escribir." if not APLICAR
      else "Aplicado. Comprueba con: python3 tinta.py <obra>.json --solo-epub")

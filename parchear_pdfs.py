#!/usr/bin/env python3
"""
parchear_pdfs.py — añade metadatos de accesibilidad a los PDF ya generados.

Inyecta en el catálogo de cada PDF:
  /Lang               idioma del documento, para que el lector de pantalla
                      use la pronunciación correcta
  /ViewerPreferences  DisplayDocTitle, para que el visor anuncie el título de
                      la obra y no el nombre del archivo

No vuelve a maquetar nada: abre el PDF, escribe esas dos entradas y lo guarda.
Páginas, texto, tipografías y metadatos existentes quedan igual.

Lo que NO hace: etiquetar el PDF. Eso requiere un árbol de estructura que
ReportLab no puede generar. Para accesibilidad real hace falta otro formato.

Uso:
    python3 parchear_pdfs.py pdf/              # simula
    python3 parchear_pdfs.py pdf/ --aplicar
"""
import glob
import os
import shutil
import sys
import tempfile

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

IDIOMA = "es-ES"


def ya_parcheado(ruta):
    try:
        return PdfReader(ruta).trailer["/Root"].get("/Lang") is not None
    except Exception:
        return False


def parchear(ruta):
    """Escribe sobre un temporal y solo sustituye si el resultado es legible."""
    w = PdfWriter(clone_from=ruta)
    w._root_object[NameObject("/Lang")] = TextStringObject(IDIOMA)
    vp = DictionaryObject()
    vp[NameObject("/DisplayDocTitle")] = NameObject("/true")
    w._root_object[NameObject("/ViewerPreferences")] = vp

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False,
                                      dir=os.path.dirname(ruta) or ".")
    try:
        with open(tmp.name, "wb") as f:
            w.write(f)
        # Verificación antes de pisar el original
        comp = PdfReader(tmp.name)
        if comp.trailer["/Root"].get("/Lang") != IDIOMA:
            raise ValueError("el idioma no quedó escrito")
        if len(comp.pages) != len(PdfReader(ruta).pages):
            raise ValueError("cambió el número de páginas")
        shutil.move(tmp.name, ruta)
        return True, None
    except Exception as e:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        return False, str(e)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    destino = sys.argv[1]
    aplicar = "--aplicar" in sys.argv

    archivos = (sorted(glob.glob(os.path.join(destino, "*.pdf")))
                if os.path.isdir(destino) else [destino])
    if not archivos:
        sys.exit(f"No hay PDF en {destino}")

    pendientes = [a for a in archivos if not ya_parcheado(a)]
    print(f"{len(archivos)} PDF encontrados")
    print(f"  ya con idioma declarado: {len(archivos) - len(pendientes)}")
    print(f"  por parchear           : {len(pendientes)}")

    if not aplicar:
        for a in pendientes[:5]:
            print(f"    {os.path.basename(a)}")
        if len(pendientes) > 5:
            print(f"    ... y {len(pendientes)-5} más")
        print("\nSimulación. Añade --aplicar para escribirlos.")
        return

    ok, fallos = 0, []
    for i, a in enumerate(pendientes, 1):
        bien, err = parchear(a)
        if bien:
            ok += 1
        else:
            fallos.append((os.path.basename(a), err))
        if i % 100 == 0:
            print(f"  {i}/{len(pendientes)}...")

    print(f"\nParcheados: {ok}")
    if fallos:
        print(f"Fallidos: {len(fallos)} (el original quedó intacto)")
        for n, e in fallos[:5]:
            print(f"  {n}: {e}")
    print("\nSiguiente paso: volver a subirlos a R2 para que sirvan la versión nueva.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
integrar_licencias.py — registra la licencia de las obras enlazadas.

La mayor parte del catálogo es dominio público y no impone condiciones. Pero
unas pocas entradas son material con licencia Creative Commons, que sí exige
atribución con cuatro elementos: título, autoría, fuente y licencia enlazada.
Sin mostrar la licencia, la atribución queda incompleta.

Aplica tres cambios:

  1. catalogo.csv      columnas licencia y licencia_url, después de tipo
  2. rellenado         deduce la licencia del campo tipo donde consta
  3. generar_fichas.py muestra la atribución en la ficha

Criterios:
  - La columna es solo para la licencia de la OBRA ENLAZADA. Las políticas de
    acceso —«descarga liberada», «acceso abierto»— no son licencias con
    cláusulas y se quedan en el campo tipo.
  - La licencia de la maquetación propia (CC BY-SA 4.0) no va aquí: es la
    misma para las 695 ediciones y vive en el colofón y en el Impressum.

Uso:
    python3 integrar_licencias.py              # simula
    python3 integrar_licencias.py --aplicar
"""
import csv
import io
import os
import re
import shutil
import sys
from pathlib import Path

APLICAR = "--aplicar" in sys.argv
hechos, fallos = [], []

# Identificadores reconocidos en el campo tipo -> (etiqueta, url)
LICENCIAS = {
    "cc by 4.0": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/deed.es"),
    "cc by 3.0": ("CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/deed.es"),
    "cc by-sa 4.0": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/deed.es"),
    "cc by-sa 3.0": ("CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/deed.es"),
    "cc by-nc 4.0": ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/deed.es"),
    "cc by-nd 4.0": ("CC BY-ND 4.0", "https://creativecommons.org/licenses/by-nd/4.0/deed.es"),
    "cc0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/deed.es"),
}


def deducir(tipo):
    t = (tipo or "").lower()
    for clave, (etiqueta, url) in LICENCIAS.items():
        if clave in t:
            return etiqueta, url
    return "", ""


# ---------------------------------------------------------------- 1 y 2
def columnas_y_rellenado(ruta="catalogo.csv"):
    if not os.path.exists(ruta):
        fallos.append(f"1 columnas: no existe {ruta}")
        return
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    campos = list(filas[0].keys())

    nuevas = [c for c in ("licencia", "licencia_url") if c not in campos]
    if nuevas:
        if "tipo" not in campos:
            fallos.append("1 columnas: no encuentro la columna 'tipo'")
            return
        i = campos.index("tipo") + 1
        campos = campos[:i] + nuevas + campos[i:]
        hechos.append(f"1 columnas: {'añadidas' if APLICAR else 'listas'} "
                      f"({', '.join(nuevas)}) tras 'tipo'")
    else:
        hechos.append("1 columnas: ya existían")

    rellenadas = []
    for f in filas:
        f.setdefault("licencia", "")
        f.setdefault("licencia_url", "")
        if (f.get("licencia") or "").strip():
            continue
        etiqueta, url = deducir(f.get("tipo"))
        if etiqueta:
            f["licencia"], f["licencia_url"] = etiqueta, url
            rellenadas.append((f["id"], f["titulo"][:38], etiqueta))

    hechos.append(f"2 rellenado: {len(rellenadas)} entradas con licencia deducida "
                  f"de 'tipo'")
    for cid, titulo, etiqueta in rellenadas[:10]:
        hechos.append(f"      [{cid}] {titulo:40} {etiqueta}")
    if len(rellenadas) > 10:
        hechos.append(f"      ... y {len(rellenadas)-10} más")

    if APLICAR:
        shutil.copy(ruta, ruta + ".bak")
        salida = io.StringIO()
        w = csv.DictWriter(salida, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
        Path(ruta).write_text(salida.getvalue(), encoding="utf-8")


columnas_y_rellenado()


# ---------------------------------------------------------------- 3
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


editar(
    "generar_fichas.py",
    """    proc = ""
    if r.get("fuente"):""",
    """    # Atribución de las obras con licencia. Creative Commons exige cuatro
    # elementos: título, autoría, fuente y licencia enlazada. Los tres primeros
    # ya salen arriba en la ficha; este bloque aporta el cuarto.
    licencia = ""
    if (r.get("licencia") or "").strip():
        enlace = (f'<a href="{e(r["licencia_url"])}" rel="license">'
                  f'{e(r["licencia"])}</a>') if (r.get("licencia_url") or "").strip() \\
                 else e(r["licencia"])
        licencia = (f'<p class="fuente">Obra publicada bajo licencia {enlace}. '
                    f'Tinta y Datos la enlaza sin modificarla.</p>')

    proc = ""
    if r.get("fuente"):""",
    "3a bloque de atribución", marca='rel="license"')

editar(
    "generar_fichas.py",
    """    if r.get("notas", "").strip():
        proc += f'<p class="fuente">{e(r["notas"])}</p>'""",
    """    if r.get("notas", "").strip():
        proc += f'<p class="fuente">{e(r["notas"])}</p>'
    proc += licencia""",
    "3b inserción en la ficha", marca="proc += licencia")

print("CAMBIOS")
for h in hechos:
    print("  ok   " if not h.startswith("      ") else "", h)
for f in fallos:
    print("  FALLA", f)
print()
if fallos:
    sys.exit(1)
if not APLICAR:
    print("Simulación. Añade --aplicar para escribir (deja .bak de cada archivo).")
else:
    print("Aplicado. Falta:")
    print("  - añadir 'licencia' y 'licencia_url' a la lista de sync_catalogo.py")
    print("  - python3 generar_fichas.py --escribir")

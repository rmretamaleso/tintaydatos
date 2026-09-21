#!/usr/bin/env python3
"""
integrar_notas_internas.py — separa las anotaciones de trabajo del texto
que se publica.

El campo `notas` se imprime tal cual en la ficha de la obra. Eso significa que
cualquier apunte de verificación escrito ahí acaba publicado en el sitio. Con
un catálogo que crece, el descuido es cuestión de tiempo.

La columna `notas_internas` no se exporta al índice ni aparece en la ficha:
es el sitio donde anotar dudas, pendientes y comprobaciones.

Aplica tres cambios:

  1. catalogo.csv       columna notas_internas, después de notas
  2. sync_catalogo.py   la excluye explícitamente de la exportación
  3. auditar            informe de las notas que parecen anotaciones internas

Uso:
    python3 integrar_notas_internas.py              # simula y audita
    python3 integrar_notas_internas.py --aplicar
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

# Señales de que una nota está escrita para ti y no para quien lee la ficha
MARCAS = re.compile(
    r"corrección:|no lo pude|no pude|revisar|pendiente|ojo:|todo:|"
    r"verificar si|herramientas|comprobar|falta confirmar|¿",
    re.I)


def columna(ruta="catalogo.csv"):
    if not os.path.exists(ruta):
        fallos.append(f"1 columna: no existe {ruta}")
        return []
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    campos = list(filas[0].keys())

    if "notas_internas" in campos:
        hechos.append("1 columna: ya existía")
    else:
        if "notas" not in campos:
            fallos.append("1 columna: no encuentro la columna 'notas'")
            return filas
        i = campos.index("notas") + 1
        campos = campos[:i] + ["notas_internas"] + campos[i:]
        hechos.append(f"1 columna: {'añadida' if APLICAR else 'lista'} tras 'notas'")

    for f in filas:
        f.setdefault("notas_internas", "")

    if APLICAR:
        shutil.copy(ruta, ruta + ".bak")
        s = io.StringIO()
        w = csv.DictWriter(s, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
        Path(ruta).write_text(s.getvalue(), encoding="utf-8")
    return filas


filas = columna()


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


# El aviso de sync_catalogo lista las columnas que no se exportan. Declarar
# notas_internas como deliberada evita que alguien la añada por error al ver
# el aviso y pensar que es un olvido.
editar(
    "sync_catalogo.py",
    "OPCIONALES = {",
    '# Nunca se exporta: es el campo de anotaciones de trabajo.\nNO_PUBLICAR = {"notas_internas"}\n\nOPCIONALES = {',
    "2 sync_catalogo declara la columna", marca="NO_PUBLICAR")

print("CAMBIOS")
for h in hechos:
    print("  ok   ", h)
for f in fallos:
    print("  FALLA", f)

# ---------------------------------------------------------------- auditoría
if filas:
    sosp = [f for f in filas
            if (f.get("notas") or "").strip() and MARCAS.search(f["notas"])]
    print(f"\nNOTAS QUE PARECEN INTERNAS: {len(sosp)}")
    for f in sosp:
        print(f"  [{f['id']}] {f['titulo'][:34]:36} {f['notas'][:64]}…")
    if sosp:
        print("\nRevísalas: lo que sea apunte de trabajo, muévelo a notas_internas.")
        print("La detección es orientativa, no todas lo serán.")

print()
if fallos:
    sys.exit(1)
print("Simulación. Añade --aplicar para escribir." if not APLICAR
      else "Aplicado. Recuerda: python3 sync_catalogo.py --escribir")

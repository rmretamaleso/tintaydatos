#!/usr/bin/env python3
"""
limpiar_duplicados.py — quita columnas repetidas de un CSV.

Conserva la PRIMERA aparición de cada nombre de columna y descarta las demás.
Escribe sobre el archivo y deja copia en .bak

Uso: python3 limpiar_duplicados.py catalogo.csv
"""
import csv, shutil, sys

ruta = sys.argv[1] if len(sys.argv) > 1 else "catalogo.csv"
with open(ruta, encoding="utf-8") as f:
    filas = list(csv.reader(f))

cabecera = filas[0]
vistos, quedan = set(), []
for i, c in enumerate(cabecera):
    if c not in vistos:
        vistos.add(c); quedan.append(i)

repetidas = len(cabecera) - len(quedan)
if repetidas == 0:
    print(f"{ruta}: sin columnas repetidas, no se toca.")
    sys.exit(0)

shutil.copy(ruta, ruta + ".bak")
with open(ruta, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    for fila in filas:
        w.writerow([fila[i] if i < len(fila) else "" for i in quedan])

print(f"{ruta}: {repetidas} columnas repetidas eliminadas, quedan {len(quedan)}.")
print(f"Copia de seguridad en {ruta}.bak")
print("Columnas finales:", ", ".join(cabecera[i] for i in quedan))

#!/usr/bin/env python3
"""
lote_subir_epub.py — sube a R2 los EPUB ya generados y escribe su url_epub
en el catálogo.

No genera nada: los EPUB tienen que existir en epub/. Se empareja cada archivo
con su fila usando el slug de los .json de obras/, que es donde consta el
catalogo_id. Emparejar por nombre de archivo no bastaría: Fortunata y Jacinta
tiene cuatro PDF y un solo EPUB.

Salta las filas que ya tienen url_epub, así que se puede parar y reanudar.
El catálogo se escribe cada 20 obras y al terminar, para que una interrupción
no pierda el trabajo hecho.

Uso:
    python3 lote_subir_epub.py                    # informe
    python3 lote_subir_epub.py --aplicar
    python3 lote_subir_epub.py --aplicar --limite 5
"""
import argparse
import csv
import glob
import io
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

R2_BASE = "https://archivos.tintaydatos.com/ediciones"
REGISTRO = "lote_subir_epub.log"


def anotar(linea):
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')}\t{linea}\n")


def mapa_slug_a_id(carpeta="obras"):
    """slug -> catalogo_id, tomado de los .json. Es la relación autorizada."""
    m = {}
    for ruta in glob.glob(os.path.join(carpeta, "*.json")):
        try:
            d = json.load(open(ruta, encoding="utf-8"))
        except Exception:
            continue
        if d.get("slug") and d.get("catalogo_id") is not None:
            m[d["slug"]] = str(d["catalogo_id"])
    return m


def guardar(ruta_csv, campos, filas):
    salida = io.StringIO()
    w = csv.DictWriter(salida, fieldnames=campos, lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    Path(ruta_csv).write_text(salida.getvalue(), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--catalogo", default="catalogo.csv")
    ap.add_argument("--script", default="R2_upload/subir_a_r2.py")
    a = ap.parse_args()

    filas = list(csv.DictReader(open(a.catalogo, encoding="utf-8")))
    campos = list(filas[0].keys())
    if "url_epub" not in campos:
        sys.exit(f"{a.catalogo} no tiene la columna 'url_epub'.")
    por_id = {f["id"]: f for f in filas}

    slugs = mapa_slug_a_id()
    pendientes, sin_fila, ya = [], [], 0

    for ruta in sorted(glob.glob("epub/*.epub")):
        slug = os.path.basename(ruta).replace("-tinta-y-datos.epub", "")
        cid = slugs.get(slug)
        fila = por_id.get(cid) if cid else None
        if fila is None:
            sin_fila.append(os.path.basename(ruta))
        elif (fila.get("url_epub") or "").strip():
            ya += 1
        else:
            pendientes.append((ruta, fila))

    print(f"EPUB en epub/        : {len(glob.glob('epub/*.epub'))}")
    print(f"  ya en el catálogo  : {ya}")
    print(f"  por subir          : {len(pendientes)}")
    if sin_fila:
        print(f"  SIN FILA en el catálogo: {len(sin_fila)}")
        for n in sin_fila[:8]:
            print(f"      {n}")

    if a.limite:
        pendientes = pendientes[:a.limite]
        print(f"  esta pasada        : {len(pendientes)}")

    if not a.aplicar:
        for ruta, fila in pendientes[:8]:
            print(f"    {os.path.basename(ruta):48} -> fila {fila['id']}")
        if len(pendientes) > 8:
            print(f"    ... y {len(pendientes)-8} más")
        print("\nSimulación. Añade --aplicar para subirlos.")
        return

    anotar(f"INICIO\t{len(pendientes)} pendientes")
    bien, mal, desde_guardado = 0, [], 0
    try:
        for i, (ruta, fila) in enumerate(pendientes, 1):
            nombre = os.path.basename(ruta)
            print(f"[{i}/{len(pendientes)}] {nombre}", flush=True)
            r = subprocess.run([sys.executable, a.script, ruta,
                                "--prefix", "ediciones/"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                motivo = (r.stderr or r.stdout or "sin salida").strip().splitlines()
                motivo = motivo[-1][:160] if motivo else "sin salida"
                mal.append((nombre, motivo))
                anotar(f"FALLA\t{nombre}\t{motivo}")
                print(f"    FALLA: {motivo}", flush=True)
                continue

            fila["url_epub"] = f"{R2_BASE}/{nombre}"
            bien += 1
            desde_guardado += 1
            anotar(f"OK\t{nombre}\tfila {fila['id']}")

            if desde_guardado >= 20:
                guardar(a.catalogo, campos, filas)
                desde_guardado = 0
                print("    (catálogo guardado)", flush=True)
    finally:
        guardar(a.catalogo, campos, filas)

    print(f"\nSubidos: {bien}    Fallidos: {len(mal)}")
    anotar(f"FIN\tok={bien}\tfallos={len(mal)}")
    if mal:
        print("\nFallaron (relanza el lote para reintentarlos):")
        for n, motivo in mal[:15]:
            print(f"  {n:46} {motivo}")
    print("\nDespués: python3 sync_catalogo.py --escribir "
          "&& python3 generar_fichas.py --escribir && python3 generar_sitemap.py")


if __name__ == "__main__":
    main()

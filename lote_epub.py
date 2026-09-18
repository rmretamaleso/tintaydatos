#!/usr/bin/env python3
"""
lote_epub.py — genera los EPUB que faltan, uno a uno, sin tocar los PDF.

Cada obra se descarga de su fuente original, así que el lote:
  - salta las que ya tienen EPUB (se puede parar y reanudar sin perder nada)
  - espacia las peticiones para no castigar a textos.info ni a Wikisource
  - registra lo hecho y lo fallido en lote_epub.log
  - sigue adelante cuando una falla, en vez de abortar el lote entero

Uso:
    python3 lote_epub.py                 # informe: qué haría
    python3 lote_epub.py --aplicar
    python3 lote_epub.py --aplicar --limite 10     # tanda corta de prueba
    python3 lote_epub.py --aplicar --pausa 8       # más margen entre descargas
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime

REGISTRO = "lote_epub.log"


def slug_de(ruta_cfg):
    try:
        with open(ruta_cfg, encoding="utf-8") as f:
            return json.load(f).get("slug")
    except Exception:
        return None


def epubs_de(slug):
    """Rutas posibles: la obra completa o, si no, cualquiera por partes."""
    unico = f"epub/{slug}-tinta-y-datos.epub"
    return [unico] if os.path.exists(unico) else glob.glob(
        f"epub/{slug}-parte-*-tinta-y-datos.epub")


def anotar(linea):
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')}\t{linea}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--limite", type=int, default=0,
                    help="procesar como mucho N obras en esta pasada")
    ap.add_argument("--pausa", type=float, default=5.0,
                    help="segundos de espera entre descargas (por defecto 5)")
    ap.add_argument("--obras", default="obras")
    a = ap.parse_args()

    os.makedirs("epub", exist_ok=True)
    todas = sorted(glob.glob(os.path.join(a.obras, "*.json")))
    pendientes, sin_slug, ya = [], [], 0

    for ruta in todas:
        slug = slug_de(ruta)
        if not slug:
            sin_slug.append(ruta)
        elif epubs_de(slug):
            ya += 1
        else:
            pendientes.append((ruta, slug))

    print(f"Obras en {a.obras}/ : {len(todas)}")
    print(f"  con EPUB ya hecho: {ya}")
    print(f"  pendientes       : {len(pendientes)}")
    if sin_slug:
        print(f"  sin slug en el JSON: {len(sin_slug)} -> {', '.join(sin_slug[:3])}")

    if a.limite:
        pendientes = pendientes[:a.limite]
        print(f"  esta pasada      : {len(pendientes)} (límite {a.limite})")

    if not a.aplicar:
        for ruta, _ in pendientes[:8]:
            print(f"    {ruta}")
        if len(pendientes) > 8:
            print(f"    ... y {len(pendientes)-8} más")
        tiempo = len(pendientes) * (a.pausa + 6) / 60
        print(f"\nTiempo aproximado: {tiempo:.0f} min con pausa de {a.pausa}s.")
        print("Simulación. Añade --aplicar para ejecutarlo.")
        return

    anotar(f"INICIO\t{len(pendientes)} pendientes\tpausa={a.pausa}s")
    bien, mal = 0, []

    for i, (ruta, slug) in enumerate(pendientes, 1):
        print(f"[{i}/{len(pendientes)}] {os.path.basename(ruta)}", flush=True)
        try:
            r = subprocess.run(
                [sys.executable, "tinta.py", ruta, "--solo-epub"],
                capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            mal.append((ruta, "tiempo agotado"))
            anotar(f"FALLA\t{ruta}\ttiempo agotado")
            continue

        if r.returncode == 0 and epubs_de(slug):
            bien += 1
            anotar(f"OK\t{ruta}")
        else:
            motivo = (r.stderr or r.stdout or "sin salida").strip().splitlines()
            motivo = motivo[-1][:160] if motivo else "sin salida"
            mal.append((ruta, motivo))
            anotar(f"FALLA\t{ruta}\t{motivo}")
            print(f"    FALLA: {motivo}", flush=True)

        if i < len(pendientes):
            time.sleep(a.pausa)

    print(f"\nGenerados: {bien}    Fallidos: {len(mal)}")
    anotar(f"FIN\tok={bien}\tfallos={len(mal)}")
    if mal:
        print("\nFallaron (quedan pendientes, relanza el lote para reintentarlas):")
        for ruta, motivo in mal[:15]:
            print(f"  {os.path.basename(ruta):36} {motivo}")
        if len(mal) > 15:
            print(f"  ... y {len(mal)-15} más. Detalle completo en {REGISTRO}")


if __name__ == "__main__":
    main()

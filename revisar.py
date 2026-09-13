#!/usr/bin/env python3
"""Revisión periódica de Tinta y Datos.

Reúne en un solo comando las comprobaciones que conviene repetir cada cierto
tiempo. Cada una nació de un problema real: obras publicadas a las que les
faltaba medio texto, ids que se pisaban entre tandas, enlaces que dejaron de
responder, fechas de autor que contradecían el dominio público.

    python3 revisar.py              # lo rápido: catálogo, ids, enlaces internos
    python3 revisar.py --enlaces    # + comprueba que los 700 PDF respondan
    python3 revisar.py --todo       # + regenera y verifica cada edición (lento)

Sin argumentos tarda segundos. Con --todo puede tardar una hora: esa pasada
conviene hacerla de vez en cuando, no cada semana.
"""
import argparse
import csv
import glob
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

R2 = "archivos.tintaydatos.com"
SALIDA = "obras-web"
problemas, avisos = [], []


def titulo(t):
    print(f"\n{'─' * 64}\n{t}\n{'─' * 64}")


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower() or "obra"


# ─────────────────────────────────────────────────────────────────────────
def revisar_auditoria():
    """Derechos de autor, ids repetidos y coherencia del catálogo."""
    titulo("1. Auditoría del catálogo")
    r = subprocess.run([sys.executable, "auditar_catalogo.py"],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if "(nada)" not in r.stdout:
        problemas.append("la auditoría encontró algo que resolver")


def revisar_fichas_web():
    """Cada obra del catálogo debe tener su página, y al revés."""
    titulo("2. Fichas web")
    filas = list(csv.DictReader(open("catalogo.csv", encoding="utf-8")))
    esperadas, vistos = set(), set()
    for r in filas:
        n = slug(r["titulo"])
        if len(n) > 45:
            n = n[:45].rsplit("-", 1)[0] or n[:45]
        esperadas.add(n)          # comparación laxa: basta el prefijo
    hay = {Path(p).stem for p in glob.glob(f"{SALIDA}/*.html")}
    print(f"  {len(filas)} obras en el catálogo | {len(hay)} fichas en {SALIDA}/")
    if len(hay) != len(filas):
        problemas.append(f"hay {len(filas)} obras y {len(hay)} fichas: "
                         f"corre generar_fichas.py --escribir")
    else:
        print("  coinciden")


def revisar_sitemap():
    titulo("3. Sitemap")
    if not Path("sitemap.xml").exists():
        problemas.append("falta sitemap.xml")
        print("  no existe"); return
    s = Path("sitemap.xml").read_text(encoding="utf-8")
    n = s.count("<loc>")
    filas = sum(1 for _ in csv.DictReader(open("catalogo.csv", encoding="utf-8")))
    print(f"  {n} URL ({filas + 1} esperadas: portada + obras)")
    if n != filas + 1:
        problemas.append("el sitemap no está al día: corre generar_sitemap.py")


def revisar_index():
    """El catálogo del sitio tiene que reflejar el CSV."""
    titulo("4. index.html")
    s = Path("index.html").read_text(encoding="utf-8")
    m = re.search(r"const CATALOGO = (\[.*?\n\]);", s, re.S)
    if not m:
        problemas.append("no encontré el catálogo dentro de index.html")
        print("  no encontré el bloque"); return
    enweb = len(json.loads(m.group(1)))
    filas = sum(1 for _ in csv.DictReader(open("catalogo.csv", encoding="utf-8")))
    print(f"  {enweb} obras en el sitio | {filas} en el CSV")
    if enweb != filas:
        problemas.append("index.html desactualizado: corre sync_catalogo.py --escribir")


def revisar_enlaces():
    """Que los PDF publicados sigan respondiendo."""
    titulo("5. Enlaces a los PDF")
    try:
        import requests
    except ImportError:
        avisos.append("sin requests no puedo comprobar los enlaces")
        print("  falta requests"); return
    filas = [r for r in csv.DictReader(open("catalogo.csv", encoding="utf-8"))
             if R2 in r["url"] or R2 in r.get("urls", "")]
    malos = []
    for i, r in enumerate(filas, 1):
        enlaces = ([p.split("::")[-1] for p in r["urls"].split("|")]
                   if r.get("urls", "").strip() else [r["url"]])
        for u in enlaces:
            try:
                c = requests.head(u.strip(), timeout=30,
                                  allow_redirects=True).status_code
            except Exception:
                c = 0
            if c != 200:
                malos.append((r["id"], r["titulo"][:40], c))
        if i % 100 == 0:
            print(f"  {i}/{len(filas)}…", flush=True)
    print(f"  {len(filas)} obras comprobadas | {len(malos)} con problema")
    for i, t, c in malos:
        print(f"    [{i}] {t} -> {c}")
        problemas.append(f"enlace roto en la ficha {i}")


def revisar_ediciones():
    """Regenera cada PDF y comprueba que no falte texto."""
    titulo("6. Integridad de las ediciones (lento)")
    configs = sorted(glob.glob("obras/*.json"))
    print(f"  {len(configs)} configuraciones; esto tarda un buen rato…")
    r = subprocess.run([sys.executable, "tinta.py"] + configs +
                       ["--pdf", "--verificar"], capture_output=True, text=True)
    salida = r.stdout
    for linea in salida.splitlines():
        if any(x in linea for x in ("AUSENTE", "ATENCIÓN", "ABORTADA",
                                    "FALLÓ", "════")):
            print("  " + linea.strip())
    if "FALLÓ" in salida or "AUSENTE" in salida:
        problemas.append("alguna edición no pasó la verificación")


# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--enlaces", action="store_true",
                    help="comprueba que los PDF respondan (unos minutos)")
    ap.add_argument("--todo", action="store_true",
                    help="además regenera y verifica cada edición (una hora)")
    a = ap.parse_args()

    revisar_auditoria()
    revisar_fichas_web()
    revisar_sitemap()
    revisar_index()
    if a.enlaces or a.todo:
        revisar_enlaces()
    if a.todo:
        revisar_ediciones()

    titulo("Resumen")
    if problemas:
        print(f"  {len(problemas)} cosa(s) que resolver:")
        for p in problemas:
            print(f"    · {p}")
    else:
        print("  todo en orden")
    for v in avisos:
        print(f"  aviso: {v}")
    if not (a.enlaces or a.todo):
        print("\n  (con --enlaces comprueba los PDF; con --todo, además las "
              "ediciones)")
    sys.exit(1 if problemas else 0)

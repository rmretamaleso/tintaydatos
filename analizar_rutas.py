#!/usr/bin/env python3
"""
analizar_rutas.py — mapa de dependencias antes de reordenar la carpeta.

Recorre los .py y .sh del directorio y saca qué archivos y carpetas menciona
cada uno. Sirve para saber qué se rompe si mueves algo, antes de moverlo.

Uso:
    python3 analizar_rutas.py            # informe completo
    python3 analizar_rutas.py catalogo.csv   # quién usa ese archivo
"""
import os
import re
import sys
from collections import defaultdict

# Lo que sirve Cloudflare Pages desde la raíz: mover esto rompe URLs públicas
INTOCABLE = {
    "index.html", "impressum.html", "datenschutz.html",
    "robots.txt", "sitemap.xml", "obras-web", "_redirects", "_headers",
}

PATRON = re.compile(
    r"""["']([\w./-]+\.(?:csv|json|tsv|txt|md|html|xml|pdf|py|sh|toml))["']"""
)
PATRON_DIR = re.compile(r"""["']([\w-]+)/["']""")


def main():
    filtro = sys.argv[1] if len(sys.argv) > 1 else None
    fuentes = sorted(
        f for f in os.listdir(".")
        if f.endswith((".py", ".sh")) and os.path.isfile(f)
    )

    usa = defaultdict(set)       # script -> archivos que menciona
    usado_por = defaultdict(set)  # archivo -> scripts que lo mencionan

    for f in fuentes:
        try:
            texto = open(f, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        refs = set(PATRON.findall(texto)) | {d + "/" for d in PATRON_DIR.findall(texto)}
        refs.discard(f)
        for r in refs:
            usa[f].add(r)
            usado_por[r].add(f)

    if filtro:
        print(f"Scripts que mencionan «{filtro}»:")
        encontrados = [s for r, ss in usado_por.items() if filtro in r for s in ss]
        for s in sorted(set(encontrados)):
            print(f"  {s}")
        if not encontrados:
            print("  ninguno: se puede mover sin tocar código")
        return

    print("=" * 68)
    print("QUÉ USA CADA SCRIPT")
    print("=" * 68)
    for f in fuentes:
        if usa[f]:
            print(f"\n{f}")
            for r in sorted(usa[f]):
                marca = "  [INTOCABLE]" if r.rstrip("/") in INTOCABLE else ""
                print(f"    {r}{marca}")

    print()
    print("=" * 68)
    print("ARCHIVOS COMPARTIDOS (moverlos afecta a varios scripts)")
    print("=" * 68)
    compartidos = {r: s for r, s in usado_por.items() if len(s) > 1}
    for r in sorted(compartidos, key=lambda x: -len(compartidos[x])):
        marca = "  [INTOCABLE]" if r.rstrip("/") in INTOCABLE else ""
        print(f"  {r:34} <- {', '.join(sorted(compartidos[r]))}{marca}")

    print()
    print("=" * 68)
    print("SIN REFERENCIAS: se pueden mover libremente")
    print("=" * 68)
    sueltos = [
        f for f in os.listdir(".")
        if os.path.isfile(f)
        and f not in usado_por
        and f not in INTOCABLE
        and not f.endswith((".py", ".sh"))
    ]
    for f in sorted(sueltos)[:40]:
        print(f"  {f}")
    if len(sueltos) > 40:
        print(f"  ... y {len(sueltos)-40} más")


if __name__ == "__main__":
    main()

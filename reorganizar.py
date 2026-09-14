#!/usr/bin/env python3
"""
reorganizar.py — ordena Pag_web/ por etapas, de menor a mayor riesgo.

Por defecto SIMULA: enseña cada movimiento sin tocar nada. Añade --aplicar
para ejecutarlo. Usa `git mv` cuando el archivo está versionado, para que el
historial no se pierda.

    python3 reorganizar.py 1              # simula la etapa 1
    python3 reorganizar.py 1 --aplicar
    python3 reorganizar.py 2 --aplicar

Etapas:
    1  PDF de ediciones -> pdf/        (704 archivos, sin referencias, ignorados por git)
    2  Trabajo legal    -> legal/      (documentos y CSV del análisis de dominio público)
    3  Datos auxiliares -> datos/      (.json y .tsv del pipeline de recopilación)

NO se mueven: index.html, impressum.html, datenschutz.html, robots.txt,
sitemap.xml ni obras-web/, porque Cloudflare Pages los sirve desde la raíz y
moverlos rompería las URLs públicas. Tampoco catalogo.csv ni autores.csv, que
usan 14 y 7 scripts respectivamente: el beneficio no compensa el riesgo.
"""
import os
import re
import shutil
import subprocess
import sys

ETAPAS = {
    "1": {
        "destino": "pdf",
        "descripcion": "PDF de ediciones",
        "patron": lambda f: f.endswith("-tinta-y-datos.pdf"),
    },
    "2": {
        "destino": "legal",
        "descripcion": "trabajo de dominio público",
        "patron": lambda f: f in {
            "CUMPLIMIENTO_LEGAL.md", "IMPRESSUM.md", "geobloqueo.md",
            "autores_dominio.csv", "autores_pendientes.csv", "postumas.csv",
            "calculadora_calibracion.csv", "consultas_calculadora.csv",
            "DominioPublico_1900_1945.xlsx",
        },
    },
    "3": {
        "destino": "datos",
        "descripcion": "datos auxiliares del pipeline",
        "patron": lambda f: (
            f.endswith((".json", ".tsv"))
            and f not in {"manifiesto_bloqueo.json"}
        ),
    },
}

INTOCABLES = {
    "index.html", "impressum.html", "datenschutz.html", "pie.html",
    "robots.txt", "sitemap.xml", "catalogo.csv", "autores.csv",
    ".gitignore", "README.md",
}


def versionado(ruta):
    r = subprocess.run(["git", "ls-files", "--error-unmatch", ruta],
                       capture_output=True, text=True)
    return r.returncode == 0


def referencias(nombre):
    """Scripts que mencionan este archivo por su nombre."""
    fuentes = [f for f in os.listdir(".") if f.endswith((".py", ".sh"))]
    out = []
    for f in fuentes:
        try:
            if re.search(r"['\"]%s['\"]" % re.escape(nombre), open(f, encoding="utf-8").read()):
                out.append(f)
        except (OSError, UnicodeDecodeError):
            pass
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ETAPAS:
        sys.exit(__doc__)
    etapa = ETAPAS[sys.argv[1]]
    aplicar = "--aplicar" in sys.argv
    destino = etapa["destino"]

    archivos = [
        f for f in sorted(os.listdir("."))
        if os.path.isfile(f) and f not in INTOCABLES and etapa["patron"](f)
    ]
    if not archivos:
        print(f"Etapa {sys.argv[1]}: nada que mover.")
        return

    print(f"Etapa {sys.argv[1]}: {etapa['descripcion']} -> {destino}/")
    print(f"{len(archivos)} archivos\n")

    con_refs = {f: referencias(f) for f in archivos}
    problematicos = {f: r for f, r in con_refs.items() if r}
    if problematicos:
        print("  AVISO: estos archivos se mencionan en el código y habría que")
        print("  actualizar las rutas a mano después de moverlos:")
        for f, r in problematicos.items():
            print(f"    {f}  <-  {', '.join(r)}")
        print()

    if not aplicar:
        for f in archivos[:12]:
            print(f"  {f}  ->  {destino}/{f}")
        if len(archivos) > 12:
            print(f"  ... y {len(archivos)-12} más")
        print(f"\nSimulación. Añade --aplicar para moverlos de verdad.")
        return

    os.makedirs(destino, exist_ok=True)
    movidos_git, movidos_fs, fallos = 0, 0, []
    for f in archivos:
        try:
            if versionado(f):
                subprocess.run(["git", "mv", f, os.path.join(destino, f)], check=True)
                movidos_git += 1
            else:
                shutil.move(f, os.path.join(destino, f))
                movidos_fs += 1
        except Exception as e:
            fallos.append((f, str(e)))

    print(f"Movidos: {movidos_git} con git mv, {movidos_fs} en el sistema de archivos.")
    if fallos:
        print(f"Fallos: {len(fallos)}")
        for f, e in fallos[:5]:
            print(f"  {f}: {e}")
    print(f"\nComprueba con: git status")
    if problematicos:
        print("Y corrige las rutas de los scripts listados arriba.")


if __name__ == "__main__":
    main()

"""
Publicación de una obra ya generada: subida a R2 + fila del catálogo.

El .json de la obra manda sobre lo que produjo el pipeline (url, fuente,
verificado, notas). Los campos descriptivos del catálogo —dominio, pais,
genero, tema, tipo— siguen siendo tuyos: este módulo no los toca.

La obra se enlaza con su fila mediante "catalogo_id" en el .json.
"""
import csv
import io
import subprocess
import sys
from pathlib import Path

R2_BASE = "https://archivos.tintaydatos.com/ediciones"


def credenciales_listas():
    """Faltantes de R2. Se comprueba antes de generar: descubrirlo después de
    producir veinte PDF, y con el catálogo a medio escribir, sale caro."""
    import os
    return [n for n in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                        "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
            if not os.environ.get(n)]


def subir(pdfs, script="subir_a_r2.py", prefix="ediciones/", dry_run=False):
    """Sube los PDF a R2. Devuelve True si todos salieron bien."""
    ok = True
    for pdf in pdfs:
        cmd = [sys.executable, script, pdf, "--prefix", prefix]
        if dry_run:
            cmd.append("--dry-run")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"  FALLA la subida de {pdf}", file=sys.stderr)
            ok = False
    return ok


def _fila_nueva(campos, cid):
    f = dict.fromkeys(campos, "")
    f["id"] = str(cid)
    f["puede_alojarse"] = "si"
    return f


def actualizar_catalogo(cfg, pdfs, ruta_csv="catalogo.csv", notas=None,
                        piezas=None):
    """Escribe url/urls/fuente/verificado/notas en la fila indicada por catalogo_id."""
    cid = cfg.get("catalogo_id")
    if cid is None:
        print("  Sin 'catalogo_id' en el .json: no toco el catálogo.", file=sys.stderr)
        return False

    filas = list(csv.DictReader(open(ruta_csv, encoding="utf-8")))
    campos = list(filas[0].keys())
    if "urls" not in campos:
        sys.exit(f"{ruta_csv} no tiene la columna 'urls'. Añádela antes de publicar.")

    destino = next((f for f in filas if f["id"] == str(cid)), None)
    nueva = destino is None
    if nueva:
        destino = _fila_nueva(campos, cid)
        filas.append(destino)

    enlaces = [f"{R2_BASE}/{Path(p).name}" for p in pdfs]
    if len(enlaces) == 1:
        destino["url"], destino["urls"] = enlaces[0], ""
    else:
        etiquetas = cfg.get("etiquetas_volumenes") or [
            f"Parte {i}" for i in range(1, len(enlaces) + 1)]
        destino["url"] = enlaces[0]
        destino["urls"] = "|".join(f"{e}::{u}" for e, u in zip(etiquetas, enlaces))

    fuente = cfg.get("fuente", {}).get("texto", "")
    if " — " in fuente:                      # "sitio — detalle"  ->  "sitio (detalle)"
        sitio, detalle = fuente.split(" — ", 1)
        fuente = f"{sitio} ({detalle})"
    destino["fuente"] = fuente

    # Las decisiones editoriales de cada edición viven en el colofón del PDF.
    # Aquí se llevan también a la ficha del sitio, porque son lo que distingue
    # una edición propia de un simple enlace. Si la fila ya trae una versión
    # escrita a mano, esa manda: suele ser más breve y mejor para leer en web.
    if "nota_editorial" in campos and not (destino.get("nota_editorial") or "").strip():
        destino["nota_editorial"] = cfg.get("fuente", {}).get("nota", "").strip()

    # Los títulos de las piezas contenidas, para que el buscador del sitio
    # encuentre un cuento aunque se publique dentro de su volumen.
    if "piezas" in campos:
        destino["piezas"] = " | ".join(piezas or [])

    destino["verificado"] = "True"
    if notas:
        destino["notas"] = notas
    # OJO: "catalogo" en el .json es el texto del colofón, no campos de la fila.
    # Los campos extra para el CSV van en "catalogo_campos".
    extra = cfg.get("catalogo_campos") or {}
    if not isinstance(extra, dict):
        print("  'catalogo_campos' debe ser un objeto; lo ignoro.", file=sys.stderr)
        extra = {}
    for clave, valor in extra.items():
        if clave in campos:
            destino[clave] = valor
        else:
            print(f"  'catalogo_campos' menciona una columna inexistente: {clave}",
                  file=sys.stderr)

    salida = io.StringIO()
    w = csv.DictWriter(salida, fieldnames=campos, lineterminator="\n")
    w.writeheader(); w.writerows(filas)
    Path(ruta_csv).write_text(salida.getvalue(), encoding="utf-8")

    if nueva:
        vacios = [c for c in ("dominio", "pais", "genero", "tema", "tipo")
                  if c in campos and not destino[c]]
        print(f"  Fila {cid} CREADA en {ruta_csv}.")
        if vacios:
            print(f"  Complétala a mano: {', '.join(vacios)}")
    else:
        print(f"  Fila {cid} actualizada en {ruta_csv}.")
    return True


def sincronizar(script="sync_catalogo.py"):
    if not Path(script).exists():
        print(f"  No encuentro {script}; no sincronizo index.html.", file=sys.stderr)
        return False
    return subprocess.run([sys.executable, script, "--escribir"]).returncode == 0

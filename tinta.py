#!/usr/bin/env python3
"""
Tinta y Datos — pipeline de ediciones.

    python3 tinta.py obras/fortunata.json --inspeccionar   # mira la estructura, no genera
    python3 tinta.py obras/fortunata.json --txt            # vuelca el texto a .txt
    python3 tinta.py obras/fortunata.json --pdf            # genera el/los PDF
    python3 tinta.py obras/fortunata.json --pdf --verificar

Con --html archivo.html usa una copia local en vez de descargar.
El .json de la obra manda; este script no decide nada por su cuenta.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import edicion
import publicar
import textosinfo as T
import wikisource as W


def volcar_txt(obra, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"{obra['titulo']}\n{obra['autor']}\n\n")
        for parte in obra["partes"]:
            if parte.get("nombre"):
                f.write(f"# {parte['nombre']}\n\n")
            for cap in parte["capitulos"]:
                cab = str(cap["numero"]) if cap.get("numero") is not None else ""
                if cap.get("titulo"):
                    cab += f". {cap['titulo']}"
                f.write(f"{cab}\n\n")
                for sec in cap["secciones"]:
                    if sec.get("numero") is not None:
                        f.write(f"[{sec['numero']}]\n\n")
                    for b in sec["bloques"]:
                        f.write(("\n".join(b) if isinstance(b, list) else b) + "\n\n")
    print(f"Escrito: {ruta}")


def contar(obra):
    n = 0
    for p in obra["partes"]:
        for c in p["capitulos"]:
            for s in c["secciones"]:
                for b in s["bloques"]:
                    n += len(b) if isinstance(b, list) else 1
    return n


def _clave(s):
    """Clave de comparación insensible a cómo el PDF partió las líneas.

    reportlab con partición mete guiones al cortar palabras (sobrevi-/nieron),
    y pdftotext junta ". . ." en "...". El prefijo ">> " marca acotaciones y no
    se imprime, así que tampoco debe contarse. Quitando eso, ambos lados quedan
    comparables sin perder capacidad de detectar texto ausente.
    """
    s = s[3:] if s.startswith(">> ") else s
    return re.sub(r"[\s\u00ad\u2010-]+", "", s)


def verificar(pdf, partes):
    """Comprueba que cada unidad de texto del árbol aparece en el PDF."""
    r = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"pdftotext falló sobre {pdf}: {r.stderr.strip()}")
    plano = _clave(r.stdout)

    unidades, titulos = [], []
    for p in partes:
        for c in p["capitulos"]:
            if c.get("titulo"):
                titulos.append(c["titulo"])
            for s in c["secciones"]:
                for b in s["bloques"]:
                    unidades.extend(b if isinstance(b, list) else [b])

    faltan = [u for u in unidades if _clave(u) not in plano]
    faltan_t = [t for t in titulos if _clave(t) not in plano]

    print(f"\n{pdf}")
    print(f"  unidades de texto  {len(unidades):>7}   faltan {len(faltan):>5}")
    print(f"  títulos de capítulo{len(titulos):>7}   faltan {len(faltan_t):>5}")
    for u in (faltan + faltan_t)[:10]:
        print(f"    AUSENTE «{u[:70]}»")
    if len(faltan) + len(faltan_t) > 10:
        print(f"    ... y {len(faltan) + len(faltan_t) - 10} más")
    return not (faltan or faltan_t)


def _ap():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="+", help="uno o varios .json de obra")
    ap.add_argument("--html", help="HTML local en vez de descargar")
    ap.add_argument("--inspeccionar", action="store_true")
    ap.add_argument("--txt", action="store_true")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--publicar", action="store_true",
                    help="genera, verifica, sube a R2 y actualiza el catálogo")
    ap.add_argument("--catalogo", default="catalogo.csv")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def procesar(ruta_cfg, a):
    cfg = json.loads(Path(ruta_cfg).read_text(encoding="utf-8"))
    slug = cfg.get("slug") or Path(ruta_cfg).stem
    if cfg.get("wikisource"):
        # Wikisource no se raspa: se usa su exportador oficial, que arma la obra
        # a partir de las páginas transcritas contra el facsímil.
        pagina = cfg["wikisource"]
        val = W.validado(pagina)
        print(f"Wikisource: «{pagina}»  "
              + {True: "texto validado", False: "texto NO validado",
                 None: "estado de revisión desconocido"}[val])
        if val is False:
            print("  Aviso: la transcripción no ha sido cotejada por dos personas.")
        partes, tipo = W.arbol(pagina)
        cfg.setdefault("tipo", tipo)
        totales = {"partes": 0, "capitulos": len(partes[0]["capitulos"]),
                   "secciones": len(partes[0]["capitulos"])}
        esp = cfg.get("esperados") or {}
        for k in ("partes", "capitulos"):
            if k in esp and esp[k] != totales[k]:
                raise SystemExit(f"{k}: esperaba {esp[k]}, encontré {totales[k]}. "
                                 f"Aborto para no generar una edición incompleta.")
    else:
        doc = (Path(a.html).read_text(encoding="utf-8") if a.html
               else T.descargar(cfg["url"]))
        if a.inspeccionar:
            T.inspeccionar(doc)
            return True
        partes, totales = T.parsear(doc, cfg)
    obra = {k: cfg.get(k) for k in
            ("titulo", "autor", "anio", "tipo", "catalogo", "fuente")}
    obra["partes"] = partes
    unidad = "versos" if cfg.get("tipo") == "verso" else "párrafos"
    n_unidades = contar(obra)
    print(f"{totales} | {n_unidades} {unidad}")

    # Sin esto, una obra cuyo texto se pierde entero produce un PDF con portada
    # y colofón que la verificación aprueba: cero unidades esperadas, cero
    # faltantes. Es el único control que detecta una edición vacía.
    esperado_u = (cfg.get("esperados") or {}).get("unidades")
    if esperado_u is not None and n_unidades != esperado_u:
        raise SystemExit(f"Esperaba {esperado_u} {unidad} y encontré {n_unidades}. "
                         f"Aborto para no generar una edición incompleta.")
    if n_unidades == 0:
        raise SystemExit("La obra quedó sin una sola unidad de texto. "
                         "Revisa los niveles declarados en el .json.")

    if a.txt:
        volcar_txt(obra, f"{slug}.txt")

    if not (a.pdf or a.publicar):
        return True

    op = cfg.get("opciones", {})
    if cfg.get("volumenes") == "por_parte":
        salidas = edicion.generar_por_parte(obra, f"{slug}-parte-{{n}}-tinta-y-datos.pdf", **op)
    else:
        salidas = [edicion.generar(obra, f"{slug}-tinta-y-datos.pdf", **op)]

    if a.verificar or a.publicar:
        grupos = ([[p] for p in obra["partes"]] if cfg.get("volumenes") == "por_parte"
                  else [obra["partes"]])
        if not all(verificar(pdf, trozo) for pdf, trozo in zip(salidas, grupos)):
            print("  Verificación fallida: no publico.", file=sys.stderr)
            return False

    if not a.publicar:
        return True

    if not publicar.subir(salidas, dry_run=a.dry_run):
        return False
    if a.dry_run:
        print("  [dry-run] No toco el catálogo.")
        return True

    n_cap = sum(len(pa["capitulos"]) for pa in obra["partes"])
    notas = cfg.get("catalogo_notas") or (
        f"Edición propia Tinta y Datos: {n_cap} "
        f"{'rimas' if cfg.get('tipo') == 'verso' else 'capítulos'}, "
        f"{contar(obra)} {unidad}.")
    publicar.actualizar_catalogo(cfg, salidas, a.catalogo, notas)
    return True


def main():
    a = _ap()
    resultados = {}
    for ruta in a.config:
        if len(a.config) > 1:
            print(f"\n──────── {ruta} ────────")
        try:
            resultados[ruta] = procesar(ruta, a)
        except SystemExit as e:
            print(f"  ABORTADA: {e}", file=sys.stderr)
            resultados[ruta] = False
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}", file=sys.stderr)
            resultados[ruta] = False

    if a.publicar and any(resultados.values()) and not a.dry_run:
        print("\n──────── sincronizando index.html ────────")
        publicar.sincronizar()

    if len(a.config) > 1:
        ok = [r for r, v in resultados.items() if v]
        mal = [r for r, v in resultados.items() if not v]
        print(f"\n════ {len(ok)}/{len(resultados)} correctas ════")
        for r in mal:
            print(f"  FALLÓ  {r}")
    sys.exit(0 if all(resultados.values()) else 1)


if __name__ == "__main__":
    main()

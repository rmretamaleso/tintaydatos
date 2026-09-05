#!/usr/bin/env python3
"""
Revisa el catálogo y señala inconsistencias antes de que lleguen al sitio.

Cruza catalogo.csv con autores.csv para detectar lo que no se ve leyendo una
fila aislada: obras de autores todavía protegidos, ediciones muy posteriores a
la muerte del autor (que suelen tener derechos editoriales propios), y filas
cuyo estado no concuerda con lo que realmente se publicó.

    python3 auditar_catalogo.py
    python3 auditar_catalogo.py --duros      # solo lo que hay que resolver sí o sí
"""
import argparse
import csv
import glob
import json
import datetime
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

R2 = "archivos.tintaydatos.com"
PLAZO, PLAZO_ES = 70, 80
# Una edición muchos años posterior a la muerte suele ser una recopilación
# ajena: prólogo, selección y notas tienen derechos propios.
MARGEN_POSTUMA = 20


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def libre_desde(pais, muerte):
    if not str(muerte).strip().isdigit():
        return None
    m = int(muerte)
    return m + (PLAZO_ES if pais.strip() == "España" and m < 1987 else PLAZO) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default="catalogo.csv")
    ap.add_argument("--autores", default="autores.csv")
    ap.add_argument("--duros", action="store_true")
    a = ap.parse_args()

    obras = list(csv.DictReader(open(a.catalogo, encoding="utf-8")))
    autores = {}
    if Path(a.autores).exists():
        for f in csv.DictReader(open(a.autores, encoding="utf-8")):
            autores[norm(f["nombre"])] = f
            # seudónimos y variantes con que aparece en el catálogo
            for al in (f.get("alias") or "").split("|"):
                if al.strip():
                    autores[norm(al)] = f
    hoy = datetime.date.today().year
    graves, avisos = [], []

    for r in obras:
        propia = R2 in r.get("url", "") or R2 in r.get("urls", "")
        aut = autores.get(norm(r["autor"]))
        etq = f"[{r['id']:>4}] {r['titulo'][:34]:<36}"

        # 1. autor todavía protegido
        if aut:
            libre = libre_desde(aut["pais"], aut["muerte"])
            if libre and libre > hoy:
                graves.append(f"{etq} {r['autor']} entra en dominio público en {libre}")
            # 2. edición muy posterior a la muerte del autor
            elif (libre and str(r.get("anio","")).strip().isdigit()
                  and aut["muerte"].strip().isdigit()
                  and int(r["anio"]) > int(aut["muerte"]) + MARGEN_POSTUMA):
                (graves if propia else avisos).append(
                    f"{etq} edición de {r['anio']}, {int(r['anio'])-int(aut['muerte'])} "
                    f"años tras la muerte del autor: ¿recopilación con derechos propios?")
        elif r.get("tipo", "").strip().startswith("Dominio público"):
            # Solo tiene sentido preguntar por la fecha de muerte cuando la obra
            # sigue el régimen de dominio público; una licencia CC o una
            # publicación institucional no dependen de eso.
            avisos.append(f"{etq} {r['autor'][:30]} no está en autores.csv")

        # 3. publicada pero marcada como dudosa
        if propia and r.get("puede_alojarse","").strip() != "si":
            graves.append(f"{etq} tiene edición propia pero puede_alojarse="
                          f"«{r['puede_alojarse']}»")
        # 4. publicada sin verificar
        if propia and r.get("verificado","").strip().lower() not in ("true","1","si"):
            graves.append(f"{etq} tiene edición propia pero verificado="
                          f"«{r['verificado']}»")
        # 5. dice ser edición propia y la fuente no lo refleja
        if propia and "textos.info" not in r.get("fuente","").lower():
            avisos.append(f"{etq} edición propia con fuente «{r['fuente'][:34]}»")

    # 6. duplicados
    porobra = defaultdict(list)
    for r in obras:
        porobra[(norm(r["autor"]), norm(r["titulo"]))].append(r["id"])
    for (au, ti), ids in porobra.items():
        if len(ids) > 1:
            graves.append(f"[{','.join(ids):>9}] duplicado: mismo autor y título")

    # 7. configuraciones que comparten catalogo_id
    #
    # Dos obras con el mismo id escriben la misma fila, así que una pisa a la
    # otra y desaparece del catálogo sin que nada falle. Pasó con dieciocho
    # obras y solo se notó porque el conteo no cuadraba.
    porid = defaultdict(list)
    sin_fila = []
    ids_catalogo = {r["id"] for r in obras}
    for p in sorted(glob.glob("obras/*.json")):
        try:
            c = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cid = c.get("catalogo_id")
        if cid is None:
            continue
        porid[str(cid)].append(Path(p).name)
        if str(cid) not in ids_catalogo:
            sin_fila.append((Path(p).name, cid))
    for cid, cuales in sorted(porid.items()):
        if len(cuales) > 1:
            graves.append(f"[{cid:>9}] id compartido por {', '.join(cuales)}"
                          f" — corre arreglar_ids.py")
    for nombre, cid in sin_fila:
        avisos.append(f"[{str(cid):>9}] {nombre}: configurada pero sin fila en el "
                      f"catálogo; falta publicarla")

    # 8. autores publicados que no están en el registro
    #
    # Sin ficha no hay fecha de muerte, y sin ella el plazo de dominio público
    # no se puede comprobar: la obra queda publicada sin verificar. Cada tanda
    # nueva deja autores fuera, así que conviene que salte aquí y no en una
    # revisión manual.
    for r in obras:
        propia = R2 in r.get("url", "") or R2 in r.get("urls", "")
        if not propia:
            continue
        ficha = autores.get(norm(r["autor"]))
        if not ficha:
            graves.append(f"[{r['id']:>9}] {r['autor']}: sin ficha en autores.csv, "
                          f"no se puede comprobar el plazo")
        elif not ficha.get("muerte", "").strip():
            graves.append(f"[{r['id']:>9}] {r['autor']}: sin fecha de muerte en el "
                          f"registro")

    print(f"{len(obras)} obras | {sum(1 for r in obras if R2 in r.get('url','') or R2 in r.get('urls',''))} "
          f"con edición propia | {len(autores)} autores en el registro\n")
    print(f"HAY QUE RESOLVER ({len(graves)}):\n")
    for g in sorted(set(graves)):
        print("  " + g)
    if not graves:
        print("  (nada)")
    if not a.duros:
        print(f"\nPARA MIRAR ({len(set(avisos))}):\n")
        for v in sorted(set(avisos)):
            print("  " + v)


if __name__ == "__main__":
    main()

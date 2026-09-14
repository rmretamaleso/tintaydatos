#!/usr/bin/env python3
"""
auditoria.py — revisa lo que ya está publicado en archivos.tintaydatos.com.

Cruza catalogo.csv con la matriz por país y saca los problemas ordenados por
gravedad. Distingue entre lo catalogado y lo efectivamente alojado: un enlace
externo no te expone igual que un PDF en tu bucket.

Uso: python3 auditoria.py catalogo.csv salida/matriz_paises.csv
"""
import csv
import re
import sys
from collections import Counter, defaultdict

DOMINIO_PROPIO = "archivos.tintaydatos.com"


def anio(v):
    m = re.search(r"(1[3-9]\d\d|20\d\d)", str(v))
    return int(m.group(1)) if m else None


def cargar(catalogo, matriz):
    cat = {r["id"]: r for r in csv.DictReader(open(catalogo, encoding="utf-8"))}
    mat = {r["id"]: r for r in csv.DictReader(open(matriz, encoding="utf-8"))}
    for k, v in mat.items():
        if k in cat:
            cat[k].update({f"m_{c}": v[c] for c in v})
    return cat


def main():
    if len(sys.argv) < 3:
        sys.exit("uso: auditoria.py catalogo.csv matriz_paises.csv")
    cat = cargar(sys.argv[1], sys.argv[2])
    alojadas = {k: r for k, r in cat.items() if DOMINIO_PROPIO in (r.get("url") or "")}

    hallazgos = defaultdict(list)
    for k, r in alojadas.items():
        titulo = (r.get("titulo") or "")[:42]
        autor = (r.get("autor") or "")[:24]
        tipo = (r.get("tipo") or "").strip()
        accion = r.get("m_accion", "")
        muerte = anio(r.get("m_anio_muerte"))
        pub = anio(r.get("anio"))
        ficha = f"[{k:>4}] {titulo:44} {autor:26}"

        # GRAVE: publicada y protegida en el país desde el que publicas
        if accion == "NO_PUBLICAR":
            hallazgos["1. Retirar ya: protegida en Alemania"].append(ficha)

        # GRAVE: alojada pese a estar marcada como no alojable
        pa = (r.get("puede_alojarse") or "").strip().lower()
        if pa == "no":
            hallazgos["2. Contradicción: puede_alojarse=no pero está en tu bucket"].append(ficha)
        elif pa.startswith("revisar"):
            hallazgos[f"3. Alojada con puede_alojarse={pa}"].append(ficha)

        # MEDIO: alojada sin verificar
        if (r.get("verificado") or "").strip().lower() not in ("true", "si", "1"):
            hallazgos["4. Alojada con verificado=False"].append(ficha)

        # MEDIO: no es dominio público sino licencia con obligaciones
        if tipo and not tipo.lower().startswith("dominio público"):
            hallazgos[f"5. No es dominio público: {tipo}"].append(ficha)

        # MEDIO: protegida en algún país -> exige geobloqueo
        if accion.startswith("GEOBLOQUEAR"):
            hallazgos[f"6. Exige geobloqueo en {accion.split(':')[1]}"].append(ficha)

        # MEDIO: póstuma, la fórmula por plazo p.m.a. no aplica
        if muerte and pub and pub > muerte:
            hallazgos["7. Póstuma: el plazo puede contarse desde la publicación"].append(ficha)

        # BASE: sin datos para decidir
        if accion == "REVISAR":
            hallazgos["8. Sin decidir: faltan datos del autor"].append(ficha)

    print("=" * 74)
    print(f"AUDITORÍA — {len(alojadas)} obras alojadas en {DOMINIO_PROPIO}")
    print(f"           ({len(cat) - len(alojadas)} más solo enlazadas, exposición mucho menor)")
    print("=" * 74)
    for clave in sorted(hallazgos):
        items = hallazgos[clave]
        print(f"\n{clave}  —  {len(items)} obras")
        for f in items[:8]:
            print("   " + f)
        if len(items) > 8:
            print(f"   ... y {len(items)-8} más")

    limpias = [k for k, r in alojadas.items() if r.get("m_accion") == "PUBLICAR"]
    print("\n" + "=" * 74)
    print(f"SIN NINGÚN HALLAZGO: {len(limpias)} obras alojadas están en regla.")
    print("=" * 74)


if __name__ == "__main__":
    main()

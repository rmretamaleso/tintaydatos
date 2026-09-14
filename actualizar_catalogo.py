#!/usr/bin/env python3
"""
actualizar_catalogo.py — vuelca al catálogo lo calculado por dominio_publico.py.

Escribe un archivo NUEVO (catalogo_actualizado.csv) y deja intacto el original.
Añade columnas al final, conserva el orden de las existentes y no toca ningún
valor que ya estuviera, salvo las correcciones declaradas en CORRECCIONES.

Uso:
    python3 actualizar_catalogo.py catalogo.csv salida/matriz_paises.csv autores.csv
"""
import csv
import shutil
import sys
from datetime import date

# Correcciones de datos del catálogo, con su motivo. Se aplican por id.
CORRECCIONES = {
    "696": {
        "autor": "Antonio Argerich",
        "_motivo": "«¿Inocentes o Culpables?» (1884) es de Antonio Argerich (1855-1940), "
                   "no de Juan Antonio Argerich Elizalde (1862-1924): nombres distintos "
                   "que estaban fundidos en una sola ficha",
    },
}

NUEVAS = ["autor_muerte", "autor_nacionalidad", "dominio_estado", "paises_bloqueo", "revisado_el"]


def main():
    if len(sys.argv) < 4:
        sys.exit("uso: actualizar_catalogo.py catalogo.csv matriz_paises.csv autores.csv")
    cat_path, mat_path, aut_path = sys.argv[1:4]

    with open(cat_path, encoding="utf-8") as f:
        lector = csv.DictReader(f)
        campos = list(lector.fieldnames)
        filas = list(lector)

    # Idempotencia: si las columnas ya existen (porque el script se corrió antes
    # sobre su propia salida), se reutilizan en vez de añadirse otra vez.
    duplicadas = [c for c in campos if campos.count(c) > 1]
    if duplicadas:
        sys.exit(f"{cat_path} tiene columnas repetidas: {sorted(set(duplicadas))}\n"
                 f"Límpialo antes con limpiar_duplicados.py.")
    campos_base = [c for c in campos if c not in NUEVAS]

    mat = {r["id"]: r for r in csv.DictReader(open(mat_path, encoding="utf-8"))}
    aut = {r["autor"].strip(): r for r in csv.DictReader(open(aut_path, encoding="utf-8"))}

    hoy = date.today().isoformat()
    corregidas, enriquecidas, sin_datos = [], 0, 0
    sin_ficha = set()

    for fila in filas:
        idx = fila["id"]

        autor_previo = (fila.get("autor") or "").strip()
        if idx in CORRECCIONES:
            c = CORRECCIONES[idx]
            for k, v in c.items():
                if k.startswith("_"):
                    continue
                corregidas.append((idx, k, fila.get(k), v))
                fila[k] = v

        # Tras renombrar un autor, autores.csv puede seguir con el nombre viejo:
        # se busca por el nuevo y, si no está, por el anterior.
        nombre = (fila.get("autor") or "").strip()
        a = aut.get(nombre) or aut.get(autor_previo) or {}
        if not a and nombre:
            sin_ficha.add(nombre)
        fila["autor_muerte"] = a.get("anio_muerte", "")
        fila["autor_nacionalidad"] = a.get("nacionalidad", "")

        m = mat.get(idx, {})
        accion = m.get("accion", "")
        fila["dominio_estado"] = accion.split(":")[0] if accion else ""
        fila["paises_bloqueo"] = accion.split(":")[1] if ":" in accion else ""
        fila["revisado_el"] = hoy if accion else ""
        if fila["dominio_estado"] in ("PUBLICAR", "GEOBLOQUEAR", "NO_PUBLICAR"):
            enriquecidas += 1
        else:
            sin_datos += 1

    salida = "catalogo_actualizado.csv"
    with open(salida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos_base + NUEVAS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    shutil.copy(cat_path, cat_path + ".bak")

    print(f"Escrito {salida} ({len(filas)} filas)")
    print(f"  original intacto, copia de seguridad en {cat_path}.bak")
    print(f"  columnas añadidas: {', '.join(NUEVAS)}")
    print(f"  con veredicto: {enriquecidas}   sin datos suficientes: {sin_datos}")
    if sin_ficha:
        print(f"\n  AVISO: {len(sin_ficha)} autores del catálogo no tienen fila en {aut_path}:")
        for n in sorted(sin_ficha)[:10]:
            print(f"    {n}")
        print("    Añádelos con: dominio_publico.py catalogo.csv --init-autores")
    if corregidas:
        print("\n  CORRECCIONES APLICADAS:")
        for idx, campo, antes, ahora in corregidas:
            print(f'    [{idx}] {campo}: "{antes}" -> "{ahora}"')
            print(f'          {CORRECCIONES[idx]["_motivo"]}')


if __name__ == "__main__":
    main()

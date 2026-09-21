#!/usr/bin/env python3
"""
verificar_integridad.py — comprueba que lo publicado es lo que tú generaste.

El código ya lo vigila git. Este script cubre lo que git no ve:

  1. Cambios locales sin confirmar en archivos del pipeline
  2. Commits en GitHub que no están en tu copia (el repositorio es público)
  3. Archivos de R2 que no coinciden con tu copia local
  4. URLs del catálogo que apuntan a archivos inexistentes en R2

No modifica nada. Devuelve código de salida 1 si encuentra algún problema,
así que sirve para lanzarlo desde un temporizador.

Uso:
    source ~/.config/tintaydatos/data_account.txt
    python3 verificar_integridad.py
    python3 verificar_integridad.py --sin-r2      # solo código y repositorio
"""
import argparse
import csv
import glob
import hashlib
import os
import subprocess
import sys

R2_BASE = "https://archivos.tintaydatos.com/"
CRITICOS = {
    "tinta.py", "edicion.py", "publicar.py", "wikisource.py", "textosinfo.py",
    "gutenberg.py", "generar_epub.py", "cubierta.py", "sync_catalogo.py",
    "generar_fichas.py", "catalogo.csv", "R2_upload/subir_a_r2.py",
}
problemas = []


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


# ---------------------------------------------------------------- 1
def cambios_locales():
    print("1. CÓDIGO LOCAL")
    rc, out = git("status", "--porcelain")
    if rc != 0:
        problemas.append("no estoy dentro de un repositorio git")
        print("   no estoy en un repositorio git")
        return
    lineas = [l for l in out.splitlines() if l.strip()]
    criticos = [l for l in lineas if l[3:].strip() in CRITICOS]
    otros = len(lineas) - len(criticos)
    if criticos:
        for l in criticos:
            print(f"   MODIFICADO  {l[3:]}")
        problemas.append(f"{len(criticos)} archivo(s) crítico(s) con cambios sin confirmar")
    else:
        print("   archivos críticos: sin cambios pendientes")
    if otros:
        print(f"   otros {otros} archivo(s) con cambios sin confirmar")


# ---------------------------------------------------------------- 2
def remoto():
    print("\n2. REPOSITORIO REMOTO")
    rc, _ = git("fetch", "--quiet")
    if rc != 0:
        print("   no pude consultar GitHub (sin red o sin acceso)")
        return
    rc, out = git("rev-list", "--left-right", "--count", "HEAD...@{u}")
    if rc != 0:
        print("   la rama no sigue a ninguna rama remota")
        return
    locales, ajenos = (int(x) for x in out.split())
    if ajenos:
        _, log = git("log", "--format=%h %an %ad %s", "--date=short", "HEAD..@{u}")
        print(f"   HAY {ajenos} COMMIT(S) EN GITHUB QUE NO TIENES:")
        for l in log.splitlines():
            print(f"      {l}")
        problemas.append(f"{ajenos} commit(s) remotos desconocidos: revísalos antes de hacer pull")
    else:
        print("   GitHub no tiene nada que no tengas tú")
    if locales:
        print(f"   tienes {locales} commit(s) sin subir")


# ---------------------------------------------------------------- 3 y 4
def md5(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def cliente_r2():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])


def listar_r2(c, bucket, prefijo="ediciones/"):
    """{nombre: (etag, tamaño)} de todo lo que hay bajo el prefijo."""
    objetos = {}
    for pag in c.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefijo):
        for o in pag.get("Contents", []):
            nombre = o["Key"].split("/")[-1]
            objetos[nombre] = (o["ETag"].strip('"'), o["Size"])
    return objetos


def comparar(remotos, locales):
    """remotos: {nombre: (etag, tamaño)}; locales: {nombre: ruta}.

    Para subidas simples el ETag es el MD5 del archivo. Las subidas en varias
    partes, que boto3 usa a partir de 8 MB, llevan un ETag del tipo «abc-3»
    que no es un MD5: ahí solo se puede comparar el tamaño.
    """
    distintos, solo_tamano, sin_local = [], 0, []
    for nombre, (etag, tam) in sorted(remotos.items()):
        ruta = locales.get(nombre)
        if not ruta:
            sin_local.append(nombre)
            continue
        if "-" in etag:
            solo_tamano += 1
            if os.path.getsize(ruta) != tam:
                distintos.append((nombre, "el tamaño no coincide"))
        elif md5(ruta) != etag:
            distintos.append((nombre, "el contenido no coincide"))
    sin_subir = sorted(set(locales) - set(remotos))
    return distintos, solo_tamano, sin_local, sin_subir


def bucket_y_catalogo():
    print("\n3. BUCKET DE R2 FRENTE A TU COPIA LOCAL")
    faltan = [v for v in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                          "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
              if not os.environ.get(v)]
    if faltan:
        print("   sin credenciales: haz primero source ~/.config/tintaydatos/data_account.txt")
        problemas.append("no pude revisar R2 por falta de credenciales")
        return
    c = cliente_r2()
    remotos = listar_r2(c, os.environ["R2_BUCKET_NAME"])
    locales = {os.path.basename(p): p
               for p in glob.glob("pdf/*.pdf") + glob.glob("epub/*.epub")}
    distintos, solo_tamano, sin_local, sin_subir = comparar(remotos, locales)

    print(f"   {len(remotos)} objetos en R2, {len(locales)} archivos locales")
    if distintos:
        print(f"   NO COINCIDEN ({len(distintos)}):")
        for n, motivo in distintos[:15]:
            print(f"      {n}  —  {motivo}")
        problemas.append(f"{len(distintos)} archivo(s) de R2 distintos de tu copia local")
    else:
        print("   todo lo comparable coincide con tu copia local")
    if solo_tamano:
        print(f"   {solo_tamano} se comprobaron solo por tamaño (subidas en varias partes)")
    if sin_local:
        print(f"   {len(sin_local)} en R2 sin copia local, p. ej. {', '.join(sin_local[:3])}")
    if sin_subir:
        print(f"   {len(sin_subir)} locales sin subir, p. ej. {', '.join(sin_subir[:3])}")

    print("\n4. CATÁLOGO FRENTE A R2")
    rotas = []
    for fila in csv.DictReader(open("catalogo.csv", encoding="utf-8")):
        urls = [fila.get("url") or "", fila.get("url_epub") or ""]
        urls += [p.split("::")[-1] for p in (fila.get("urls") or "").split("|") if p]
        for u in urls:
            if u.startswith(R2_BASE):
                nombre = u.rsplit("/", 1)[-1]
                if nombre not in remotos:
                    rotas.append((fila["id"], fila["titulo"][:40], nombre))
    if rotas:
        print(f"   ENLACES A ARCHIVOS INEXISTENTES ({len(rotas)}):")
        for cid, tit, n in rotas[:15]:
            print(f"      [{cid}] {tit}  ->  {n}")
        problemas.append(f"{len(rotas)} enlace(s) del catálogo apuntan a archivos que no están en R2")
    else:
        print("   todas las URLs del catálogo apuntan a archivos existentes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-r2", action="store_true")
    a = ap.parse_args()

    cambios_locales()
    remoto()
    if not a.sin_r2:
        bucket_y_catalogo()

    print("\n" + "=" * 60)
    if problemas:
        print("PROBLEMAS:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    print("Sin problemas de integridad.")


if __name__ == "__main__":
    main()

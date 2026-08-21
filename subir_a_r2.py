#!/usr/bin/env python3
"""
Sube archivos (ediciones PDF de Tinta y Datos) a un bucket de Cloudflare R2.

R2 usa una API compatible con S3, así que esto corre con boto3 apuntando
al endpoint de R2 en vez del de AWS.

CONFIGURACIÓN (variables de entorno, nunca las pongas escritas en este archivo):
  R2_ACCOUNT_ID          — el ID de cuenta de Cloudflare (Dashboard > R2 > cualquier bucket > detalles)
  R2_ACCESS_KEY_ID       — de un API Token de R2 (Dashboard > R2 > Manage API Tokens > Create API Token)
  R2_SECRET_ACCESS_KEY   — idem
  R2_BUCKET_NAME         — nombre del bucket (ej: tinta-y-datos)
  R2_PUBLIC_BASE_URL     — opcional. La URL pública del bucket, sin barra final.
                           Si tienes un dominio propio conectado al bucket: https://cdn.tintaydatos.com
                           Si usas el subdominio r2.dev que da Cloudflare: https://pub-xxxx.r2.dev
                           Si no lo seteas, el script igual sube el archivo pero no te va a
                           poder armar la URL final para pegar en el catálogo.

CÓMO CONSEGUIR LAS CREDENCIALES (una vez):
  1. Dashboard de Cloudflare > R2 Object Storage > crea el bucket si no existe.
  2. R2 > Manage API Tokens > Create API Token.
  3. Permisos: "Object Read & Write", y restringido a tu bucket si quieres ser estricta.
  4. Copia Access Key ID y Secret Access Key (el secret solo se muestra una vez).
  5. El Account ID sale en el dashboard, panel derecho de cualquier página de R2.

USO:
  # setear credenciales en la sesión de terminal (una vez por sesión)
  export R2_ACCOUNT_ID="..."
  export R2_ACCESS_KEY_ID="..."
  export R2_SECRET_ACCESS_KEY="..."
  export R2_BUCKET_NAME="tinta-y-datos"
  export R2_PUBLIC_BASE_URL="https://pub-xxxx.r2.dev"   # opcional

  # subir un archivo (queda en la raíz del bucket)
  python3 subir_a_r2.py el_matadero_tinta_y_datos.pdf

  # subir un archivo bajo una "carpeta" (prefijo) dentro del bucket
  python3 subir_a_r2.py el_matadero_tinta_y_datos.pdf --prefix ediciones/

  # subir TODOS los PDF de una carpeta local
  python3 subir_a_r2.py --carpeta ./ediciones_listas/ --prefix ediciones/

  # ver qué se subiría, sin subir nada todavía (recomendado la primera vez)
  python3 subir_a_r2.py --carpeta ./ediciones_listas/ --prefix ediciones/ --dry-run
"""
import argparse
import os
import sys
import unicodedata
from pathlib import Path

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:  # solo hace falta para subir de verdad; --dry-run funciona sin boto3
    boto3 = None

    class _FaltaBoto3(Exception):
        pass

    ClientError = NoCredentialsError = _FaltaBoto3


def slugificar(nombre: str) -> str:
    """Deja el nombre de archivo en minúsculas, sin acentos ni espacios, para
    que la URL final quede prolija. No toca la extensión."""
    stem, ext = os.path.splitext(nombre)
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    stem = stem.lower().strip()
    stem = "".join(c if c.isalnum() else "-" for c in stem)
    while "--" in stem:
        stem = stem.replace("--", "-")
    return stem.strip("-") + ext.lower()


def cliente_r2():
    if boto3 is None:
        print("Falta boto3. Instálalo con: pip install boto3", file=sys.stderr)
        sys.exit(1)
    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    faltantes = [
        nombre
        for nombre, val in [
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY_ID", access_key),
            ("R2_SECRET_ACCESS_KEY", secret_key),
        ]
        if not val
    ]
    if faltantes:
        print(f"Faltan variables de entorno: {', '.join(faltantes)}", file=sys.stderr)
        print("Revisa el bloque CONFIGURACIÓN al inicio de este script.", file=sys.stderr)
        sys.exit(1)

    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def subir_archivo(cliente, ruta_local: Path, bucket: str, prefix: str, base_url: str | None, dry_run: bool):
    nombre_final = slugificar(ruta_local.name)
    key = f"{prefix}{nombre_final}" if prefix else nombre_final

    if dry_run:
        destino = f"{base_url}/{key}" if base_url else f"s3://{bucket}/{key}"
        print(f"[dry-run] {ruta_local.name}  ->  {destino}")
        return key

    extra_args = {"ContentType": "application/pdf", "CacheControl": "public, max-age=31536000"}
    try:
        cliente.upload_file(str(ruta_local), bucket, key, ExtraArgs=extra_args)
    except NoCredentialsError:
        print("Credenciales inválidas o no encontradas.", file=sys.stderr)
        sys.exit(1)
    except ClientError as e:
        print(f"Error subiendo {ruta_local.name}: {e}", file=sys.stderr)
        return None

    if base_url:
        print(f"OK  {ruta_local.name}  ->  {base_url}/{key}")
    else:
        print(f"OK  {ruta_local.name}  ->  key: {key}  (setea R2_PUBLIC_BASE_URL para ver la URL completa)")
    return key


def main():
    ap = argparse.ArgumentParser(description="Sube archivos a un bucket de Cloudflare R2.")
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("archivo", nargs="?", help="Ruta a un único archivo a subir")
    grupo.add_argument("--carpeta", help="Sube todos los .pdf de esta carpeta")
    ap.add_argument("--prefix", default="", help="Prefijo/carpeta dentro del bucket, ej: ediciones/")
    ap.add_argument("--dry-run", action="store_true", help="Muestra qué se subiría, sin subir nada")
    args = ap.parse_args()

    if args.prefix and not args.prefix.endswith("/"):
        args.prefix += "/"

    bucket = os.environ.get("R2_BUCKET_NAME")
    if not bucket:
        if args.dry_run:
            bucket = "(R2_BUCKET_NAME sin definir)"
        else:
            print("Falta la variable de entorno R2_BUCKET_NAME.", file=sys.stderr)
            sys.exit(1)
    base_url = os.environ.get("R2_PUBLIC_BASE_URL", "").rstrip("/") or None

    cliente = None if args.dry_run else cliente_r2()

    if args.carpeta:
        carpeta = Path(args.carpeta)
        archivos = sorted(carpeta.glob("*.pdf"))
        if not archivos:
            print(f"No encontré archivos .pdf en {carpeta}", file=sys.stderr)
            sys.exit(1)
        print(f"Subiendo {len(archivos)} archivo(s) de {carpeta}...\n")
        resultados = {}
        for ruta in archivos:
            key = subir_archivo(cliente, ruta, bucket, args.prefix, base_url, args.dry_run)
            if key:
                resultados[ruta.name] = f"{base_url}/{key}" if base_url else key
        print(f"\nListo: {len(resultados)}/{len(archivos)} subidos correctamente.")
    else:
        ruta = Path(args.archivo)
        if not ruta.exists():
            print(f"No existe el archivo: {ruta}", file=sys.stderr)
            sys.exit(1)
        subir_archivo(cliente, ruta, bucket, args.prefix, base_url, args.dry_run)


if __name__ == "__main__":
    main()

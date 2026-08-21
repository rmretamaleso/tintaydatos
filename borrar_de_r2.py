#!/usr/bin/env python3
"""
Borra objetos de un bucket de Cloudflare R2.

Pensado para deshacer una subida accidental: conserva solo lo que calza con el
patrón de las ediciones propias y borra el resto bajo el prefijo indicado.

USO:
  # ver qué se borraría (NO borra nada)
  python3 borrar_de_r2.py --prefix ediciones/ --dry-run

  # borrar de verdad (pide confirmación escrita)
  python3 borrar_de_r2.py --prefix ediciones/

  # conservar otro patrón
  python3 borrar_de_r2.py --prefix ediciones/ --conservar "*-tinta-y-datos.pdf" --dry-run

  # borrar una lista concreta, sin patrones
  python3 borrar_de_r2.py --claves ediciones/uno.pdf ediciones/dos.pdf

Usa las mismas variables de entorno que subir_a_r2.py.
"""
import argparse
import fnmatch
import os
import sys

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception


def cliente_r2():
    if boto3 is None:
        sys.exit("Falta boto3. Instálalo con: pip install boto3 --break-system-packages")
    faltan = [n for n in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
              if not os.environ.get(n)]
    if faltan:
        sys.exit(f"Faltan variables de entorno: {', '.join(faltan)}")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"), region_name="auto")


def listar(cli, bucket, prefix):
    claves, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kw["ContinuationToken"] = token
        r = cli.list_objects_v2(**kw)
        claves += [o["Key"] for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            return sorted(claves)
        token = r.get("NextContinuationToken")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="", help="prefijo a revisar, ej: ediciones/")
    ap.add_argument("--conservar", default="*-tinta-y-datos.pdf",
                    help="patrón de lo que NO se borra (por defecto, las ediciones propias)")
    ap.add_argument("--claves", nargs="*", help="borrar exactamente estas claves")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    bucket = os.environ.get("R2_BUCKET_NAME")
    if not bucket:
        sys.exit("Falta la variable de entorno R2_BUCKET_NAME.")
    cli = cliente_r2()

    if a.claves:
        borrar, conservar = list(a.claves), []
    else:
        todas = listar(cli, bucket, a.prefix)
        if not todas:
            sys.exit(f"No hay objetos bajo «{a.prefix}» en {bucket}.")
        conservar = [k for k in todas if fnmatch.fnmatch(os.path.basename(k), a.conservar)]
        borrar = [k for k in todas if k not in conservar]

    print(f"CONSERVAR ({len(conservar)}):")
    for k in conservar:
        print(f"  = {k}")
    print(f"\nBORRAR ({len(borrar)}):")
    for k in borrar:
        print(f"  x {k}")

    if not borrar:
        print("\nNada que borrar.")
        return
    if a.dry_run:
        print("\n[dry-run] No se borró nada.")
        return

    print(f"\nSe van a borrar {len(borrar)} objetos de «{bucket}». Esto no se deshace.")
    if input("Escribe BORRAR para confirmar: ").strip() != "BORRAR":
        sys.exit("Cancelado.")

    hechos = 0
    for i in range(0, len(borrar), 1000):
        lote = [{"Key": k} for k in borrar[i:i + 1000]]
        try:
            r = cli.delete_objects(Bucket=bucket, Delete={"Objects": lote})
        except ClientError as e:
            print(f"Error borrando el lote {i//1000 + 1}: {e}", file=sys.stderr)
            continue
        hechos += len(r.get("Deleted", []))
        for err in r.get("Errors", []):
            print(f"  FALLA {err.get('Key')}: {err.get('Message')}", file=sys.stderr)
    print(f"\nBorrados {hechos}/{len(borrar)}.")


if __name__ == "__main__":
    main()

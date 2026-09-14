#!/usr/bin/env bash
# desplegar.sh — despliega el Worker de geobloqueo, probándolo antes.
#
#   ./desplegar.sh prueba       regenera el manifiesto, despliega en workers.dev
#                               y ejecuta las comprobaciones. NO toca producción.
#   ./desplegar.sh produccion   añade la ruta archivos.tintaydatos.com/*
#   ./desplegar.sh revertir     quita la ruta y devuelve el tráfico a R2
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$AQUI")"
CATALOGO="${CATALOGO:-$RAIZ/catalogo.csv}"
MATRIZ="${MATRIZ:-$RAIZ/salida/matriz_paises.csv}"
NOMBRE_PRUEBA="tintaydatos-geobloqueo-prueba"
NOMBRE_PROD="tintaydatos-geobloqueo"

cd "$AQUI"

comprobar_requisitos() {
  command -v npx >/dev/null || { echo "Falta Node/npx."; exit 1; }
  [[ -f "$CATALOGO" ]] || { echo "No encuentro $CATALOGO"; exit 1; }
  [[ -f "$MATRIZ" ]]   || { echo "No encuentro $MATRIZ (corre dominio_publico.py primero)"; exit 1; }
  if grep -q "CAMBIAR-POR-EL-NOMBRE-REAL" wrangler.toml; then
    echo "Edita wrangler.toml y pon el nombre real del bucket de R2."
    echo "Lo ves en el panel: R2 > Overview."
    exit 1
  fi
}

regenerar() {
  echo "==> Regenerando el manifiesto desde el catálogo"
  # generar_manifiesto.py escribe en el directorio actual, que ya es worker/.
  # NO copiar aquí ninguna otra versión: sobrescribiría la recién generada.
  python3 "$RAIZ/generar_manifiesto.py" "$CATALOGO" "$MATRIZ"
  [[ -f manifiesto_bloqueo.json ]] || { echo "No se generó el manifiesto."; exit 1; }
  # Aviso si quedó una copia antigua en la raíz que pueda confundir
  if [[ -f "$RAIZ/manifiesto_bloqueo.json" ]]; then
    echo "    Aviso: hay un manifiesto suelto en $RAIZ que no se usa. Bórralo para evitar líos."
  fi
  python3 -c "
import json,sys
d=json.load(open('manifiesto_bloqueo.json'))['bloqueos']
k=next(iter(d)); v=d[k]
print('    formato:', 'nuevo (con títulos)' if isinstance(v,dict) else 'ANTIGUO (sin títulos)')
"
}

# Genera un wrangler temporal sin rutas, para desplegar en workers.dev
config_prueba() {
  # workers_dev va justo tras compatibility_date: si se añade al final del
  # archivo cae dentro de [[r2_buckets]] y wrangler avisa de campo inesperado.
  sed -e "s/^name = .*/name = \"$NOMBRE_PRUEBA\"/" \
      -e "/^routes = \[/,/^\]/d" \
      -e "/^compatibility_date/a workers_dev = true\npreview_urls = false" \
      wrangler.toml > wrangler.prueba.toml
}

pruebas() {
  local base="$1" token="$2"
  local fallos=0
  echo
  echo "==> Comprobaciones contra $base"

  # Toma casos reales del manifiesto: uno bloqueado en MX, uno bloqueado en US
  local ruta_mx ruta_us ruta_libre
  # El manifiesto puede venir en formato antiguo (lista de países) o nuevo
  # (objeto con países, título y autor). Se soportan los dos.
  ruta_mx="$(python3 -c "
import json,sys
d=json.load(open('manifiesto_bloqueo.json'))['bloqueos']
def paises(v): return v if isinstance(v,list) else v['p']
try: print(next(k for k,v in d.items() if paises(v)==['MX']))
except StopIteration: sys.exit('sin obra bloqueada solo en MX')")"
  ruta_us="$(python3 -c "
import json,sys
d=json.load(open('manifiesto_bloqueo.json'))['bloqueos']
def paises(v): return v if isinstance(v,list) else v['p']
try: print(next(k for k,v in d.items() if 'US' in paises(v) and 'MX' not in paises(v)))
except StopIteration: sys.exit('sin obra bloqueada en US y no en MX')")"
  [[ -n "$ruta_mx" && -n "$ruta_us" ]] || { echo "  No pude elegir casos de prueba del manifiesto."; return 1; }
  ruta_libre="$(python3 -c "
import csv,json
from urllib.parse import urlparse
bl=set(json.load(open('manifiesto_bloqueo.json'))['bloqueos'])
for r in csv.DictReader(open('$CATALOGO',encoding='utf-8')):
    u=r.get('url') or ''
    if 'archivos.tintaydatos.com' in u:
        p=urlparse(u).path.lstrip('/')
        if p not in bl: print(p); break")"

  probar() {  # probar DESCRIPCION ESPERADO RUTA [PAIS]
    local desc="$1" esperado="$2" ruta="$3" pais="${4:-}"
    local args=(-s -o /dev/null -w '%{http_code}' --max-time 20)
    [[ -n "$pais" ]] && args+=(-H "x-pais-prueba-token: $token" -H "x-pais-prueba: $pais")
    local code; code="$(curl "${args[@]}" "$base/$ruta")"
    if [[ "$code" == "$esperado" ]]; then
      printf '  OK    %-3s  %s\n' "$code" "$desc"
    else
      printf '  FALLO %-3s  %s (esperaba %s)\n' "$code" "$desc" "$esperado"
      fallos=$((fallos+1))
    fi
  }

  probar "obra libre, sin forzar país"        200 "$ruta_libre"
  probar "obra restringida, desde Chile"      200 "$ruta_mx" CL
  probar "obra restringida, desde México"     451 "$ruta_mx" MX
  probar "obra restringida en EE. UU."        451 "$ruta_us" US
  probar "la de EE. UU., ahora desde España"  200 "$ruta_us" ES
  probar "archivo inexistente"                404 "ediciones/no-existe-xyz.pdf"

  # El 451 debe mostrar el título real del catálogo, no el slug
  local titulo_esperado cuerpo
  titulo_esperado="$(python3 -c "
import json
d=json.load(open('manifiesto_bloqueo.json'))['bloqueos']['$ruta_mx']
print(d['t'] if isinstance(d, dict) else '')")"
  if [[ -n "$titulo_esperado" ]]; then
    cuerpo="$(curl -s --max-time 20 \
      -H "x-pais-prueba-token: $token" -H "x-pais-prueba: MX" "$base/$ruta_mx")"
    if grep -qF "$titulo_esperado" <<<"$cuerpo"; then
      printf '  OK    ---  el 451 muestra el título real: %s\n' "$titulo_esperado"
    else
      printf '  FALLO ---  el 451 NO muestra "%s" (¿geobloqueo.js sin actualizar?)\n' "$titulo_esperado"
      fallos=$((fallos+1))
    fi
  fi

  echo
  if [[ $fallos -eq 0 ]]; then
    echo "  Las 6 comprobaciones pasan."
  else
    echo "  $fallos comprobación(es) fallida(s). NO promuevas a producción."
    return 1
  fi
}

case "${1:-}" in
  prueba)
    comprobar_requisitos
    regenerar
    config_prueba
    echo "==> Configurando el secreto de pruebas"
    TOKEN="$(od -An -tx1 -N16 /dev/urandom | tr -d ' \n')"
    echo "$TOKEN" | npx wrangler secret put PAIS_PRUEBA_TOKEN --config wrangler.prueba.toml
    echo "    Token de pruebas (para comprobar a mano): $TOKEN"
    echo "==> Desplegando en workers.dev (producción intacta)"
    SALIDA="$(npx wrangler deploy --config wrangler.prueba.toml 2>&1 | tee /dev/stderr)"
    URL="$(grep -oE 'https://[a-z0-9.-]+\.workers\.dev' <<<"$SALIDA" | head -1)"
    [[ -n "$URL" ]] || { echo "No pude leer la URL de workers.dev del despliegue."; exit 1; }
    sleep 3
    pruebas "$URL" "$TOKEN"
    echo
    echo "Si todo está bien:  ./desplegar.sh produccion"
    ;;

  produccion)
    comprobar_requisitos
    regenerar
    echo
    echo "Esto pone el Worker delante de las 699 ediciones."
    read -rp "¿Ya corriste './desplegar.sh prueba' y pasaron las comprobaciones? (escribe SI) " ok
    [[ "$ok" == "SI" ]] || { echo "Cancelado."; exit 1; }
    npx wrangler deploy
    echo
    echo "Desplegado. Comprueba a mano un par de URLs reales desde tu navegador."
    echo "Si algo va mal: ./desplegar.sh revertir"
    ;;

  revertir)
    echo "Quitando la ruta para que el tráfico vuelva directo a R2..."
    npx wrangler delete --name "$NOMBRE_PROD" || true
    echo "Hecho. Comprueba que las ediciones se descargan otra vez."
    ;;

  *)
    echo "uso: ./desplegar.sh {prueba|produccion|revertir}" >&2
    exit 2
    ;;
esac

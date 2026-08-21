# Tinta y Datos

Catálogo de literatura y ciencia en español, de acceso libre.

Las ediciones son propias: se tipografían de nuevo a partir de textos verificados
como de dominio público. No son copias de archivos de terceros.

## Estructura

- `index.html` — el sitio completo (HTML/CSS/JS en un archivo, sin build)
- `catalogo.csv` — **la fuente de verdad del catálogo**
- `obras/*.json` — una configuración por obra para el generador de PDF
- `correcciones.tsv`, `cortes.tsv` — aparato crítico de las ediciones enmendadas

## Cómo actualizar el catálogo

`catalogo.csv` manda. Se edita ahí y se sincroniza el sitio:

```bash
python3 sync_catalogo.py            # avisa si index.html quedó atrás (sale con 1)
python3 sync_catalogo.py --escribir # lo actualiza
```

Nunca editar `const CATALOGO = [...]` de `index.html` a mano: lo sobrescribe el
sincronizador.

Una obra puede tener varios archivos (novelas repartidas en volúmenes). Van en la
columna `urls` con el formato `Parte 1::https://…|Parte 2::https://…`. Si está
vacía se usa `url`.

## Cómo producir una edición

Cada obra se describe en un `.json` bajo `obras/`. El flujo completo:

```bash
python3 tinta.py obras/lillo-subsole.json --inspeccionar   # ver la estructura de la fuente
python3 tinta.py obras/lillo-subsole.json --publicar --dry-run
python3 tinta.py obras/lillo-subsole.json --publicar
```

`--publicar` genera el PDF, verifica que no falte texto, lo sube a R2, escribe la
fila del catálogo y sincroniza `index.html`. Si la verificación falla, no publica.

Varias obras a la vez, aislando los fallos:

```bash
python3 tinta.py obras/*.json --publicar
```

### Módulos

- `textosinfo.py` — descarga y parsea la versión `/ebook` de textos.info
- `edicion.py` — compone el PDF (prosa y verso) desde un árbol
- `publicar.py` — subida a R2 y escritura de la fila del catálogo
- `tinta.py` — orquesta todo lo anterior

**Siempre usar `/ebook`, nunca el PDF de la fuente.** El PDF pierde los saltos de
estrofa en verso y los límites de párrafo en prosa.

### Antes de dar una edición por buena

`--inspeccionar` no genera nada y reporta la estructura encontrada. Hay que
mirarla: si aparecen encabezados o párrafos que el `.json` no declara, el parser
avisa, porque ese material se perdería sin que la verificación lo note.

La verificación comprueba que no **falte** texto, no que **sobre**.

## Almacenamiento

Los PDF viven en Cloudflare R2, bucket `tinta-y-datos`, dominio
`archivos.tintaydatos.com`. Las credenciales van por variables de entorno; ver la
cabecera de `subir_a_r2.py`. Nunca se versionan.

`borrar_de_r2.py` limpia el bucket conservando solo `*-tinta-y-datos.pdf`.

## Deploy

1. Empujar a GitHub.
2. Cloudflare Pages, ya conectado al repo, publica solo.
3. Dominio: tintaydatos.com

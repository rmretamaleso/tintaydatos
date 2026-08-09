# Tinta y Datos

Catálogo de literatura y ciencia en español, de acceso libre.

## Estructura
- `index.html` — el sitio completo (HTML/CSS/JS en un solo archivo, sin dependencias de build)
- `catalogo.csv` — el mismo catálogo en formato descargable

## Cómo actualizar el catálogo
Los datos viven directamente en `index.html`, dentro de `const CATALOGO = [...]` (buscar ese texto en el archivo). Para agregar una obra, se suma un objeto nuevo a ese arreglo siguiendo el mismo formato que los existentes.

## Deploy
1. Subir este contenido a un repositorio de GitHub (reemplazando los archivos existentes).
2. Cloudflare Pages/Workers ya conectado a ese repo lo publica solo.
3. Dominio: tintaydatos.com

# Tinta y Datos

Catálogo de literatura y ciencia en español, de acceso libre.

## Estructura
- `index.html` — el sitio completo (HTML/CSS/JS en un solo archivo, sin dependencias de build)
- `catalogo.csv` — el mismo catálogo en formato descargable

## Cómo actualizar el catálogo
Los datos viven directamente en `index.html`, dentro de `const CATALOGO = [...]` (buscar ese texto en el archivo). Para agregar una obra, se suma un objeto nuevo a ese arreglo siguiendo el mismo formato que los existentes.

## Deploy
Ver guía de despliegue en la conversación con Claude — resumen:
1. Subir este contenido a un repositorio de GitHub.
2. Conectar el repo a Cloudflare Pages (sin build command, "Deploy" apunta a la raíz).
3. Configurar el dominio `tintaydatos.cl` en la pestaña "Custom domains" del proyecto en Cloudflare Pages.

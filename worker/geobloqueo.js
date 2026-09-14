/**
 * Worker de geobloqueo para archivos.tintaydatos.com
 *
 * Se coloca delante del bucket de R2 y decide, por país de origen de la
 * petición, si sirve el PDF o devuelve un 451. Sirve los objetos desde el
 * binding de R2, no con fetch(), para no provocar un bucle con el dominio
 * personalizado del bucket.
 *
 * Base legal: TJUE C-788/24 (9/7/2026). Publicar una obra de dominio público
 * es lícito aunque siga protegida en otro país, siempre que un geobloqueo
 * actualizado impida el acceso desde allí.
 */

import manifiesto from "./manifiesto_bloqueo.json";

const BLOQUEOS = manifiesto.bloqueos;

const MOTIVOS = {
  MX: "México aplica un plazo de 100 años desde la muerte del autor",
  CO: "Colombia aplica un plazo de 80 años desde la muerte del autor",
  ES: "España aplica 80 años a los autores fallecidos antes del 7/12/1987",
  US: "el cálculo del dominio público en Estados Unidos depende de renovaciones de registro que aún no hemos podido verificar para esta obra",
  PR: "Puerto Rico se rige por la ley federal de Estados Unidos",
};

function escapar(t) {
  return String(t).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
}

function paginaBloqueo(pais, ruta, entrada) {
  const motivo = MOTIVOS[pais] || "la obra sigue protegida en tu país";
  // Título y autor reales del catálogo. El slug solo se usa como último recurso.
  const titulo = escapar(entrada?.t || decodeURIComponent(ruta.split("/").pop() || "")
    .replace(/-tinta-y-datos\.pdf$/, "").replace(/-/g, " "));
  const autor = entrada?.a ? escapar(entrada.a) : "";
  const firma = autor ? `, de ${autor},` : "";
  return `<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>No disponible en tu país — Tinta y Datos</title>
<style>
 body{font-family:Georgia,serif;max-width:38rem;margin:4rem auto;padding:0 1.5rem;
      line-height:1.6;color:#1a1a1a}
 h1{font-size:1.5rem;font-weight:normal;border-bottom:1px solid #ddd;padding-bottom:.6rem}
 .obra{font-style:italic}
 .nota{color:#555;font-size:.92rem;margin-top:2rem;border-top:1px solid #eee;padding-top:1rem}
 a{color:#1a1a1a}
</style></head><body>
<h1>Esta edición no está disponible en tu país</h1>
<p><span class="obra">${titulo}</span>${firma} es de dominio público en el país desde
el que publicamos, pero no en el tuyo: ${motivo}.</p>
<p>Por eso no podemos ofrecerte el archivo. La ficha bibliográfica sigue disponible en
<a href="https://tintaydatos.com/">tintaydatos.com</a>, y la edición se abrirá aquí en
cuanto la obra entre al dominio público en tu jurisdicción.</p>
<p class="nota">Código 451. Si crees que es un error, escríbenos.</p>
</body></html>`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const ruta = decodeURIComponent(url.pathname.replace(/^\/+/, ""));

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Método no permitido", { status: 405 });
    }

    // País real de la petición. Solo para pruebas se puede forzar otro, y
    // únicamente si el secreto PAIS_PRUEBA_TOKEN está configurado y coincide.
    // Sin ese secreto, la cabecera se ignora por completo.
    let pais = request.cf?.country || "XX";
    const token = env.PAIS_PRUEBA_TOKEN;
    if (token && request.headers.get("x-pais-prueba-token") === token) {
      const forzado = request.headers.get("x-pais-prueba");
      if (forzado) pais = forzado.toUpperCase();
    }
    const entrada = BLOQUEOS[ruta];
    // Compatibilidad: el manifiesto antiguo guardaba un array de países.
    const restringidos = Array.isArray(entrada) ? entrada : entrada?.p;

    if (restringidos && restringidos.includes(pais)) {
      return new Response(paginaBloqueo(pais, ruta, Array.isArray(entrada) ? null : entrada), {
        status: 451,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "no-store",
          // Cachear por país: una respuesta de MX no debe servirse a CL
          "vary": "CF-IPCountry",
          "link": '<https://tintaydatos.com/>; rel="blocked-by"',
        },
      });
    }

    const objeto = await env.ARCHIVOS.get(ruta);
    if (objeto === null) {
      return new Response("No encontrado", { status: 404 });
    }

    const cabeceras = new Headers();
    objeto.writeHttpMetadata(cabeceras);
    cabeceras.set("etag", objeto.httpEtag);
    cabeceras.set("cache-control", "public, max-age=3600");
    cabeceras.set("vary", "CF-IPCountry");

    return new Response(request.method === "HEAD" ? null : objeto.body, {
      headers: cabeceras,
    });
  },
};

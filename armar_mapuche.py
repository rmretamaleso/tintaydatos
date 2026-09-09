#!/usr/bin/env python3
"""Genera las dos obras sobre tradición y lengua mapuche de Wikisource.

Reemplazan la ficha genérica que apuntaba a una portada de Memoria Chilena sin
obra concreta detrás. Ambas están marcadas como corregidas en Wikisource.
"""
import json, pathlib
from ids import reservar

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
OBRAS = [
 ("Comentarios del Pueblo Araucano", "mq-comentarios",
  "Comentarios del Pueblo Araucano", "Manuel Manquilef", 1911, "Etnografía",
  "Manquilef fue el primer intelectual mapuche que publicó sobre su propia "
  "cultura. La obra recoge la vida y las costumbres del pueblo araucano desde "
  "dentro, no desde la mirada de un recopilador externo."),
 ("Lecturas Araucanas", "fa2-lecturasaraucanas",
  "Lecturas Araucanas", "Félix José de Augusta", 1910, "Etnografía",
  "Relatos, cantos y discursos recogidos en mapudungún por el misionero "
  "capuchino Félix José de Augusta, con su traducción al castellano. La "
  "tradición es anónima; el trabajo de recolección y transcripción es suyo."),
]
ids = reservar(len(OBRAS))
for (pagina, archivo, titulo, autor, anio, tema, nota), cid in zip(OBRAS, ids):
    c = {"slug": archivo.split("-",1)[1], "titulo": titulo, "autor": autor,
         "anio": anio, "tipo": "prosa", "wikisource": pagina, "catalogo": CAT,
         "fuente": {"nota": nota}, "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Ciencia","titulo":titulo,"autor":autor,
            "anio":str(anio),"pais":"Chile","genero":tema,"tema":tema,
            "tipo":"Dominio público","puede_alojarse":"si"},
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    pathlib.Path(f"obras/{archivo}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"  {archivo+'.json':<28} {titulo:<34} id={cid}")
print(f"\n{len(OBRAS)} configuraciones")

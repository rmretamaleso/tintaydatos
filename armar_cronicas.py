#!/usr/bin/env python3
"""Genera las crónicas coloniales americanas de Project Gutenberg.

Son textos fundacionales de la historiografía y la prosa americanas. Sus
autores son españoles, pero las obras se catalogan por el territorio del que
tratan, con el mismo criterio que el Inca Garcilaso, ya publicado como Perú.
"""
import json, pathlib

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
OBRAS = [
 (64945,"bd-conquistai","Historia Verdadera de la Conquista de la Nueva España, tomo I",
  "Bernal Díaz del Castillo","México",1632),
 (64946,"bd-conquistaii","Historia Verdadera de la Conquista de la Nueva España, tomo II",
  "Bernal Díaz del Castillo","México",1632),
 (64947,"bd-conquistaiii","Historia Verdadera de la Conquista de la Nueva España, tomo III",
  "Bernal Díaz del Castillo","México",1632),
 (25705,"jb-sumaincas","Suma y Narración de los Incas",
  "Juan de Betanzos","Perú",1551),
 (39579,"rl-descripcioni","Descripción Colonial, libro primero",
  "Reginaldo de Lizárraga","Perú",1605),
 (40724,"rl-descripcionii","Descripción Colonial, libro segundo",
  "Reginaldo de Lizárraga","Perú",1605),
]
cid = 961
for libro, archivo, titulo, autor, pais, anio in OBRAS:
    c = {"slug": archivo.split("-",1)[1], "titulo": titulo, "autor": autor,
         "anio": anio, "tipo": "prosa", "gutenberg": libro, "catalogo": CAT,
         "fuente": {}, "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":autor,
            "anio":str(anio),"pais":pais,"genero":"Memoria/Crónica",
            "tipo":"Dominio público","puede_alojarse":"si"},
         "nivel_capitulo":"h2",
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    pathlib.Path(f"obras/{archivo}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"  {archivo+'.json':<24} {titulo[:44]:<46} {pais}")
    cid += 1
print(f"\n{len(OBRAS)} configuraciones, ids 961-{cid-1}")

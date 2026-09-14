# Geobloqueo por país

Basado en la sentencia TJUE C-788/24 (9/7/2026): publicar una obra de
dominio público es lícito aunque siga protegida en otro país, si un
bloqueo geográfico actualizado impide el acceso desde allí.

## España (ES)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Alemania (DE)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## México (MX)
- Bloquear: 179 obras -> ids 10, 11, 12, 17, 22, 209, 227, 230, 231, 232, 234, 235, 236, 237, 238, 240, 241, 262, 263, 264, 271, 274, 273, 275, 276, 277, 272, 278, 280, 281, 279, 282, 297, 298, 307, 308, 311, 309, 310, 314 ...
- Sin decidir: 462 obras

## Colombia (CO)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Argentina (AR)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Chile (CL)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Perú (PE)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Ecuador (EC)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Venezuela (VE)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Uruguay (UY)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Cuba (CU)
- Bloquear: 0 obras -> ids 
- Sin decidir: 462 obras

## Estados Unidos (US)
- Bloquear: 0 obras -> ids 
- Sin decidir: 306 obras

## Expresión para Cloudflare (WAF, acción Block)

```
(ip.geoip.country eq "MX" and http.request.uri.path contains "/ediciones/<slug>")
```

Genera una regla por país usando los ids de arriba, o marca cada
edición con una cabecera de país en el worker y bloquea por ella.

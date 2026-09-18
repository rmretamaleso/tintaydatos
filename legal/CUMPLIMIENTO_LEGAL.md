
---

## 7. Cloudflare como encargado del tratamiento

El DPA de Cloudflare forma parte automáticamente del acuerdo de suscripción,
incluido el plan gratuito. No requiere aceptación separada en el panel.

- Documento: https://www.cloudflare.com/cloudflare-customer-dpa/
- Versión vigente: **6.4, en vigor desde el 3 de abril de 2026**
  (comprobado el 18/09/2026; la anterior era de 20/06/2025)
- El DPA sustituye cualquier término anterior desde la fecha en que se aceptó,
  por eso se registra la versión y no solo el enlace
- Responsable de protección de datos de Cloudflare: Emily Hancock,
  legal@cloudflare.com
- Transferencias a EE. UU.: Data Privacy Framework y, en su defecto, cláusulas
  contractuales tipo de la UE. Cloudflare está certificada en los sistemas
  Global CBPR y Global PRP
- Lista de subencargados: https://www.cloudflare.com/gdpr/subprocessors/
- Transferencias a EE. UU.: EU-US Data Privacy Framework y cláusulas
  contractuales tipo (SCC)
- Lista pública de subencargados mantenida por Cloudflare

---

## 8. Convenio de Berna: qué se aplica y qué no

Convenio de Berna para la Protección de las Obras Literarias y Artísticas
(1886), Acta de París de 1971, administrado por la OMPI. Texto español
oficial verificado. No confundir con el Convenio de Berna de 1979 sobre
conservación de la vida silvestre, que no guarda relación alguna.

Datos del convenio relevantes para este catálogo:
- Art. 7.1: el plazo mínimo del convenio es vida + 50 años. Los 70 años son
  una ampliación potestativa (art. 7.6), no una obligación. Cuba con 50 es
  plenamente conforme.
- Art. 7.5: el plazo NO corre desde la fecha de muerte, sino desde el 1 de
  enero del año siguiente. Un autor fallecido en 1956, en un país de 70 años,
  entra al dominio público el 1 de enero de 2027. Verificado en los casos
  límite de dominio_publico.py.
- Art. 7.8: el plazo es el del país donde se reclama la protección, «a menos
  que la legislación de este país no disponga otra cosa». Esa cláusula es la
  que permite a México prescindir de la comparación de plazos.
- Art. 18.2: una obra que ya pasó al dominio público en el país donde se
  reclama la protección no vuelve a protegerse allí. Principio contra la
  resurrección de derechos, en tensión con la retroactividad de la Ley
  uruguaya 19.858 (2019).

Aplicado en `dominio_publico.py`:
- Art. 5.2: la protección se rige por la ley del país donde se reclama. Es el
  fundamento de calcular una matriz obra x país.
- Art. 7.8: regla del plazo más corto para autores extranjeros, salvo entre
  miembros del EEE, donde rige el trato nacional. México no la aplica.

Revisado y sin incidencia en este catálogo:
- Art. 7.3 (obras anónimas o seudónimas, plazo desde la publicación): 27 obras
  con seudónimo, todas de identidad conocida y documentada, luego se les
  aplica el plazo normal post mortem. Obras anónimas: ninguna.
- Art. 7 bis (obras en colaboración, plazo desde la muerte del último
  superviviente): ninguna coautoría en el catálogo.
- Art. 7.4 (obras fotográficas y de artes aplicadas, mínimo 25 años): ninguna.

Si en el futuro se incorporan coautorías, obras anónimas o material
fotográfico, el script necesita ampliarse: hoy asume un autor único y plazo
contado desde su muerte.

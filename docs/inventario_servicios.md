# Inventario de servicios: instrumento inicial y ampliación

Revisión documental: 27 de octubre de 2026. Una fila no acredita conectividad, calibración ni cobertura de todas las categorías. No se contrata ni configura un servicio por aparecer aquí.

| Servicio / perfil | Función documentada | Estado |
|---|---|---|
| Cloudflare estándar / seguridad / familiar | Resolución, amenazas, contenido adulto según perfil | Tres perfiles instrumentados; solo calibración limitada |
| Google Public DNS | Referencia de resolución | Instrumentado, pendiente de calibración completa |
| Quad9 seguro / sin bloqueo | Amenazas o referencia según perfil | Dos perfiles instrumentados; no filtro parental universal |
| CleanBrowsing Family / Adult | Filtros de contenido adulto; Family incluye condiciones distintas de Adult | Candidatos documentados, no incorporados a mediciones |
| AdGuard DNS público familiar | Publicita protección frente a contenido adulto, además de otras funciones | Candidato documentado, sin calibrar |
| OpenDNS FamilyShield | Perfil FamilyShield con resolutores propios | Candidato documentado; contrastar política y señales antes de incorporarlo |
| VPN y proxies con protección por categorías | Depende del plan, cliente y configuración reales | Requieren evidencia de filtro activo, recorrido y ámbito; no inventar condiciones |

Fuentes primarias: [Cloudflare](https://developers.cloudflare.com/1.1.1.1/setup/), [Google](https://developers.google.com/speed/public-dns/docs/intro), [Quad9](https://docs.quad9.net/services/), [CleanBrowsing](https://cleanbrowsing.org/filters), [AdGuard](https://adguard-dns.io/en/public-dns.html), [OpenDNS](https://www.opendns.com/setupguide/).

Para cada incorporación registrar perfil y plan, categorías efectivamente prometidas, fuente/fecha, endpoint, referencia, huellas, restricciones y resultado de calibración. Antes de comparar armas o apuestas, obtener perfiles que declaren tratar esas categorías; la lista inicial no acredita esa cobertura. Revisar servicios gratuitos y comerciales sin asumir equivalencia entre planes ni contratar por defecto. Ampliar mediante términos de búsqueda y criterios documentados; este inventario no se presenta como exhaustivo.

## Cobertura por categoría revisada el 30-10-2026

La configuración activa solo aporta protección de contenido adulto con Cloudflare familiar. Los perfiles estándar y de amenazas sirven de referencia técnica; no cubren apuestas ni armas como filtros de contenido. Antes de evaluar esas categorías se requiere un perfil con política declarada, categoría habilitada, plan documentado, endpoint y controles calibrados. Una lista manual de dominios bloqueados no sustituye la evaluación de la categorización del proveedor.

CleanBrowsing documenta `category_adult`, `category_gambling` y `category_weapons` en su [API oficial](https://cleanbrowsing.org/api/). Su [descripción de filtros](https://cleanbrowsing.org/learn/cleanbrowsing-predefined-filters) distingue los perfiles gratuitos de las categorías configurables de pago. Se incorpora como candidato con cobertura documental, sin cuenta, contratación, perfil activo ni mediciones. No extrapolar estas categorías a los resolutores gratuitos Family/Adult. La selección operativa permanece pendiente de acceso y calibración; no se declara cerrada la brecha con una revisión documental.

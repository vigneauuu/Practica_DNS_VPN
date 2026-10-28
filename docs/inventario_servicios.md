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

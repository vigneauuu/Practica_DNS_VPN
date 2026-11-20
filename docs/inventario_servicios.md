# Inventario de servicios: instrumento inicial y ampliación

Configuración inicial revisada el 27 de octubre de 2026. La ampliación medida figura al final de este documento. Una fila no acredita conectividad, calibración ni cobertura de todas las categorías. No se contrata ni configura un servicio por aparecer aquí.

| Servicio / perfil | Función documentada | Estado al 27 de octubre |
|---|---|---|
| Cloudflare estándar / seguridad / familiar | Resolución, amenazas, contenido adulto según perfil | Tres perfiles instrumentados; solo calibración limitada |
| Google Public DNS | Referencia de resolución | Instrumentado, pendiente de calibración completa |
| Quad9 seguro / sin bloqueo | Amenazas o referencia según perfil | Dos perfiles instrumentados; no filtro parental universal |
| CleanBrowsing Family / Adult | Filtros de contenido adulto; Family incluye condiciones distintas de Adult | Candidatos documentados, no incorporados a mediciones |
| AdGuard DNS público familiar | Publicita protección frente a contenido adulto, además de otras funciones | Candidato documentado, sin calibrar |
| OpenDNS FamilyShield | Perfil FamilyShield con resolutores propios | Candidato documentado; contrastar política y señales antes de incorporarlo |
| VPN y proxies con protección por categorías | Depende del plan, cliente y configuración reales | Faltaba comprobar el filtro activo, la ruta y las aplicaciones que lo utilizaban |

Fuentes primarias: [Cloudflare](https://developers.cloudflare.com/1.1.1.1/setup/), [Google](https://developers.google.com/speed/public-dns/docs/intro), [Quad9](https://docs.quad9.net/services/), [CleanBrowsing](https://cleanbrowsing.org/filters), [AdGuard](https://adguard-dns.io/en/public-dns.html), [OpenDNS](https://www.opendns.com/setupguide/).

Para cada incorporación registrar perfil y plan, categorías efectivamente prometidas, fuente/fecha, endpoint, referencia, huellas, restricciones y resultado de calibración. Antes de comparar armas o apuestas, obtener perfiles que declaren tratar esas categorías; la lista inicial no acredita esa cobertura. Revisar servicios gratuitos y comerciales sin asumir equivalencia entre planes ni contratar por defecto. Ampliar mediante términos de búsqueda y criterios documentados; este inventario no se presenta como exhaustivo.

## Cobertura por categoría revisada el 30-10-2026

La configuración del piloto de octubre solo incorporó protección de contenido adulto con Cloudflare familiar. Los perfiles estándar y de amenazas sirven de referencia técnica; no cubren apuestas ni armas como filtros de contenido. Antes de evaluar esas categorías se requiere un perfil con política declarada, categoría habilitada, plan documentado, endpoint y controles calibrados. Una lista manual de dominios bloqueados no sustituye la evaluación de la categorización del proveedor.

CleanBrowsing documenta `category_adult`, `category_gambling` y `category_weapons` en su [API oficial](https://cleanbrowsing.org/api/). Su [descripción de filtros](https://cleanbrowsing.org/learn/cleanbrowsing-predefined-filters) distingue los perfiles gratuitos de las categorías configurables de pago. Se incorpora como candidato con cobertura documental, sin cuenta, contratación, perfil activo ni mediciones. No extrapolar estas categorías a los resolutores gratuitos Family/Adult. La selección operativa permanece pendiente de acceso y calibración; no se declara cerrada la brecha con una revisión documental.


## Perfiles medidos el 18-11-2026

La ampliación mantuvo los seis perfiles iniciales y midió ocho más por TCP/53. La tabla indica qué resolutor se utilizó como referencia para cada perfil de filtrado. El contraste específico de apuestas se hizo por DoH.

| Proveedor | Perfiles añadidos | Referencia para perfiles de filtrado |
|---|---|---|
| [AdGuard](https://adguard-dns.io/en/public-dns.html) | Sin filtro y familiar | AdGuard sin filtro |
| [CleanBrowsing](https://cleanbrowsing.org/filters) | Adulto y familiar | Cloudflare estándar, de otro proveedor |
| [Control D](https://docs.controld.com/docs/free-dns) | Sin filtro y Family Friendly | Control D sin filtro |
| [Cisco OpenDNS](https://www.opendns.com/setupguide/) | Estándar y FamilyShield | OpenDNS estándar |

En laboratorio se midieron una conexión OpenVPN y un proxy HTTP. En el servicio externo WARP de Cloudflare se midieron las respuestas DNS del túnel y el acceso HTTPS por un proxy SOCKS5. Queda pendiente comparar estos resultados con los de otro operador externo. [Mediciones de laboratorio](comparacion_2026-11-18.md) y [prueba de WARP](warp-2026-11-18.md).

El 18 de noviembre se recibieron 152 respuestas por DoH de los nombres de servicio que Mullvad documentó para sus perfiles familiar y sin filtro. Fueron 76 respuestas por perfil, mediante HTTP/2 y fuera de la VPN. El familiar incluía contenido adulto y apuestas en su política. En una segunda ejecución se recibieron otras 112 respuestas sobre seis nombres de apuestas de la nómina de Subtel, cuatro portales educativos y cuatro controles técnicos. Mullvad había anunciado la retirada de su DNS público cifrado para el 2 de noviembre. Las respuestas describen los servidores que contestaron durante esas dos mediciones; su disponibilidad para futuras repeticiones queda abierta. [Guía de Mullvad](https://mullvad.net/en/help/dns-over-https-and-dns-over-tls) · [Anuncio de retirada](https://mullvad.net/en/blog/2026/9/3/shutting-down-our-public-encrypted-dns-servers-and-sponsoring-quad9-instead) · [Segunda medición](doh-apuestas-subtel-2026-11-18.md)

## DNS4EU

El 19 de noviembre se midieron tres perfiles públicos de DNS4EU, operado por Whalebone. El perfil infantil (`child.joindns4.eu`) declara restringir apuestas y armas. Se comparó con el perfil de protección contra amenazas (`protective.joindns4.eu`) y con el perfil sin filtro de contenido (`unfiltered.joindns4.eu`). Los tres usan la ruta DoH `/dns-query`. Las órdenes judiciales aplicables al operador pueden afectar a cualquiera de ellos. [Configuración del servicio](https://joindns4.eu/for-public) · [Política de los resolutores, pp. 1–2](https://legal-documents-dns4eu.s3.fr-par.scw.cloud/DNS4EU-Public-DNS-Resolver-policy-2025.pdf)

Se recibieron 204 respuestas para 17 nombres, dos tipos de registro y dos rondas en los tres perfiles. Solo el infantil devolvió las direcciones de aviso al consultar los seis nombres de apuestas y los tres de armas. Las direcciones IPv4 e IPv6 coincidieron con las obtenidas en consultas separadas a `warning.joindns4.eu` y con las registradas en un estudio independiente de DNS4EU. Los cuatro portales educativos devolvieron direcciones A distintas de la de aviso en los tres perfiles. [Medición de DNS4EU](doh-dns4eu-2026-11-19.md) · [Szymutko, 2026, sección 4.5](https://dspace.vut.cz/server/api/core/bitstreams/453f2f87-5ecc-48f4-8225-09d7832975d2/content)

## Ampliación de rutas externas y perfiles familiares (19 y 20-11-2026)

El 19 de noviembre se evaluó la política infantil de DNS4EU sobre 88 dominios documentados y cinco controles (1.116 respuestas DoH) y se contrastaron los perfiles familiares de Cloudflare y AdGuard sobre 22 dominios de contenido adulto y 39 portales educativos (1.700 respuestas DoH). [Evaluación de DNS4EU](politica-dns4eu-2026-11-19.md) · [Perfiles familiares de Cloudflare y AdGuard](filtros-familiares-2026-11-19.md)

En transporte externo, el 19 de noviembre se añadieron RiseupVPN (OpenVPN con salida verificada en Francia, 520 respuestas DNS combinando el resolutor interno de Riseup y DNS4EU) y un proxy SOCKS5 de Tor (16 solicitudes HTTPS de control). El 20 de noviembre se midió AdGuard VPN para Linux (v1.7.12, plan gratuito, salida fija en Dallas) en un contenedor descartable, alternando sus perfiles DNS sin filtro y familiar dentro del túnel `tun0` (199 respuestas UDP de 200 consultas, contrastadas con 200 referencias DoH) y probando su modo proxy SOCKS5 (16 solicitudes HTTPS de control, donde por diseño no aplica el filtro DNS del túnel). [Riseup y Tor](riseup-tor-2026-11-19.md) · [Prueba de AdGuard VPN](adguard-vpn-2026-11-20.md)

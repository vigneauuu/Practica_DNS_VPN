# Contraste del control `example.com` con OONI

Se consultó el archivo público de OONI para comprobar si sus mediciones de conectividad podían compararse con las pruebas de la práctica. Web Connectivity evalúa una URL mediante DNS, TCP, TLS y HTTP. Compara la observación de una sonda con una red de referencia y conserva por separado el estado de acceso y las señales de interferencia. [Documentación de OONI](https://ooni.org/support/interpreting-ooni-data/) · [Especificación de Web Connectivity](https://github.com/ooni/spec/blob/master/nettests/ts-017-web-connectivity.md)

Primero se consultó el índice de Web Connectivity para Chile, entre el 20 de octubre y el 20 de noviembre de 2026, en UTC, con filtros separados para `example.com` y los cuatro dominios educativos de la [medición con DNS4EU](doh-dns4eu-2026-11-19.md). Las cinco consultas devolvieron cero filas. Después se buscó sin filtro de país la URL exacta `https://example.com/` en los días UTC 18 y 19 de noviembre, cuando se obtuvieron las mediciones propias. Se tomaron las primeras cinco filas que devolvió la API para cada día y se recuperó cada registro por su identificador. El [archivo de evidencia](evidencia/ooni-control-2026-11-19.json) conserva las consultas, los identificadores y los campos importados. [Acceso a datos de OONI](https://docs.ooni.org/data/)

| Fuente | Qué se midió en `example.com` | Resultado |
|---|---|---|
| OONI en Indonesia y Turquía | 10 mediciones de Web Connectivity de la misma URL | 10/10 con acceso, DNS consistente frente al control de OONI y campo `blocking=false`. |
| WARP, 18 de noviembre | Consultas DNS A y AAAA en conexión directa, túnel sin filtro familiar y túnel con filtro familiar. Peticiones HTTPS HEAD por conexión directa y SOCKS5h | 12/12 respuestas DNS con dirección y 8/8 peticiones HEAD con HTTP 200. |
| DNS4EU, 19 de noviembre | Consultas DoH A y AAAA con los perfiles sin filtro, protector e infantil | 12/12 respuestas DNS con dirección del tipo consultado. |

Las mediciones públicas muestran que el control fue accesible en esas otras redes. Una respuesta DNS con dirección comprueba la resolución. Para comprobar el acceso HTTP se necesita medir ese paso. Estimar la concordancia de filtrado entre OONI y los perfiles de la práctica requeriría probar las mismas URL con una red, un resolutor, una ruta y una ventana de tiempo comparables. La consulta a OONI fue de solo lectura. [WARP](warp-2026-11-18.md) · [DNS4EU](doh-dns4eu-2026-11-19.md)

Desde la raíz del repositorio, con el entorno de Python del proyecto activo, ejecutar `python scripts/consultar_ooni.py /tmp/ooni-control.json`. El índice público puede incorporar mediciones después del corte. Para cotejar la muestra original se pueden abrir los enlaces `medicion_original` del archivo de evidencia.

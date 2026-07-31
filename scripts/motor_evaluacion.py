import sqlite3
import datetime
import dns.resolver

def inicializar_bd():
    conexion = sqlite3.connect('resultados.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dominio TEXT NOT NULL,
            categoria TEXT NOT NULL,
            resolutor TEXT NOT NULL,
            estado TEXT NOT NULL,
            ip_resuelta TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conexion.commit()
    conexion.close()
    print("[+] Base de datos lista.")

def evaluar_dominio(dominio, ip_resolutor, nombre_resolutor, categoria):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [ip_resolutor]
    resolver.timeout = 3     
    resolver.lifetime = 3
    
    estado = "Error"
    ip_resuelta = "Ninguna"
    
    try:
        respuesta = resolver.resolve(dominio, 'A')
        ip_resuelta = respuesta[0].to_text()
        estado = "Permitido"
    
    except dns.resolver.NXDOMAIN:
        estado = "Bloqueado (NXDOMAIN)"
    except Exception as e:
        estado = "Error/Timeout"
        
    conexion = sqlite3.connect('resultados.db')
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO evaluaciones (dominio, categoria, resolutor, estado, ip_resuelta)
        VALUES (?, ?, ?, ?, ?)
    ''', (dominio, categoria, nombre_resolutor, estado, ip_resuelta))
    conexion.commit()
    conexion.close()
    
    print(f"[{estado}] {dominio} -> {ip_resuelta}")

if __name__ == '__main__':
    print("--- Iniciando Motor de Evaluación DNS ---")
    inicializar_bd()
    
    print("\n--- Ejecutando prueba con Cloudflare (1.1.1.1) ---")
    dominios_prueba = ['google.com', 'udp.cl', 'bet365.com']
    
    for dom in dominios_prueba:
        evaluar_dominio(dom, '1.1.1.1', 'Cloudflare_Publico', 'Prueba_Inicial')
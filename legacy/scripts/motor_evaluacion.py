import sqlite3
import datetime
import dns.resolver
import os
import csv

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
    print("[+] Base de datos SQLite lista para ingesta masiva.")

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
        
        if ip_resuelta in ['0.0.0.0', '127.0.0.1']:
            estado = "Bloqueado (Sinkhole)"
        else:
            estado = "Permitido"
            
    except dns.resolver.NXDOMAIN:
        estado = "Bloqueado (NXDOMAIN)"
    except (dns.resolver.NoNameservers, dns.resolver.NoAnswer):
        estado = "Bloqueado (REFUSED/NoAnswer)"
    except Exception:
        estado = "Error/Timeout"
        
    conexion = sqlite3.connect('resultados.db')
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO evaluaciones (dominio, categoria, resolutor, estado, ip_resuelta)
        VALUES (?, ?, ?, ?, ?)
    ''', (dominio, categoria, nombre_resolutor, estado, ip_resuelta))
    conexion.commit()
    conexion.close()
    
    print(f"[{nombre_resolutor}] {categoria} | {dominio} -> {estado}")

def procesar_datasets_masivos():
    ruta_datasets = os.path.join(os.path.dirname(__file__), '..', 'dataset')
    
    resolutores = [
        {'nombre': 'HideMe_Free', 'ip': '10.34.196.1'}
    ]
    
    for archivo in os.listdir(ruta_datasets):
        if archivo.endswith("_top400.csv"):
            categoria = archivo.split('_')[0].capitalize()
            ruta_csv = os.path.join(ruta_datasets, archivo)
            
            print(f"\n==================================================")
            print(f"[*] INICIANDO CATEGORÍA: {categoria.upper()} ({archivo})")
            print(f"==================================================")
            
            with open(ruta_csv, 'r', encoding='utf-8') as f:
                lector = csv.reader(f)
                for fila in lector:
                    if not fila: continue
                    dominio = fila[0].strip()
                    
                    for res in resolutores:
                        evaluar_dominio(dominio, res['ip'], res['nombre'], categoria)

if __name__ == '__main__':
    print("--- Iniciando Motor de Evaluación Comparativa ---")
    inicializar_bd()
    procesar_datasets_masivos()
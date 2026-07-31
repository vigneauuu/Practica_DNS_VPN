import sqlite3
import datetime

def inicializar_bd():
    # Conectar a la base de datos local
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
    print("[+] Base de datos SQLite inicializada correctamente ('resultados.db')")

if __name__ == '__main__':
    print("--- Iniciando Motor de Evaluación DNS ---")
    inicializar_bd()
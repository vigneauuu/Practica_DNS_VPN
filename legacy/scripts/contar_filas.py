import sqlite3

try:
    conexion = sqlite3.connect('resultados.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM evaluaciones")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}")
    conexion.close()
except Exception as e:
    print(f"Error: {e}")
import sqlite3
import pandas as pd

def auditar_resultados():
    conexion = sqlite3.connect('resultados.db')
    
    # Total de registros
    total = pd.read_sql_query("SELECT COUNT(*) as total_filas FROM evaluaciones;", conexion)
    print("--- TOTAL DE REGISTROS ---")
    print(total)
    print("\n")
    
    # Desglose por DNS
    desglose = pd.read_sql_query("SELECT resolutor, COUNT(*) as cantidad FROM evaluaciones GROUP BY resolutor;", conexion)
    print("--- REGISTROS POR DNS ---")
    print(desglose)
    print("\n")

    # Desglose por estados (para confirmar el parche de los bloqueos)
    estados = pd.read_sql_query("SELECT estado, COUNT(*) as cantidad FROM evaluaciones GROUP BY estado;", conexion)
    print("--- RESUMEN DE ESTADOS ---")
    print(estados)
    
    conexion.close()

if __name__ == "__main__":
    auditar_resultados()
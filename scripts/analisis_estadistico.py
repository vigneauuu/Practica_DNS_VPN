import sqlite3
import pandas as pd
from sklearn.metrics import cohen_kappa_score

def ejecutar_analisis():
    conexion = sqlite3.connect('resultados.db')
    df = pd.read_sql_query("SELECT * FROM evaluaciones;", conexion)
    conexion.close()

    # Ajuste de nombre de categoría según informe
    df['categoria'] = df['categoria'].replace('Tranco', 'Benigno')

    # Codificación binaria (Sección 6.1 del informe)
    def clasificar_estado(estado):
        if "Bloqueado" in estado:
            return 1
        elif estado == "Permitido":
            return 0
        else:
            return None # Los Timeout/Errores se excluyen del Kappa

    df['bloqueo_binario'] = df['estado'].apply(clasificar_estado)

    # 1. Tabla de Tasas de Bloqueo
    print("\n==================================================")
    print("--- TASAS DE BLOQUEO POR DNS Y CATEGORÍA (%) ---")
    print("==================================================")
    df_validos = df.dropna(subset=['bloqueo_binario'])
    tasas = df_validos.groupby(['resolutor', 'categoria'])['bloqueo_binario'].mean() * 100
    print(tasas.unstack().round(2).fillna(0))

    # 2. Coeficiente Kappa de Cohen
    print("\n==================================================")
    print("--- KAPPA DE COHEN (ACUERDO INTER-JUEZ) ---")
    print("==================================================")
    # Pivotear tabla: Dominios en filas, Resolutores en columnas
    pivot = df_validos.drop_duplicates(subset=['dominio', 'resolutor']).pivot(index='dominio', columns='resolutor', values='bloqueo_binario')
    
    # Evaluar Kappa solo en dominios donde AMBOS respondieron (excluye si uno dio Timeout)
    pivot = pivot.dropna()
    
    resolutores = pivot.columns
    for i in range(len(resolutores)):
        for j in range(i+1, len(resolutores)):
            r1 = resolutores[i]
            r2 = resolutores[j]
            kappa = cohen_kappa_score(pivot[r1], pivot[r2])
            print(f"{r1} vs {r2}: {kappa:.3f}")

if __name__ == "__main__":
    ejecutar_analisis()
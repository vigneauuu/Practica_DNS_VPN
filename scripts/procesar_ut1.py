import csv

def procesar_lista(archivo_entrada, archivo_salida, limite=400):
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f_in, \
             open(archivo_salida, 'w', encoding='utf-8', newline='') as f_out:
            
            escritor = csv.writer(f_out)
            contador = 0
            
            for linea in f_in:
                dominio = linea.strip() 
                
                if dominio and contador < limite:
                    escritor.writerow([dominio])
                    contador += 1
                elif contador >= limite:
                    break
                    
        print(f"¡Éxito! Se guardaron {contador} dominios en {archivo_salida}")
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo_entrada}")

print("categoría Adultos...")
procesar_lista('../dataset/adultos_full.txt', '../dataset/adultos_top400.csv')

print("categoría Armas/Violencia...")
procesar_lista('../dataset/armas_full.txt', '../dataset/armas_top400.csv')
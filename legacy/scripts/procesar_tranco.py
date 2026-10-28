import csv

archivo_entrada = '../dataset/tranco_full.csv'
archivo_salida = '../dataset/tranco_top400.csv'


try:
    with open(archivo_entrada, 'r', encoding='utf-8') as f_in, \
         open(archivo_salida, 'w', encoding='utf-8', newline='') as f_out:
        
        lector = csv.reader(f_in)
        escritor = csv.writer(f_out)
        
        contador = 0
        for fila in lector:
            if contador < 400:
                dominio = fila[1] 
                escritor.writerow([dominio])
                contador += 1
            else:
                break
                
    print(f" Se guardaron exactamente {contador} dominios limpios en la carpeta dataset.")

except FileNotFoundError:
    print("Error: No se encontró el archivo tranco_full.csv en la carpeta dataset.")
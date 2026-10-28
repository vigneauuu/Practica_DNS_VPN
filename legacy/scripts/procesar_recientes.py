import csv
import urllib.request
import os

def generar_dataset_recientes():
    ruta_script = os.path.dirname(__file__)
    archivo_salida = os.path.join(ruta_script, '..', 'dataset', 'recientes_top400.csv')
    url_nrd = "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-domains-ACTIVE.txt"
    
    print("Descargando dominios de phishing...")
    
    try:
        respuesta = urllib.request.urlopen(url_nrd)
        lineas = respuesta.read().decode('utf-8').splitlines()
        
        dominios_limpios = []
        dominios_vistos = set()
        
        for linea in lineas:
            if linea and not linea.startswith("#"):
                dominio = linea.strip()
                
                if dominio not in dominios_vistos:
                    dominios_vistos.add(dominio)
                    dominios_limpios.append(dominio)
                    
            if len(dominios_limpios) == 400:
                break
                
        with open(archivo_salida, 'w', encoding='utf-8', newline='') as f_out:
            escritor = csv.writer(f_out)
            for dom in dominios_limpios:
                escritor.writerow([dom])
                
        print(f"Listo. Se guardaron {len(dominios_limpios)} dominios en {archivo_salida}.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    generar_dataset_recientes()
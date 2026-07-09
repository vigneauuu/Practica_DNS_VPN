import csv
import urllib.request

def generar_dataset_recientes():
    archivo_salida = '../dataset/recientes_top400.csv'
    
    # Base de datos pública de dominios maliciosos/phishing activos.
    url_nrd = "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-domains-ACTIVE.txt"
    
    print("Conectando a la fuente pública de dominios recientes/maliciosos...")
    
    try:
        respuesta = urllib.request.urlopen(url_nrd)
        lineas = respuesta.read().decode('utf-8').splitlines()
        
        dominios_limpios = []
        
        for linea in lineas:
            if linea and not linea.startswith("#"):
                dominio = linea.strip()
                dominios_limpios.append(dominio)
                
            if len(dominios_limpios) == 400:
                break
                
        # Guardar en CSV
        with open(archivo_salida, 'w', encoding='utf-8', newline='') as f_out:
            escritor = csv.writer(f_out)
            for dom in dominios_limpios:
                escritor.writerow([dom])
                
        print(f" Se guardaron 400 dominios recientemente registrados/maliciosos en {archivo_salida}")
        
    except Exception as e:
        print(f"Error de conexión: {e}")

generar_dataset_recientes()
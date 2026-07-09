import csv
import urllib.request

def generar_dataset_casinos():
    archivo_salida = '../dataset/casinos_top400.csv'
    
    casinos_chile = [
        "betano.com", "betsson.com", "coolbet.com", "rojabet.cl", 
        "juegaenlinea.com", "micasino.com", "latamwin.com", "betway.com",
        "jackpotcitycasino.com", "1xbet.com", "bet365.com", "sportingbet.com",
        "bwin.com", "888sport.com", "22bet.com", "pinnacle.com", "novibet.cl",
        "jugabet.cl", "marathonbet.com", "betwarrior.bet"
    ]
    
    dominios_finales = set(casinos_chile)
    
    #lista negra internacional en tiempo real (StevenBlack hosts)
    url_gambling = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling-only/hosts"
    
    print("Conectando a GitHub para descargar lista negra internacional...")
    try:
        respuesta = urllib.request.urlopen(url_gambling)
        lineas = respuesta.read().decode('utf-8').splitlines()
        
        for linea in lineas:
            if linea.startswith("0.0.0.0") and not "0.0.0.0 0.0.0.0" in linea:
                partes = linea.split()
                if len(partes) >= 2:
                    dominio = partes[1].strip()
                    dominios_finales.add(dominio)
                    
            if len(dominios_finales) >= 400:
                break
                
        with open(archivo_salida, 'w', encoding='utf-8', newline='') as f_out:
            escritor = csv.writer(f_out)
            for dominio in list(dominios_finales)[:400]:
                escritor.writerow([dominio])
                
        print(f"Se guardaron 400 dominios en {archivo_salida}")
        
    except Exception as e:
        print(f"Hubo un error de conexión: {e}")

generar_dataset_casinos()
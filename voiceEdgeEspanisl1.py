import asyncio
import edge_tts
import subprocess
import os
import re

# --- Configuración ---
CARPETA_SALIDA = "audios_muestra"
ARCHIVO_FINAL = "todas_las_voces_es.mp3"
FILELIST = "filelist.txt"

# --- Mapa de regiones a nombres de países/regiones ---
REGION_MAP = {
    "AR": "Argentina",
    "BO": "Bolivia",
    "CL": "Chile",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "DO": "República Dominicana",
    "EC": "Ecuador",
    "SV": "El Salvador",
    "GQ": "Guinea Ecuatorial",
    "GT": "Guatemala",
    "HN": "Honduras",
    "MX": "México",
    "NI": "Nicaragua",
    "PA": "Panamá",
    "PY": "Paraguay",
    "PE": "Perú",
    "PR": "Puerto Rico",
    "ES": "España",
    "US": "Estados Unidos",
    "UY": "Uruguay",
    "VE": "Venezuela",
}

def extract_region(voice_name):
    """Extrae el código de región de un nombre de voz como en-US-JennyNeural."""
    parts = voice_name.split('-')
    if len(parts) >= 3:
        # El formato es idioma-región-nombre, pero a veces hay más guiones (ej. en-AU-WilliamMultilingualNeural)
        # La región es la segunda parte
        return parts[1]
    return None

def get_region_name(region_code):
    """Devuelve el nombre legible de la región o None si no está en el mapa."""
    return REGION_MAP.get(region_code, region_code)  # si no está, devolvemos el código

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)
def extract_voice_name(voice_name):
    """Extrae el nombre de la voz (ej: 'Jenny', 'James', 'Neerja') desde el ShortName."""
    # Eliminar 'Neural' y sufijos como 'Expressive', 'Multilingual', etc.
    base = voice_name
    # Eliminar posibles sufijos
    base = re.sub(r'(Expressive|Multilingual|Neural)$', '', base)
    # Tomar la última parte después del último guion
    parts = base.split('-')
    if parts:
        name = parts[-1]
        # Si el nombre quedó vacío, usar el original
        if not name:
            name = voice_name
        return name
    return voice_name
async def generar_muestra(voice_name):
    """Genera un MP3 para una voz, anunciando la región."""
    region_code = extract_region(voice_name)
    voice_name_clean = extract_voice_name(voice_name)
    if region_code:
        region_name = get_region_name(region_code)
        texto = (f"Hola mi amigo, bienvenido a soacha. "
                 f"esto te llega desde  {region_name}. "
                 f"Yo soy {voice_name_clean}, milagro de verlo.")
    else:
        texto = (f"Hola mi amigo, bienvenido a soacha. "
                 f"esto te llega desde  {voice_name}. "
                 f"Yo soy {voice_name_clean}, milagro de verlo.")
    
    nombre_archivo = sanitize_filename(voice_name)
    archivo_mp3 = os.path.join(CARPETA_SALIDA, f"muestra_{nombre_archivo}.mp3")
    
    print(f"Generando {archivo_mp3} ...")
    try:
        communicate = edge_tts.Communicate(texto, voice_name)
        await communicate.save(archivo_mp3)
        print(f"✅ Generado: {archivo_mp3}")
        return archivo_mp3
    except ValueError as e:
        print(f"❌ Voz inválida {voice_name}: {e}")
        return None
    except edge_tts.exceptions.NoAudioReceived as e:
        print(f"❌ No se recibió audio para {voice_name}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado con {voice_name}: {e}")
        return None

def concatenar_audios(lista_audios, archivo_salida, filelist_path):
    if not lista_audios:
        print("No hay audios válidos para concatenar.")
        return
    with open(filelist_path, "w", encoding="utf-8") as f:
        for audio in lista_audios:
            audio_escaped = audio.replace("'", "'\\''")
            f.write(f"file '{audio_escaped}'\n")
    
    comando = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", filelist_path, "-c", "copy", archivo_salida
    ]
    print(f"\nEjecutando: {' '.join(comando)}")
    try:
        subprocess.run(comando, check=True, capture_output=True, text=True)
        print(f"✅ Concatenación exitosa. Archivo final: {archivo_salida}")
    except subprocess.CalledProcessError as e:
        print("❌ Error al concatenar:")
        print(e.stderr)

async def main():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    print("Obteniendo lista de voces...")
    voces = await edge_tts.list_voices()
    print(f"Se encontraron {len(voces)} voces en total.")
    
    # Filtrar solo las voces que empiezan con "en-"
    ##voces_en = [v for v in voces if v['ShortName'].startswith('en-')]
    voces_es = [v for v in voces if v['ShortName'].startswith('es-')]
    print(f"Voces en inglés disponibles: {len(voces_es)}\n")
    
    archivos_exitosos = []
    fallos = []
    
    for voz in voces_es:
        nombre = voz['ShortName']
        archivo = await generar_muestra(nombre)
        if archivo:
            archivos_exitosos.append(archivo)
        else:
            fallos.append(nombre)
    
    print(f"\n✅ {len(archivos_exitosos)} muestras generadas exitosamente.")
    if fallos:
        print(f"❌ {len(fallos)} voces fallaron (primeras 10): {', '.join(fallos[:10])}" + (" ..." if len(fallos) > 10 else ""))
    
    if archivos_exitosos:
        concatenar = input("¿Deseas concatenar los audios exitosos en un solo archivo? (s/n): ").lower()
        if concatenar == 's':
            concatenar_audios(archivos_exitosos, ARCHIVO_FINAL, FILELIST)
        else:
            print("Los audios individuales quedaron en la carpeta:", CARPETA_SALIDA)
    else:
        print("No se generó ningún audio. Revisa la configuración.")

if __name__ == "__main__":
    asyncio.run(main())
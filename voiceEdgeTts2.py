import asyncio
import edge_tts
import subprocess
import os
import re

# --- Configuración ---
TEXTO_BASE = "Hello my friend,welcome to new york, this is the voz "
CARPETA_SALIDA = "audios_muestra"
ARCHIVO_FINAL = "todas_las_voces.mp3"
FILELIST = "filelist.txt"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

async def generar_muestra(voice_name):
    """Genera un MP3 para una voz. Retorna la ruta si éxito, None si falla."""
    texto = f"{TEXTO_BASE} {voice_name}"
    nombre_archivo = sanitize_filename(voice_name)
    archivo_mp3 = os.path.join(CARPETA_SALIDA, f"muestra_{nombre_archivo}.mp3")
    
    print(f"Generando {archivo_mp3} ...")
    try:
        # El error ValueError puede lanzarse aquí al crear Communicate
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
    print(f"Se encontraron {len(voces)} voces.\n")
    
    archivos_exitosos = []
    fallos = []
    
    for voz in voces:
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
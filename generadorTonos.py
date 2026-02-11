import subprocess
import random
import os

def crear_tono_separador(tipo="beep", duracion=0.3, frecuencia=800, output_file=None):
    """Crea un tono de separación entre grupos"""
    
    if output_file is None:
        output_file = f'tono_{tipo}_{random.randint(1000, 9999)}.mp3'
    
    if tipo == "beep":
        # Pitido corto
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'sine=frequency={frecuencia}:duration={duracion}',
            '-af', 'volume=0.5',
            '-c:a', 'libmp3lame',
            '-q:a', '9',
            '-y',
            output_file
        ]
    elif tipo == "click":
        # Click suave
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'anoisesrc=d={duracion}:c=white',
            '-af', 'volume=0.3',
            '-c:a', 'libmp3lame',
            '-q:a', '9',
            '-y',
            output_file
        ]
    elif tipo == "silence":
        # Silencio
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-t', str(duracion),
            '-c:a', 'libmp3lame',
            '-q:a', '9',
            '-y',
            output_file
        ]
    elif tipo == "fade":
        # Fade in/out
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'sine=frequency={frecuencia}:duration={duracion}',
            '-af', f'afade=t=in:st=0:d=0.1,afade=t=out:st={duracion-0.1}:d=0.1',
            '-c:a', 'libmp3lame',
            '-q:a', '9',
            '-y',
            output_file
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Tono '{tipo}' creado: {output_file}")
        return output_file
    else:
        print(f"❌ Error creando tono: {result.stderr[:200]}")
        return None

# Función para verificar si ffmpeg está instalado
def verificar_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg está instalado correctamente")
            return True
        else:
            print("❌ FFmpeg no está instalado o no es accesible desde la línea de comandos")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg no está instalado. Instálalo desde: https://ffmpeg.org/download.html")
        return False

# Función para probar todos los tonos
def probar_todos_los_tonos():
    """Crea un ejemplo de cada tipo de tono"""
    tipos = ["beep", "click", "silence", "fade"]
    
    for tipo in tipos:
        print(f"\n🔊 Creando tono de tipo: {tipo}")
        archivo = crear_tono_separador(tipo=tipo, duracion=1.0, frecuencia=1000)
        
        if archivo and os.path.exists(archivo):
            tamaño = os.path.getsize(archivo) / 1024  # Tamaño en KB
            print(f"   Tamaño del archivo: {tamaño:.1f} KB")
        else:
            print(f"   ❌ No se pudo crear el archivo")

# Función para reproducir un tono (solo en sistemas con capacidad de reproducción)
def reproducir_tono(archivo_audio):
    """Intenta reproducir el tono creado"""
    try:
        # Para Windows
        if os.name == 'nt':
            os.startfile(archivo_audio)
        # Para macOS
        elif os.name == 'posix':
            subprocess.run(['afplay', archivo_audio])
        # Para Linux con VLC (puede necesitar instalación)
        else:
            subprocess.run(['vlc', '--play-and-exit', archivo_audio])
    except:
        print(f"⚠️ No se pudo reproducir automáticamente. Abre el archivo manualmente: {archivo_audio}")

# Ejecutar las pruebas
if __name__ == "__main__":
    print("🎵 PROBANDO GENERADOR DE TONOS DE SEPARACIÓN 🎵")
    print("=" * 50)
    
    # Verificar ffmpeg
    if not verificar_ffmpeg():
        exit(1)
    
    # Probar crear un tono específico
    print("\n1. Probando tono 'beep' de 0.5 segundos a 1200Hz:")
    tono_beep = crear_tono_separador(tipo="beep", duracion=0.5, frecuencia=1200)
    
    if tono_beep:
        print(f"   Archivo creado: {tono_beep}")
        
        # Preguntar si quiere reproducir
        '''respuesta = input("\n¿Quieres reproducir el tono? (s/n): ").lower()
        if respuesta == 's':
            reproducir_tono(tono_beep)'''
    
    # Probar todos los tonos
    print("\n2. Probando todos los tipos de tonos:")
    respuesta = input("¿Quieres crear ejemplos de todos los tipos? (s/n): ").lower()
    if respuesta == 's':
        probar_todos_los_tonos()
    
    print("\n🎉 ¡Pruebas completadas! 🎉")
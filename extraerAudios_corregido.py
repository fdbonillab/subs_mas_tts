# extraerAudios_corregido.py
import subprocess
import re
import sys
import os
from pathlib import Path
from datetime import timedelta

def verificar_ffmpeg():
    """Verifica si FFmpeg está instalado"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              shell=True)
        return result.returncode == 0
    except:
        return False

def formatear_tiempo_ffmpeg(segundos_totales):
    """Convierte segundos a formato HH:MM:SS.MMM para FFmpeg"""
    horas = int(segundos_totales // 3600)
    minutos = int((segundos_totales % 3600) // 60)
    segundos = segundos_totales % 60
    
    # Formato con 2 decimales para los segundos
    return f"{horas:02d}:{minutos:02d}:{segundos:06.3f}"

def parse_srt_time(time_str):
    """Convierte tiempo SRT a segundos totales"""
    try:
        # Limpiar la cadena
        time_str = time_str.strip()
        
        # Detectar formato (00:00:00,000 o 00:00:00.000)
        if ',' in time_str:
            hms, ms = time_str.split(',')
            ms = ms.ljust(3, '0')[:3]  # Asegurar 3 dígitos
        elif '.' in time_str:
            hms, ms = time_str.split('.')
            ms = ms.ljust(3, '0')[:3]
        else:
            hms = time_str
            ms = "000"
        
        # Separar horas, minutos, segundos
        partes = hms.split(':')
        if len(partes) == 3:
            horas, minutos, segundos = partes
        elif len(partes) == 2:
            horas = 0
            minutos, segundos = partes
        else:
            horas = 0
            minutos = 0
            segundos = partes[0]
        
        # Convertir a segundos totales
        total_segundos = (int(horas) * 3600 + 
                         int(minutos) * 60 + 
                         int(segundos) + 
                         int(ms) / 1000.0)
        
        return total_segundos
        
    except Exception as e:
        print(f"Error parseando tiempo '{time_str}': {e}")
        return 0

def extraer_escena(video_path, start_time_sec, duration_sec, output_path):
    """Extrae una escena usando FFmpeg"""
    
    # Formatear tiempos correctamente
    start_formatted = formatear_tiempo_ffmpeg(start_time_sec)
    
    print(f"  Tiempo inicio: {start_formatted}")
    print(f"  Duración: {duration_sec:.2f}s")
    
    # Método 1: Copia directa (rápido)
    cmd = [
        'ffmpeg',
        '-ss', start_formatted,
        '-i', video_path,
        '-t', str(duration_sec),
        '-c', 'copy',           # Copiar sin recompresión
        '-avoid_negative_ts', 'make_zero',
        '-y',                   # Sobrescribir
        output_path
    ]
    
    # Método alternativo si falla (recompresión)
    cmd_alt = [
        'ffmpeg',
        '-ss', start_formatted,
        '-i', video_path,
        '-t', str(duration_sec),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
        output_path
    ]
    
    try:
        # Intentar copia directa primero
        print(f"  Ejecutando FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"  ⚠ Falló copia directa, intentando recompresión...")
            result = subprocess.run(cmd_alt, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                return True
            else:
                print(f"  ✗ Archivo creado pero vacío")
                return False
        else:
            print(f"  ✗ Error FFmpeg:")
            print(f"    {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout - muy largo")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def leer_srt(srt_path):
    """Lee y parsea archivo SRT"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except UnicodeDecodeError:
        try:
            with open(srt_path, 'r', encoding='latin-1') as f:
                contenido = f.read()
        except:
            print(f"Error leyendo {srt_path}")
            return []
    
    # Patrón mejorado para SRT
    patron = r'(\d+)\s*\r?\n(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\r?\n(.*?)(?=\r?\n\r?\n|\Z)'
    
    bloques = []
    matches = re.finditer(patron, contenido, re.DOTALL)
    
    for match in matches:
        idx = match.group(1)
        inicio = match.group(2)
        fin = match.group(3)
        texto = match.group(4).strip()
        
        # Limpiar texto (quitar números de línea si existen)
        lineas = [line.strip() for line in texto.split('\n') if line.strip()]
        texto_limpio = ' '.join(lineas)
        
        bloques.append({
            'id': idx,
            'inicio': inicio,
            'fin': fin,
            'texto': texto_limpio[:100]  # Limitar longitud
        })
    
    return bloques

def main():
    print("=" * 60)
    print("EXTRACTOR DE ESCENAS CON SUBTÍTULOS SRT")
    print("=" * 60)
    
    # Verificar FFmpeg
    if not verificar_ffmpeg():
        print("\nERROR: FFmpeg no está instalado o no está en el PATH")
        print("\nSolución:")
        print("1. Descarga FFmpeg de: https://www.gyan.dev/ffmpeg/builds/")
        print("2. Extrae la carpeta a C:\\ffmpeg\\")
        print("3. Añade C:\\ffmpeg\\bin al PATH del sistema")
        print("4. Reinicia la terminal")
        input("\nPresiona Enter para salir...")
        return
    
    print("✓ FFmpeg encontrado\n")
    
    # Buscar archivos
    carpeta = Path(".")
    
    # Buscar videos
    videos = list(carpeta.glob("*.mp4")) + list(carpeta.glob("*.mkv")) + \
             list(carpeta.glob("*.avi")) + list(carpeta.glob("*.mov"))
    
    if not videos:
        print("No se encontraron archivos de video")
        return
    
    print("Archivos de video encontrados:")
    for i, video in enumerate(videos, 1):
        tamano_mb = video.stat().st_size / (1024 * 1024)
        print(f"  {i}. {video.name} ({tamano_mb:.1f} MB)")
    
    seleccion = input(f"\nSelecciona video (1-{len(videos)}): ")
    if seleccion.isdigit() and 1 <= int(seleccion) <= len(videos):
        video_path = videos[int(seleccion)-1]
    else:
        video_path = videos[0]
    
    # Buscar subtítulos
    subtitulos = list(carpeta.glob("*.srt")) + list(carpeta.glob("*.ass"))
    
    if not subtitulos:
        print("\nNo se encontraron archivos de subtítulos (.srt, .ass)")
        return
    
    print("\nArchivos de subtítulos encontrados:")
    for i, sub in enumerate(subtitulos, 1):
        print(f"  {i}. {sub.name}")
    
    seleccion = input(f"\nSelecciona subtítulos (1-{len(subtitulos)}): ")
    if seleccion.isdigit() and 1 <= int(seleccion) <= len(subtitulos):
        srt_path = subtitulos[int(seleccion)-1]
    else:
        srt_path = subtitulos[0]
    
    print(f"\n● Video: {video_path.name}")
    print(f"● Subtítulos: {srt_path.name}")
    
    # Leer SRT
    print("\nLeyendo subtítulos...")
    bloques = leer_srt(srt_path)
    
    if not bloques:
        print("No se pudieron leer los subtítulos")
        return
    
    print(f"✓ Encontrados {len(bloques)} bloques de diálogo\n")
    
    # Mostrar algunos ejemplos
    print("Primeros 5 bloques encontrados:")
    for i, bloque in enumerate(bloques[:5], 1):
        print(f"  {i}. [{bloque['inicio']} --> {bloque['fin']}]")
        print(f"     Texto: {bloque['texto'][:50]}...")
    
    # Preguntar cómo procesar
    print("\n" + "-" * 60)
    print("OPCIONES DE PROCESAMIENTO:")
    print("1. Extraer TODAS las escenas")
    print("2. Extraer solo las primeras N escenas")
    print("3. Extraer cada X escenas (muestreo)")
    print("4. Extraer escenas específicas (por rango)")
    
    opcion = input("\nSelecciona opción (1-4): ")
    
    if opcion == "2":
        n = int(input("¿Cuántas escenas extraer?: "))
        bloques = bloques[:n]
    elif opcion == "3":
        x = int(input("¿Extraer cada cuántas escenas?: "))
        bloques = bloques[::x]
    elif opcion == "4":
        inicio = int(input("Escena inicial (número): ")) - 1
        fin = int(input("Escena final (número): "))
        bloques = bloques[inicio:fin]
    
    # Crear carpeta de salida
    carpeta_salida = Path("escenas_extraidas")
    carpeta_salida.mkdir(exist_ok=True)
    
    print(f"\n● Procesando {len(bloques)} escenas")
    print(f"● Carpeta de salida: {carpeta_salida}")
    print("-" * 60 + "\n")
    
    exitosos = 0
    for i, bloque in enumerate(bloques, 1):
        print(f"[{i}/{len(bloques)}] Bloque {bloque['id']}")
        print(f"  Texto: {bloque['texto'][:80]}...")
        
        # Convertir tiempos
        inicio_sec = parse_srt_time(bloque['inicio'])
        fin_sec = parse_srt_time(bloque['fin'])
        duracion = fin_sec - inicio_sec
        
        if duracion <= 0:
            print(f"  ⚠ Duración inválida, saltando...")
            continue
        
        # Crear nombre de archivo seguro
        texto_limpio = re.sub(r'[^\w\s]', '', bloque['texto'])
        texto_limpio = re.sub(r'\s+', '_', texto_limpio.strip())
        if not texto_limpio:
            texto_limpio = f"escena_{bloque['id']}"
        else:
            texto_limpio = texto_limpio[:30]
        
        nombre_archivo = f"{bloque['id'].zfill(4)}_{texto_limpio}.mp4"
        output_path = carpeta_salida / nombre_archivo
        
        # Extraer escena
        if extraer_escena(str(video_path), inicio_sec, duracion, str(output_path)):
            exitosos += 1
            print(f"  ✓ Extraído: {nombre_archivo}")
        else:
            print(f"  ✗ Falló")
        
        print()  # Línea en blanco
    
    # Resumen
    print("=" * 60)
    print("RESUMEN DEL PROCESO")
    print("=" * 60)
    print(f"● Total de escenas procesadas: {len(bloques)}")
    print(f"● Escenas exitosas: {exitosos}")
    print(f"● Fallos: {len(bloques) - exitosos}")
    print(f"● Carpeta con resultados: {carpeta_salida.absolute()}")
    
    if exitosos > 0:
        # Mostrar tamaño total
        total_bytes = sum(f.stat().st_size for f in carpeta_salida.glob("*.mp4"))
        total_mb = total_bytes / (1024 * 1024)
        print(f"● Tamaño total: {total_mb:.1f} MB")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
import subprocess
import os

def crear_beep_simple(frecuencia, duracion=0.15, volumen=0.3, 
                     tipo="suave", output_file=None):
    """
    Crea beeps sutiles para audiolibros - versión simplificada
    
    Parámetros:
    -----------
    frecuencia : int - Frecuencia en Hz (recomendado: 300-800 Hz)
    duracion : float - Duración en segundos (0.1-0.3s)
    volumen : float - Nivel de volumen (0.0 a 1.0)
    tipo : str - "suave", "fade", "corto", "normal"
    output_file : str - Nombre del archivo de salida
    """
    
    if output_file is None:
        output_file = f'beep_{frecuencia}hz_{tipo}.mp3'
    
    # Construir filtro de audio según tipo
    if tipo == "suave":
        filtro = f'volume={volumen},afade=t=in:st=0:d=0.05,afade=t=out:st={duracion-0.05}:d=0.05'
    elif tipo == "fade":
        filtro = f'volume={volumen*0.8},afade=t=in:st=0:d={duracion*0.4},afade=t=out:st={duracion*0.6}:d={duracion*0.4}'
    elif tipo == "corto":
        filtro = f'volume={volumen*0.6}'
    else:
        filtro = f'volume={volumen}'
    
    # Comando FFmpeg más simple
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'sine=frequency={frecuencia}:duration={duracion}',
        '-af', filtro,
        '-c:a', 'libmp3lame',
        '-q:a', '7',
        '-y',  # Sobrescribir sin preguntar
        output_file
    ]
    
    # Ejecutar y capturar resultado
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Verificar que el archivo se creó
        if os.path.exists(output_file):
            size_kb = os.path.getsize(output_file) / 1024
            print(f"✅ {output_file} - {frecuencia}Hz, {duracion}s, vol {volumen} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"❌ Archivo no creado: {output_file}")
            return False
    else:
        # Mostrar error breve
        error_lines = result.stderr.split('\n')
        for line in error_lines:
            if 'error' in line.lower():
                print(f"❌ Error: {line[:100]}")
                break
        return False

def generar_tonos_suaves():
    """Genera solo tonos suaves para audiolibros"""
    
    print("🎵 GENERANDO TONOS SUAVES PARA AUDIOLIBROS")
    print("=" * 50)
    
    # Tonos más suaves (bajas frecuencias, volumen bajo)
    tonos_suaves = [
        # (frecuencia, duración, volumen, tipo, descripción)
        (320, 0.12, 5, "suave", "tono_muy_suave"),
        (350, 0.15, 5, "suave", "tono_suave_medio"),
        (400, 0.15, 5, "suave", "tono_estandar"),
        (450, 0.1, 5, "corto", "tono_corto"),
        (500, 0.2, 5, "fade", "tono_con_fade"),
        (550, 0.18, 5, "suave", "tono_intermedio"),
        (600, 0.25, 5, "fade", "tono_largo_fade"),
    ]
    
    archivos_creados = []
    
    for freq, dur, vol, tipo, desc in tonos_suaves:
        nombre = f"{desc}_{freq}hz.mp3"
        if crear_beep_simple(freq, dur, vol, tipo, nombre):
            archivos_creados.append(nombre)
    
    print(f"\n📊 Resumen: {len(archivos_creados)} tonos creados exitosamente")
    
    # Crear archivo de resumen
    with open("tonos_creados.txt", "w", encoding="utf-8") as f:
        f.write("TONOS SUAVES CREADOS PARA AUDIOLIBRO\n")
        f.write("=" * 40 + "\n\n")
        for archivo in archivos_creados:
            f.write(f"- {archivo}\n")
    
    print("📝 Lista de tonos guardada en: tonos_creados.txt")
    
    return archivos_creados

def generar_variantes_frecuencia(frecuencia_base=400):
    """Genera variaciones sutiles alrededor de una frecuencia base"""
    
    print(f"\n🎵 VARIANTES DE {frecuencia_base}Hz")
    print("-" * 30)
    
    variantes = [
        (frecuencia_base - 50, 0.15, 0.3, "suave", f"variante_baja_{frecuencia_base-50}"),
        (frecuencia_base, 0.15, 0.3, "suave", f"base_{frecuencia_base}"),
        (frecuencia_base + 50, 0.15, 0.3, "suave", f"variante_alta_{frecuencia_base+50}"),
        (frecuencia_base, 0.1, 0.25, "corto", f"corto_{frecuencia_base}"),
        (frecuencia_base, 0.2, 0.35, "fade", f"largo_{frecuencia_base}"),
    ]
    
    for freq, dur, vol, tipo, nombre in variantes:
        crear_beep_simple(freq, dur, vol, tipo, f"{nombre}.mp3")

# --- EJECUCIÓN DIRECTA SIN MENÚS ---
if __name__ == "__main__":
    # Verificar FFmpeg rápidamente
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, timeout=2)
        print("✅ FFmpeg disponible\n")
    except:
        print("❌ FFmpeg no encontrado. Instálalo primero.")
        exit(1)
    
    # Generar tonos suaves directamente
    generar_tonos_suaves()
    
    # Preguntar si quiere variantes
    print("\n¿Generar variantes de 400Hz? (s/n): ", end="")
    respuesta = input().lower()
    
    if respuesta == 's':
        generar_variantes_frecuencia(400)
    
    print("\n🎉 Proceso completado. Los tonos están listos en la carpeta actual.")
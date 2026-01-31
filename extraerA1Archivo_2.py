import pysrt
import subprocess
import os

# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

# Crear archivo de lista para FFmpeg
list_file = 'lista_audio.txt'

print(f"Procesando solo una parte de los subtitulos ")

with open(list_file, 'w', encoding='utf-8') as f:
    for i in range(0, 5):  # Saltar de 3 en 3
        # Tomar 3 subtítulos seguidos
        sub1 = subs[i]
        
        # El bloque va desde el inicio del primero hasta el final del tercero
        start = sub1.start.to_time()
        end = sub1.end.to_time()
        
        # Calcular duración
        duration_seconds = (end.hour * 3600 + end.minute * 60 + end.second + end.microsecond/1e6) - \
                          (start.hour * 3600 + start.minute * 60 + start.second + start.microsecond/1e6)
        
        # Formatear tiempos para FFmpeg
        start_str = f'{start.hour:02}:{start.minute:02}:{start.second:02}.{start.microsecond//1000:03}'
        end_str = f'{end.hour:02}:{end.minute:02}:{end.second:02}.{end.microsecond//1000:03}'
        
        # Escribir en el archivo de lista
        f.write(f"file '{os.path.abspath(video)}'\n")
        f.write(f"inpoint {start_str}\n")
        f.write(f"outpoint {end_str}\n")
        
        # Mostrar progreso
        texto_resumen = f"{sub1.text[:20]}... | {sub1.text[:20]}... | {sub1.text[:20]}..."
        print(f"[{(i//3)+1:03d}] Subtítulos {i+1}-{i+3}: {texto_resumen}")

# Archivo de salida final
output_file = 'audio_completo_combinado.mp3'

print(f"\nCombinando en '{output_file}'...")

# Comando para combinar TODO en un solo paso
cmd = [
    'ffmpeg',
    '-f', 'concat',
    '-safe', '0',
    '-i', list_file,
    '-c:a', 'libmp3lame',  # Codec de audio MP3
    '-q:a', '2',           # Calidad buena (0=mejor, 9=peor)
    '-map', '0:a',         # Solo audio
    '-y',                  # Sobrescribir
    output_file
]

# Ejecutar
result = subprocess.run(cmd)

# Limpiar archivo temporal
os.remove(list_file)

if result.returncode == 0:
    print(f"\n✅ ¡Combinación exitosa!")
    print(f"   Archivo: {output_file}")
    print(f"   Bloques: {len(subs) // 3}")
    print(f"   Subtítulos totales: {(len(subs) // 3) * 3}")
else:
    print("\n❌ Error en la combinación")
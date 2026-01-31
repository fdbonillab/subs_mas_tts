import pysrt
import subprocess
import os

# Configuración
video =  'primeros_10min.mp4' ##'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

# Crear archivo de lista para FFmpeg
list_file = 'lista_video.txt'

print(f"Procesando {len(subs)} subtítulos para un solo archivo...")

# Crear el archivo de lista con todos los segmentos
with open(list_file, 'w', encoding='utf-8') as f:
    for i, sub in enumerate(subs):
        start = sub.start.to_time()
        
        # Convertir a formato FFmpeg
        start_str = f'{start.hour:02}:{start.minute:02}:{start.second:02}.{start.microsecond//1000:03}'
        
        # Calcular el punto final
        end = sub.end.to_time()
        end_str = f'{end.hour:02}:{end.minute:02}:{end.second:02}.{end.microsecond//1000:03}'
        
        # Escribir en el archivo de lista
        f.write(f"file '{os.path.abspath(video)}'\n")
        f.write(f"inpoint {start_str}\n")
        f.write(f"outpoint {end_str}\n")
        
        # Mostrar progreso cada 10 subtítulos
        if (i + 1) % 10 == 0:
            print(f"Procesados: {i + 1}/{len(subs)} subtítulos")

# Archivo de salida final
output = 'todos_los_subtitulos_combinados_10m.mp4'

print(f"\nCombinando todos los segmentos en '{output}'...")

# Comando para combinar TODO en un solo archivo
cmd = [
    'ffmpeg',
    '-f', 'concat',
    '-safe', '0',
    '-i', list_file,
    '-c:v', 'libx264',      # Codec de video
    '-c:a', 'aac',          # Codec de audio
    '-crf', '23',           # Calidad (18-28, más bajo = mejor)
    '-preset', 'medium',    # Velocidad de encoding
    '-y',                   # Sobrescribir
    output
]

# Ejecutar
subprocess.run(cmd)

# Limpiar archivo temporal
os.remove(list_file)

print(f"\n✅ ¡Combinación exitosa!")
print(f"   Archivo final: {output}")
print(f"   Subtítulos combinados: {len(subs)}")
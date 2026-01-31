import pysrt
import subprocess
import re
import os

# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

# Crear directorio para los audios si no existe
output_dir = 'bloques_audio'
os.makedirs(output_dir, exist_ok=True)

# Extraer bloques de 3 subtítulos
num_bloques = len(subs) // 3

for bloque_num in range(num_bloques):
    start_index = bloque_num * 3
    end_index = start_index + 3
    
    selected_subs = subs[start_index:end_index]
    
    # Usar el primer y último subtítulo para tiempos
    first_sub = selected_subs[0]
    last_sub = selected_subs[-1]
    
    start = first_sub.start.to_time()
    start_str = f'{start.hour:02}:{start.minute:02}:{start.second:02}.{start.microsecond//1000:03}'
    duration = (last_sub.end - first_sub.start).ordinal / 1000.0
    
    # Crear nombre descriptivo
    textos = [re.sub(r'[^\w\s]', '', sub.text)[:15] for sub in selected_subs]
    clean_text = "_".join(textos).replace(' ', '_')[:60]
    
    # Nombre del archivo
    output = f'{output_dir}/bloque_{bloque_num + 1:03d}_subs_{start_index + 1}-{end_index}_{clean_text}.mp3'
    
    # Comando FFmpeg
    cmd = [
        'ffmpeg', '-ss', start_str, '-i', video,
        '-t', str(duration),
        '-q:a', '2',  # Buena calidad
        '-map', 'a',
        '-acodec', 'libmp3lame',
        '-y',  # Sobrescribir si existe
        output
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f'Bloque {bloque_num + 1:03d}/{num_bloques}: {output}')
    print(f'  Subtítulos: {start_index + 1}-{end_index}')
    print(f'  Duración: {duration:.1f}s')
    print(f'  Texto: {" | ".join([s.text[:30] + "..." if len(s.text) > 30 else s.text for s in selected_subs])}')
    print()

print(f'\n✅ Extraídos {num_bloques} bloques de audio en la carpeta "{output_dir}/"')
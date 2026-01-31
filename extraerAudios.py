# Instalar dependencias
# pip install pysrt opencv-python

# Script Python para extraer escenas
# python -c "
import pysrt
import subprocess
import re

video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

for i, sub in enumerate(subs):
    start = sub.start.to_time()
    end = sub.end.to_time()
    
    # Convertir a formato FFmpeg
    start_str = f'{start.hour:02}:{start.minute:02}:{start.second:02}.{start.microsecond//1000:03}'
    duration = (sub.end - sub.start).ordinal / 1000.0
    
    # Limpiar texto para nombre de archivo
    clean_text = re.sub(r'[^\w\s]', '', sub.text)[:30].replace(' ', '_')
    
    output = f'escena_{i+1:03d}_{clean_text}.mp4'
    
    cmd = [
        'ffmpeg', '-ss', start_str, '-i', video,
        '-t', str(duration), '-c', 'copy', output
    ]
    
    subprocess.run(cmd)
    print(f'Extraído: {output}')

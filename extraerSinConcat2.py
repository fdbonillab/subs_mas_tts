import pysrt
import subprocess
import os

# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

print(f"Extrayendo diálogos individualmente...\n")

for i in range(0, min(3, len(subs))):
    sub = subs[i]
    
    # Convertir tiempos
    start = sub.start
    end = sub.end
    
    # Calcular duración
    duration_sec = (end.hours * 3600 + end.minutes * 60 + end.seconds + end.milliseconds/1000) - \
                   (start.hours * 3600 + start.minutes * 60 + start.seconds + start.milliseconds/1000)
    
    # Formatear para FFmpeg
    start_str = f'{start.hours:02}:{start.minutes:02}:{start.seconds:02}.{start.milliseconds:03}'
    end_str = f'{end.hours:02}:{end.minutes:02}:{(end.seconds+1):02}.{end.milliseconds:03}'
    
    output_file = f'dialogo_{i+1:02d}.mp3'
    
    print(f"=== Diálogo {i+1} ===")
    print(f"Tiempo: {start_str} -> {end_str}")
    print(f"Duración: {duration_sec:.1f} segundos")
    print(f"Texto: {sub.text}")
    print(f"Extrayendo a: {output_file}")
    
    # Comando FFmpeg CORREGIDO: -ss y -to DESPUÉS de -i
    cmd = [
        'ffmpeg',
        '-i', video,        # PRIMERO el input
        '-ss', start_str,   # LUEGO el tiempo de inicio
        '-to', end_str,     # LUEGO el tiempo de fin
        '-q:a', '2',        # Calidad de audio
        '-map', '0:a',      # Solo audio
        '-y',               # Sobrescribir
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Extraído: {output_file}")
        
        # Verificar duración real
        cmd_check = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            output_file
        ]
        
        check_result = subprocess.run(cmd_check, capture_output=True, text=True)
        if check_result.returncode == 0:
            actual_duration = float(check_result.stdout.strip())
            print(f"   Duración real: {actual_duration:.2f}s (esperada: {duration_sec:.2f}s)")
            
            if abs(actual_duration - duration_sec) > 0.1:
                print(f"   ⚠️  Diferencia: {actual_duration - duration_sec:.3f}s")
    else:
        print(f"❌ Error: {result.stderr}")
    
    print()

print("\n🎧 Escucha los archivos generados:")
for i in range(0, min(3, len(subs))):
    print(f"  dialogo_{i+1:02d}.mp3")
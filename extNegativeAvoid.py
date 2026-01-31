import pysrt
import subprocess
import os

# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

print(f"Extrayendo primeros 3 diálogos individualmente...\n")

for i in range(0, min(3, len(subs))):
    sub = subs[i]
    
    # Convertir tiempos
    start = sub.start
    end = sub.end
    
    # Agregar margen de 0.5 segundos
    start_sec = start.hours * 3600 + start.minutes * 60 + start.seconds + start.milliseconds/1000
    end_sec = end.hours * 3600 + end.minutes * 60 + end.seconds + end.milliseconds/1000
    
    # Margen pequeño
    start_sec = max(0, start_sec - 0.2)  # 0.2 segundos antes
    end_sec = end_sec + 0.2  # 0.2 segundos después
    
    # Convertir de vuelta a string
    start_h = int(start_sec // 3600)
    start_m = int((start_sec % 3600) // 60)
    start_s = int(start_sec % 60)
    start_ms = int((start_sec - int(start_sec)) * 1000)
    
    end_h = int(end_sec // 3600)
    end_m = int((end_sec % 3600) // 60)
    end_s = int(end_sec % 60)
    end_ms = int((end_sec - int(end_sec)) * 1000)
    
    start_str = f'{start_h:02}:{start_m:02}:{start_s:02}.{start_ms:03}'
    end_str = f'{end_h:02}:{end_m:02}:{end_s:02}.{end_ms:03}'
    
    output_file = f'dialogo_{i+1:02d}.mp3'
    
    print(f"=== Diálogo {i+1} ===")
    print(f"Tiempo original: {sub.start} -> {sub.end}")
    print(f"Tiempo con margen: {start_str} -> {end_str}")
    print(f"Texto: {sub.text}")
    
    # Comando FFmpeg con máxima precisión
    cmd = [
        'ffmpeg',
        '-i', video,
        '-ss', str(start_sec),      # Usar segundos directamente
        '-t', str(end_sec - start_sec),  # Duración en lugar de tiempo final
        '-q:a', '2',
        '-map', '0:a',
        '-avoid_negative_ts', 'make_zero',  # Evitar problemas de tiempo
        '-y',
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Extraído: {output_file}")
        
        # Verificación detallada
        cmd_check = ['ffprobe', '-i', output_file, '-show_entries', 'format', '-v', 'quiet']
        check_result = subprocess.run(cmd_check, capture_output=True, text=True)
        
        if 'duration' in check_result.stdout:
            import re
            match = re.search(r'duration=([\d.]+)', check_result.stdout)
            if match:
                actual_duration = float(match.group(1))
                expected_duration = end_sec - start_sec
                print(f"   Duración: {actual_duration:.2f}s (esperada: {expected_duration:.2f}s)")
                print(f"   Diferencia: {actual_duration - expected_duration:.3f}s")
    else:
        print(f"❌ Error: {result.stderr[:200]}...")
    
    print()

print("\n🎧 Archivos generados:")
for i in range(0, min(3, len(subs))):
    if os.path.exists(f'dialogo_{i+1:02d}.mp3'):
        size = os.path.getsize(f'dialogo_{i+1:02d}.mp3') / 1024
        print(f"  dialogo_{i+1:02d}.mp3 ({size:.1f} KB)")
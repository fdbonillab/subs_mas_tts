# extraerAudios_simple.py
import subprocess
import re
import sys

def parse_srt_time(time_str):
    """Convierte tiempo SRT (00:00:00,000) a segundos"""
    try:
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split(',')
        total_seconds = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
        return total_seconds
    except:
        # Si falla, probar formato alternativo (00:00:00.000)
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split('.')
        total_seconds = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
        return total_seconds

def extract_scenes_with_ffmpeg(video_file, srt_file, output_prefix="escena"):
    """Extrae escenas basadas en tiempos del SRT usando FFmpeg"""
    
    # Leer archivo SRT
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrón para extraer bloques SRT
    pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n(.*?)(?=\n\n|\Z)'
    
    # Buscar todos los bloques
    blocks = re.findall(pattern, content, re.DOTALL)
    
    print(f"Encontrados {len(blocks)} bloques de subtítulos")
    
    for i, block in enumerate(blocks):
        idx, start_time, end_time, text = block
        
        # Limpiar texto (quitar líneas extra)
        text_lines = text.strip().split('\n')
        dialog_text = text_lines[0] if text_lines else ""
        
        # Convertir tiempos
        start_sec = parse_srt_time(start_time)
        end_sec = parse_srt_time(end_time)
        duration = end_sec - start_sec
        
        # Formatear tiempo para FFmpeg (HH:MM:SS.MMM)
        start_ff = f"{int(start_sec//3600):02d}:{int((start_sec%3600)//60):02d}:{start_sec%60:06.3f}"
        
        # Crear nombre de archivo seguro
        safe_text = re.sub(r'[^\w\s]', '', dialog_text)
        safe_text = re.sub(r'\s+', '_', safe_text.strip())
        safe_text = safe_text[:30]  # Limitar longitud
        
        output_file = f"{output_prefix}_{i+1:03d}_{safe_text}.mp4"
        
        # Comando FFmpeg para extraer escena
        cmd = [
            'ffmpeg',
            '-ss', start_ff,
            '-i', video_file,
            '-t', str(duration),
            '-c', 'copy',  # Copiar sin recompresión
            '-avoid_negative_ts', 'make_zero',
            output_file
        ]
        
        print(f"Extrayendo escena {i+1}: {dialog_text[:50]}...")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ Guardado como: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error al extraer escena {i+1}: {e}")
            # Intentar con recompresión si falla
            cmd_alt = [
                'ffmpeg',
                '-ss', start_ff,
                '-i', video_file,
                '-t', str(duration),
                output_file
            ]
            try:
                subprocess.run(cmd_alt, check=True, capture_output=True)
                print(f"  ✓ Extraído con recompresión: {output_file}")
            except:
                print(f"  ✗ Error grave, saltando escena {i+1}")

if __name__ == "__main__":
    # Archivos de entrada
    video_file = "The.Matrix.1999.mp4"
    srt_file = "The.Matrix.1999.srt"
    
    # Si no existe el SRT, buscar alternativas
    import os
    
    if not os.path.exists(srt_file):
        # Buscar cualquier archivo .srt en la carpeta
        srt_files = [f for f in os.listdir() if f.endswith('.srt')]
        if srt_files:
            srt_file = srt_files[0]
            print(f"Usando archivo SRT encontrado: {srt_file}")
        else:
            print("Error: No se encontró archivo SRT")
            print("Coloca un archivo .srt en la misma carpeta que el video")
            sys.exit(1)
    
    if not os.path.exists(video_file):
        # Buscar cualquier archivo de video
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov']
        video_files = [f for f in os.listdir() if any(f.endswith(ext) for ext in video_extensions)]
        if video_files:
            video_file = video_files[0]
            print(f"Usando archivo de video encontrado: {video_file}")
        else:
            print("Error: No se encontró archivo de video")
            sys.exit(1)
    
    # Extraer escenas
    extract_scenes_with_ffmpeg(video_file, srt_file, "escena_matrix")
    
    print("\n¡Proceso completado!")
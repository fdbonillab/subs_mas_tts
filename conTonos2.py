import pysrt
import subprocess
import os
import random

# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

print(f"Extrayendo diálogos agrupando bloques cercanos...\n")

def segundos_a_str(segundos):
    """Convierte segundos a string HH:MM:SS.ms"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milisegundos = int((segundos - int(segundos)) * 1000)
    return f"{horas:02}:{minutos:02}:{segs:02}.{milisegundos:03}"

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
            '-af', 'afade=t=in:st=0:d=0.1,afade=t=out:st={duracion-0.1}:d=0.1',
            '-c:a', 'libmp3lame',
            '-q:a', '9',
            '-y',
            output_file
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return output_file
    else:
        print(f"❌ Error creando tono: {result.stderr[:100]}")
        return None

# Configuración
MAX_ESPACIO_ENTRE_BLOQUES = 2.0  # Máximo 2 segundos para unir bloques
MARGEN_FIN_GRUPO = 1.0  # Margen al final de cada grupo (cambiaste de 0.1 a 1)
TIPO_TONO = "beep"  # Opciones: "beep", "click", "silence", "fade"
DURACION_TONO = 0.3  # Duración del tono en segundos

grupos = []
grupo_actual = []
archivos_temporales = []
archivos_tonos = []

# 1. Crear tono de separación
tono_separador = crear_tono_separador(
    tipo=TIPO_TONO, 
    duracion=DURACION_TONO,
    frecuencia=800
)
if tono_separador:
    archivos_tonos.append(tono_separador)
    print(f"✅ Tono de separación creado: {tono_separador} ({TIPO_TONO}, {DURACION_TONO}s)")

# 2. Agrupar subtítulos cercanos
for i in range(len(subs)):
    if not grupo_actual:
        # Primer subtítulo del grupo
        grupo_actual.append(i)
    else:
        # Verificar distancia con el anterior
        sub_actual = subs[i]
        sub_anterior = subs[grupo_actual[-1]]
        
        # Calcular espacio entre fin del anterior e inicio del actual
        fin_anterior = sub_anterior.end.ordinal / 1000.0  # en segundos
        inicio_actual = sub_actual.start.ordinal / 1000.0  # en segundos
        espacio = inicio_actual - fin_anterior
        
        if espacio <= MAX_ESPACIO_ENTRE_BLOQUES:
            # Están cerca, agregar al mismo grupo
            grupo_actual.append(i)
        else:
            # Están lejos, cerrar grupo actual y empezar nuevo
            grupos.append(grupo_actual.copy())
            grupo_actual = [i]

# Agregar el último grupo
if grupo_actual:
    grupos.append(grupo_actual)

print(f"\nEncontrados {len(grupos)} grupos de diálogos cercanos")
print(f"(Uniendo bloques con menos de {MAX_ESPACIO_ENTRE_BLOQUES} segundos de separación)")
print(f"(Tono entre grupos: {TIPO_TONO}, {DURACION_TONO}s)")
print(f"(Margen final: {MARGEN_FIN_GRUPO}s)\n")

# 3. Extraer cada grupo 
lista_concat = []  # Para la concatenación final
grupos_procesados = 0

for idx_grupo, grupo in enumerate(grupos[:50]):  # Solo primeros 50 grupos
    if len(grupo) == 0:
        continue
    
    grupos_procesados += 1
    
    # Obtener primer y último subtítulo del grupo
    primer_idx = grupo[0]
    ultimo_idx = grupo[-1]
    
    sub_inicio = subs[primer_idx]
    sub_fin = subs[ultimo_idx]
    
    # Calcular tiempos del grupo
    inicio_grupo = sub_inicio.start.ordinal / 1000.0
    fin_grupo = sub_fin.end.ordinal / 1000.0
    
    # Agregar márgenes
    inicio_grupo = max(0, inicio_grupo - 0.1)  # 0.1s al inicio
    fin_grupo = fin_grupo + MARGEN_FIN_GRUPO   # 1s al final (tú lo cambiaste)
    
    # Convertir a string
    inicio_str = segundos_a_str(inicio_grupo)
    fin_str = segundos_a_str(fin_grupo)
    
    duracion_grupo = fin_grupo - inicio_grupo
    
    output_file = f'grupo_{idx_grupo+1:03d}.mp3'
    archivos_temporales.append(output_file)
    
    # Añadir a lista de concatenación
    lista_concat.append(output_file)
    
    # Añadir tono de separación (excepto después del último grupo)
    if idx_grupo < len(grupos[:50]) - 1 and tono_separador:
        lista_concat.append(tono_separador)
    
    # Mostrar información del grupo
    print(f"=== Grupo {idx_grupo+1} ===")
    print(f"Subtítulos: {primer_idx+1} a {ultimo_idx+1} ({len(grupo)} subtítulos)")
    print(f"Tiempo: {inicio_str} -> {fin_str}")
    print(f"Duración grupo: {duracion_grupo:.2f} segundos")
    
    # Mostrar textos de los subtítulos (solo primeros 3)
    for j, sub_idx in enumerate(grupo[:3]):
        sub = subs[sub_idx]
        tiempo_sub = f"{sub.start} -> {sub.end}"
        print(f"  {j+1}. [{tiempo_sub}] {sub.text[:60]}...")
    if len(grupo) > 3:
        print(f"  ... y {len(grupo) - 3} más")
    
    print(f"Extrayendo a: {output_file}")
    
    # Comando FFmpeg
    cmd = [
        'ffmpeg',
        '-i', video,
        '-ss', inicio_str,
        '-to', fin_str,
        '-q:a', '2',
        '-map', '0:a',
        '-y',
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
            print(f"   Duración real: {actual_duration:.2f}s (esperada: {duracion_grupo:.2f}s)")
            
            diferencia = abs(actual_duration - duracion_grupo)
            if diferencia > 0.1:
                print(f"   ⚠️  Diferencia: {diferencia:.3f}s")
    else:
        print(f"❌ Error: {result.stderr[:200]}")
    
    print()

# 4. Crear archivo de lista para concatenación con tonos
if lista_concat:
    print(f"\n=== Preparando concatenación con tonos ===")
    print(f"Total elementos a concatenar: {len(lista_concat)}")
    print(f"(Grupos: {grupos_procesados}, Tonos: {len(lista_concat) - grupos_procesados})")
    
    lista_file = 'lista_con_tonos.txt'
    with open(lista_file, 'w', encoding='utf-8') as f:
        for archivo in lista_concat:
            if os.path.exists(archivo):
                f.write(f"file '{os.path.abspath(archivo)}'\n")
            elif archivo == tono_separador and tono_separador:
                f.write(f"file '{os.path.abspath(tono_separador)}'\n")
    
    # Archivo final combinado con tonos
    output_final = f'dialogos_con_tonos_{TIPO_TONO}.mp3'
    
    cmd_combinar = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_file,
        '-c', 'copy',  # Copiar sin re-codificar
        '-y',
        output_final
    ]
    
    print(f"Combinando en '{output_final}'...")
    result = subprocess.run(cmd_combinar, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Verificar duración total
        cmd_check_total = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            output_final
        ]
        
        check_total = subprocess.run(cmd_check_total, capture_output=True, text=True)
        if check_total.returncode == 0:
            duracion_total = float(check_total.stdout.strip())
            print(f"✅ Combinación exitosa: {output_final}")
            print(f"   Duración total: {duracion_total:.2f} segundos")
            print(f"   Grupos combinados: {grupos_procesados}")
            print(f"   Tonos insertados: {len(lista_concat) - grupos_procesados}")
            
            # Calcular estadísticas
            horas = int(duracion_total // 3600)
            minutos = int((duracion_total % 3600) // 60)
            segundos = int(duracion_total % 60)
            print(f"   Tiempo total: {horas:02}:{minutos:02}:{segundos:02}")
    
    # Limpiar lista temporal
    if os.path.exists(lista_file):
        os.remove(lista_file)

# 5. También crear versión SIN tonos (para comparación)
if archivos_temporales:
    print(f"\n=== Creando versión SIN tonos (opcional) ===")
    
    lista_sin_tonos = 'lista_sin_tonos.txt'
    with open(lista_sin_tonos, 'w', encoding='utf-8') as f:
        for archivo in archivos_temporales:
            if os.path.exists(archivo):
                f.write(f"file '{os.path.abspath(archivo)}'\n")
    
    output_sin_tonos = 'dialogos_sin_tonos.mp3'
    
    cmd_sin_tonos = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_sin_tonos,
        '-c', 'copy',
        '-y',
        output_sin_tonos
    ]
    
    subprocess.run(cmd_sin_tonos, capture_output=True)
    print(f"✅ Versión sin tonos: {output_sin_tonos}")
    
    if os.path.exists(lista_sin_tonos):
        os.remove(lista_sin_tonos)

print(f"\n🎧 Archivos generados:")
print(f"  {output_final} (CON tonos {TIPO_TONO})")
if 'output_sin_tonos' in locals():
    print(f"  {output_sin_tonos} (SIN tonos)")
print(f"  Total grupos procesados: {grupos_procesados}")

# 6. Opción: Limpiar archivos temporales
limpiar_temporales = False  # Cambia a True si quieres limpiar

if limpiar_temporales:
    print(f"\n🧹 Limpiando archivos temporales...")
    temporales_eliminados = 0
    
    for archivo in archivos_temporales:
        if os.path.exists(archivo):
            os.remove(archivo)
            temporales_eliminados += 1
    
    for archivo in archivos_tonos:
        if os.path.exists(archivo):
            os.remove(archivo)
            temporales_eliminados += 1
    
    print(f"  Eliminados: {temporales_eliminados} archivos temporales")
else:
    print(f"\n📁 Archivos temporales guardados para depuración")
    print(f"  Grupos: {len(archivos_temporales)} archivos .mp3")
    print(f"  Tonos: {len(archivos_tonos)} archivos .mp3")

# 7. Sugerencia para probar diferentes tonos
print(f"\n💡 Sugerencia: Prueba diferentes tipos de tonos:")
print(f"  Cambia TIPO_TONO a: 'beep', 'click', 'silence', o 'fade'")
print(f"  Cambia DURACION_TONO a: 0.1, 0.3, 0.5 segundos")
print(f"  Cambia MARGEN_FIN_GRUPO a: 0.5, 1.0, 2.0 segundos")
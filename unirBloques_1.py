import pysrt
import subprocess
import os

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

# Configuración
MAX_ESPACIO_ENTRE_BLOQUES = 2.0  # Máximo 1 segundo para unir bloques
grupos = []
grupo_actual = []
archivos_temporales = []

# 1. Agrupar subtítulos cercanos
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

print(f"Encontrados {len(grupos)} grupos de diálogos cercanos")
print(f"(Uniendo bloques con menos de {MAX_ESPACIO_ENTRE_BLOQUES} segundo de separación)\n")

# 2. Extraer cada grupo 
### (grupos[:5])
for idx_grupo, grupo in enumerate(grupos[:50]):  # Solo primeros 5 grupos para prueba
    if len(grupo) == 0:
        continue
    
    # Obtener primer y último subtítulo del grupo
    primer_idx = grupo[0]
    ultimo_idx = grupo[-1]
    
    sub_inicio = subs[primer_idx]
    sub_fin = subs[ultimo_idx]
    
    # Calcular tiempos del grupo
    inicio_grupo = sub_inicio.start.ordinal / 1000.0
    fin_grupo = sub_fin.end.ordinal / 1000.0
    
    # Agregar pequeño margen (0.1 segundos)
    inicio_grupo = max(0, inicio_grupo - 0.1)
    fin_grupo = fin_grupo + 5 ### aumento  margen de 0.1 a 0.5 a 1
    
    # Convertir a string
    inicio_str = segundos_a_str(inicio_grupo)
    fin_str = segundos_a_str(fin_grupo)
    
    duracion_grupo = fin_grupo - inicio_grupo
    
    output_file = f'grupo_{idx_grupo+1:03d}.mp3'
    archivos_temporales.append(output_file)
    
    # Mostrar información del grupo
    print(f"=== Grupo {idx_grupo+1} ===")
    print(f"Subtítulos: {primer_idx+1} a {ultimo_idx+1} ({len(grupo)} subtítulos)")
    print(f"Tiempo: {inicio_str} -> {fin_str}")
    print(f"Duración grupo: {duracion_grupo:.2f} segundos")
    
    # Mostrar textos de los subtítulos
    for j, sub_idx in enumerate(grupo):
        sub = subs[sub_idx]
        tiempo_sub = f"{sub.start} -> {sub.end}"
        print(f"  {j+1}. [{tiempo_sub}] {sub.text[:60]}...")
    
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

# 3. Combinar todos los grupos en un solo archivo
if archivos_temporales:
    print(f"\n=== Combinando {len(archivos_temporales)} grupos ===")
    
    # Crear archivo de lista para concatenación
    lista_file = 'lista_combinar.txt'
    with open(lista_file, 'w', encoding='utf-8') as f:
        for archivo in archivos_temporales:
            if os.path.exists(archivo):
                f.write(f"file '{os.path.abspath(archivo)}'\n")
    
    # Archivo final combinado
    output_final = 'dialogos_combinados.mp3'
    
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
            print(f"   Archivos combinados: {len(archivos_temporales)}")
    
    # Limpiar lista temporal
    if os.path.exists(lista_file):
        os.remove(lista_file)

print("\n🎧 Archivos generados:")
print(f"  {output_final} (combinado)")
for i, archivo in enumerate(archivos_temporales[:5]):
    if os.path.exists(archivo):
        size_kb = os.path.getsize(archivo) / 1024
        print(f"  {archivo} ({size_kb:.1f} KB)")
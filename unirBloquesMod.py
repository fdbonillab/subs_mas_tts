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

def crear_tono_separador():
    """Crea un tono de separación simple"""
    output_file = f'tono_separador_{random.randint(1000, 9999)}.mp3'
    
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'sine=frequency=800:duration=0.3',
        '-af', 'volume=0.5',
        '-c:a', 'libmp3lame',
        '-q:a', '9',
        '-y',
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return output_file
    return None

# Configuración
MAX_ESPACIO_ENTRE_BLOQUES = 2.0  # Máximo 2 segundos para unir bloques
MARGEN_FIN_GRUPO = 1.0  # Margen al final de cada grupo

# 1. Crear tono de separación
tono_separador = crear_tono_separador()
if tono_separador:
    print(f"✅ Tono de separación creado: {tono_separador}")

# 2. Agrupar subtítulos cercanos (MANTIENE TU LÓGICA ORIGINAL)
grupos = []
grupo_actual = []
archivos_temporales = []

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

# 3. Extraer cada grupo (MANTIENE TU LÓGICA ORIGINAL)
for idx_grupo, grupo in enumerate(grupos[:50]):  # Solo primeros 50 grupos para prueba
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
    
    # Agregar pequeño margen (0.1 segundos al inicio, 1 al final)
    inicio_grupo = max(0, inicio_grupo - 0.1)
    fin_grupo = fin_grupo + MARGEN_FIN_GRUPO
    
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
    
    # Comando FFmpeg (MANTIENE TU LÓGICA ORIGINAL)
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

# 4. Crear DOS versiones: CON y SIN tonos

# Versión SIN tonos (tu versión original)
if archivos_temporales:
    print(f"\n=== Creando versión SIN tonos ===")
    
    lista_sin_tonos = 'lista_sin_tonos.txt'
    with open(lista_sin_tonos, 'w', encoding='utf-8') as f:
        for archivo in archivos_temporales:
            if os.path.exists(archivo):
                f.write(f"file '{os.path.abspath(archivo)}'\n")
    
    output_sin_tonos = 'dialogos_sin_tonos.mp3'
    
    cmd_combinar_sin = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_sin_tonos,
        '-c', 'copy',  # Copiar sin re-codificar
        '-y',
        output_sin_tonos
    ]
    
    print(f"Combinando en '{output_sin_tonos}'...")
    result_sin = subprocess.run(cmd_combinar_sin, capture_output=True, text=True)
    
    if result_sin.returncode == 0:
        cmd_check_total = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            output_sin_tonos
        ]
        
        check_total = subprocess.run(cmd_check_total, capture_output=True, text=True)
        if check_total.returncode == 0:
            duracion_total = float(check_total.stdout.strip())
            print(f"✅ Versión sin tonos creada: {output_sin_tonos}")
            print(f"   Duración: {duracion_total:.2f} segundos")
            print(f"   Grupos: {len(archivos_temporales)}")
    
    if os.path.exists(lista_sin_tonos):
        os.remove(lista_sin_tonos)

# Versión CON tonos (NUEVA funcionalidad)
if archivos_temporales and tono_separador:
    print(f"\n=== Creando versión CON tonos ===")
    
    lista_con_tonos = 'lista_con_tonos.txt'
    with open(lista_con_tonos, 'w', encoding='utf-8') as f:
        for i, archivo in enumerate(archivos_temporales):
            if os.path.exists(archivo):
                f.write(f"file '{os.path.abspath(archivo)}'\n")
            
            # Agregar tono después de cada grupo excepto el último
            if i < len(archivos_temporales) - 1:
                f.write(f"file '{os.path.abspath(tono_separador)}'\n")
    
    output_con_tonos = 'dialogos_con_tonos.mp3'
    
    cmd_combinar_con = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_con_tonos,
        '-c', 'copy',
        '-y',
        output_con_tonos
    ]
    
    print(f"Combinando en '{output_con_tonos}' (con tonos)...")
    print(f"Insertando {len(archivos_temporales)-1} tonos entre {len(archivos_temporales)} grupos")
    
    result_con = subprocess.run(cmd_combinar_con, capture_output=True, text=True)
    
    if result_con.returncode == 0:
        cmd_check_total = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            output_con_tonos
        ]
        
        check_total = subprocess.run(cmd_check_total, capture_output=True, text=True)
        if check_total.returncode == 0:
            duracion_total = float(check_total.stdout.strip())
            print(f"✅ Versión con tonos creada: {output_con_tonos}")
            print(f"   Duración: {duracion_total:.2f} segundos")
            print(f"   Grupos: {len(archivos_temporales)}")
            print(f"   Tonos insertados: {len(archivos_temporales)-1}")
    
    if os.path.exists(lista_con_tonos):
        os.remove(lista_con_tonos)

print(f"\n🎧 Archivos generados:")
if 'output_sin_tonos' in locals() and os.path.exists(output_sin_tonos):
    size_kb = os.path.getsize(output_sin_tonos) / 1024
    print(f"  {output_sin_tonos} ({size_kb:.1f} KB) - SIN tonos")

if 'output_con_tonos' in locals() and os.path.exists(output_con_tonos):
    size_kb = os.path.getsize(output_con_tonos) / 1024
    print(f"  {output_con_tonos} ({size_kb:.1f} KB) - CON tonos")

print(f"\n📁 Archivos temporales:")
for i, archivo in enumerate(archivos_temporales[:3]):  # Mostrar solo primeros 3
    if os.path.exists(archivo):
        size_kb = os.path.getsize(archivo) / 1024
        print(f"  {archivo} ({size_kb:.1f} KB)")

if len(archivos_temporales) > 3:
    print(f"  ... y {len(archivos_temporales) - 3} más")

# 5. Opcional: Limpiar archivos temporales
print(f"\n💡 Para limpiar archivos temporales, ejecuta:")
print("  import os")
print("  for archivo in archivos_temporales:")
print("      if os.path.exists(archivo):")
print("          os.remove(archivo)")
print(f"  if os.path.exists('{tono_separador}'):")
print(f"      os.remove('{tono_separador}')")
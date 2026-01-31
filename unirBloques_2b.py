import pysrt
import subprocess
import os
import random

# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')

def crear_tono_separador(tipo="beep", duracion=0.3, frecuencia=800, output_file=None):
    """Crea un tono de separación entre grupos"""
    
    if output_file is None:
        output_file = f'tono_{tipo}_{random.randint(1000, 9999)}.mp3'
    
    if tipo == "beep":
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'sine=frequency={frecuencia}:duration={duracion}',
            '-af', 'volume=0.8',
            '-c:a', 'libmp3lame',
            '-q:a', '2',
            '-y',
            output_file
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return output_file
    else:
        print(f"❌ Error creando tono: {result.stderr[:100]}")
        return None

def segundos_a_str(segundos):
    """Convierte segundos a string HH:MM:SS.ms"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milisegundos = int((segundos - int(segundos)) * 1000)
    return f"{horas:02}:{minutos:02}:{segs:02}.{milisegundos:03}"

# Configuración
MAX_ESPACIO_ENTRE_BLOQUES = 2.0
grupos = []
grupo_actual = []
archivos_temporales = []
archivos_tonos = []

MARGEN_FIN_GRUPO = 1.0
TIPO_TONO = "beep"
DURACION_TONO = 1.0

print("="*60)
print("🎵 CREANDO ARCHIVO MP3 CON TONOS ENTRE BLOQUES")
print("="*60)

# 1. Crear tono de separación
print(f"\n1️⃣  CREANDO TONO DE SEPARACIÓN...")
tono_separador = crear_tono_separador(
    tipo=TIPO_TONO, 
    duracion=DURACION_TONO,
    frecuencia=800,
    output_file="tono_separador_fijo.mp3"  # Nombre fijo para reutilizar
)

if tono_separador:
    # Verificar que el tono se creó correctamente
    if os.path.exists(tono_separador):
        tamano = os.path.getsize(tono_separador)
        print(f"✅ Tono creado: {tono_separador} ({tamano:,} bytes)")
        
        # Verificar duración con ffprobe
        try:
            cmd_check = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                tono_separador
            ]
            check_result = subprocess.run(cmd_check, capture_output=True, text=True)
            if check_result.returncode == 0:
                duracion_real = float(check_result.stdout.strip())
                print(f"   ⏱️  Duración: {duracion_real:.2f}s")
        except:
            pass
    else:
        print(f"❌ El archivo de tono no se creó")
        tono_separador = None
else:
    print("❌ No se pudo crear el tono de separación")
    tono_separador = None

# 1. Agrupar subtítulos
print(f"\n2️⃣  AGRUPANDO SUBTÍTULOS...")
for i in range(len(subs)):
    if not grupo_actual:
        grupo_actual.append(i)
    else:
        sub_actual = subs[i]
        sub_anterior = subs[grupo_actual[-1]]
        
        fin_anterior = sub_anterior.end.ordinal / 1000.0
        inicio_actual = sub_actual.start.ordinal / 1000.0
        espacio = inicio_actual - fin_anterior
        
        if espacio <= MAX_ESPACIO_ENTRE_BLOQUES:
            grupo_actual.append(i)
        else:
            grupos.append(grupo_actual.copy())
            grupo_actual = [i]

if grupo_actual:
    grupos.append(grupo_actual)

print(f"Encontrados {len(grupos)} grupos de diálogos")

# Tomar solo primeros 5 grupos para prueba
grupos_a_procesar = grupos[:5]
print(f"Procesando {len(grupos_a_procesar)} grupos para prueba\n")

# 2. Extraer cada grupo y agregar tonos
print("3️⃣  EXTRAYENDO GRUPOS Y AGREGANDO TONOS...")

for idx_grupo, grupo in enumerate(grupos_a_procesar):
    print(f"\n{'─'*50}")
    print(f"📁 GRUPO {idx_grupo+1}/{len(grupos_a_procesar)}")
    
    if len(grupo) == 0:
        continue
    
    # Obtener primer y último subtítulo
    primer_idx = grupo[0]
    ultimo_idx = grupo[-1]
    
    sub_inicio = subs[primer_idx]
    sub_fin = subs[ultimo_idx]
    
    # Calcular tiempos
    inicio_grupo = sub_inicio.start.ordinal / 1000.0
    fin_grupo = sub_fin.end.ordinal / 1000.0
    
    inicio_grupo = max(0, inicio_grupo - 0.1)
    fin_grupo = fin_grupo + MARGEN_FIN_GRUPO
    
    # Convertir a string
    inicio_str = segundos_a_str(inicio_grupo)
    fin_str = segundos_a_str(fin_grupo)
    
    duracion_grupo = fin_grupo - inicio_grupo
    
    # Nombre del archivo del grupo
    output_file = f'grupo_{idx_grupo+1:03d}.mp3'
    
    print(f"   Subtítulos: {len(grupo)}")
    print(f"   Tiempo: {inicio_str} → {fin_str}")
    print(f"   Duración: {duracion_grupo:.2f}s")
    print(f"   Archivo: {output_file}")
    
    # Extraer audio del grupo
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
    
    if result.returncode == 0 and os.path.exists(output_file):
        print(f"   ✅ Extraído exitosamente")
        
        # Agregar a la lista para combinar
        archivos_temporales.append(output_file)
        
        # 🔥 AGREGAR TONO DESPUÉS DE CADA GRUPO (excepto el último)
        if idx_grupo < len(grupos_a_procesar) - 1 and tono_separador:
            print(f"   ➕ Agregando tono de separación...")
            archivos_temporales.append(tono_separador)
    else:
        print(f"   ❌ Error al extraer")

# 3. CREAR ARCHIVO FINAL COMBINADO
print(f"\n{'='*60}")
print("4️⃣  CREANDO ARCHIVO FINAL COMBINADO")
print(f"{'='*60}")

if not archivos_temporales:
    print("❌ No hay archivos para combinar")
    exit()

# Verificar que todos los archivos existen
print(f"\n📋 Verificando {len(archivos_temporales)} archivos a combinar:")
archivos_validos = []
for i, archivo in enumerate(archivos_temporales):
    if os.path.exists(archivo):
        tamano = os.path.getsize(archivo)
        tipo = "GRUPO" if "grupo" in archivo else "TONO"
        archivos_validos.append(archivo)
        print(f"   {i+1:02d}. ✅ [{tipo}] {archivo} ({tamano:,} bytes)")
    else:
        print(f"   {i+1:02d}. ❌ {archivo} (NO EXISTE)")

if not archivos_validos:
    print("❌ No hay archivos válidos para combinar")
    exit()

# Crear archivo de lista para ffmpeg
lista_file = 'lista_combinar.txt'
print(f"\n📝 Creando lista de combinación: {lista_file}")

with open(lista_file, 'w', encoding='utf-8') as f:
    for archivo in archivos_validos:
        ruta_absoluta = os.path.abspath(archivo)
        # En Windows, necesitamos escapar las barras invertidas
        ruta_absoluta = ruta_absoluta.replace('\\', '/')
        f.write(f"file '{ruta_absoluta}'\n")

# Archivo final
output_final = 'dialogos_con_tonos.mp3'
print(f"\n🔗 Combinando en: {output_final}")

# Comando para combinar
cmd_combinar = [
    'ffmpeg',
    '-f', 'concat',
    '-safe', '0',
    '-i', lista_file,
    '-c', 'copy',
    '-y',
    output_final
]

print(f"\n⚙️  Ejecutando comando ffmpeg...")
result = subprocess.run(cmd_combinar, capture_output=True, text=True)

if result.returncode == 0:
    print(f"\n✅ ARCHIVO FINAL CREADO EXITOSAMENTE!")
    
    # Verificar el archivo final
    if os.path.exists(output_final):
        tamano_final = os.path.getsize(output_final)
        
        # Obtener duración total
        try:
            cmd_duration = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                output_final
            ]
            duration_result = subprocess.run(cmd_duration, capture_output=True, text=True)
            if duration_result.returncode == 0:
                duracion_total = float(duration_result.stdout.strip())
                print(f"\n📊 INFORMACIÓN DEL ARCHIVO FINAL:")
                print(f"   📁 Nombre: {output_final}")
                print(f"   📊 Tamaño: {tamano_final:,} bytes ({tamano_final/1024/1024:.2f} MB)")
                print(f"   ⏱️  Duración: {duracion_total:.2f} segundos")
                print(f"   📍 Ruta: {os.path.abspath(output_final)}")
                
                # Mostrar estructura del archivo
                print(f"\n🎵 ESTRUCTURA DEL ARCHIVO:")
                num_grupos = len([a for a in archivos_validos if "grupo" in a])
                num_tonos = len([a for a in archivos_validos if "tono" in a])
                
                print(f"   • {num_grupos} segmentos de diálogo")
                print(f"   • {num_tonos} tonos de separación")
                print(f"   • Total: {len(archivos_validos)} segmentos combinados")
                
                # Mostrar secuencia aproximada
                print(f"\n   SECUENCIA APROXIMADA:")
                for i, archivo in enumerate(archivos_validos[:10]):  # Mostrar primeros 10
                    if "grupo" in archivo:
                        print(f"     {i+1}. [DIÁLOGO] Grupo {i//2+1}")
                    else:
                        print(f"     {i+1}. [TONO] Separación ({DURACION_TONO}s)")
                if len(archivos_validos) > 10:
                    print(f"     ... y {len(archivos_validos)-10} segmentos más")
        except:
            print(f"\n✅ Archivo creado: {output_final} ({tamano_final:,} bytes)")
    else:
        print(f"\n⚠️  El archivo no se creó o no se puede encontrar")
else:
    print(f"\n❌ Error al combinar archivos")
    print(f"   Error: {result.stderr[:200]}")

# Limpiar archivo de lista
if os.path.exists(lista_file):
    os.remove(lista_file)

print(f"\n{'='*60}")
print("🎉 PROCESO COMPLETADO")
print(f"{'='*60}")

# Instrucciones para verificar
print(f"\n🔍 PARA VERIFICAR QUE LOS TONOS ESTÁN INCLUIDOS:")
print(f"1. Abre el archivo: {output_final}")
print(f"2. Escucha y deberías oír:")
print(f"   • Diálogo del Grupo 1")
print(f"   • Tono de {DURACION_TONO}s")
print(f"   • Diálogo del Grupo 2")
print(f"   • Tono de {DURACION_TONO}s")
print(f"   • ... y así sucesivamente")
print(f"\n3. También puedes verificar con:")
print(f"   ffprobe -i {output_final}")

print(f"\n📁 ARCHIVOS TEMPORALES CREADOS:")
archivos_para_limpiar = archivos_temporales.copy()
if tono_separador and tono_separador not in archivos_para_limpiar:
    archivos_para_limpiar.append(tono_separador)

for archivo in archivos_para_limpiar:
    if os.path.exists(archivo):
        tamano = os.path.getsize(archivo)
        print(f"   • {archivo} ({tamano:,} bytes)")
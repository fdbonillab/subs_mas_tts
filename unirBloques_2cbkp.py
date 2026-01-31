import pysrt
import subprocess
import os
import random
from datetime import datetime


# Configuración
video = 'The.Matrix.1999.mp4'
subs = pysrt.open('The Matrix (1999)-en.srt')
# Configuración de TTS (Text-to-Speech)
TTS_ENGINE = "win"  # "edge" (Microsoft Edge TTS) o "win" (Windows TTS)
TTS_VOICE = "en-US-AriaNeural"  # Voz para Edge TTS
TTS_RATE = "+0%"  # Velocidad del habla
TTS_VOLUME = "+0%"  # Volumen

# Configuración de mezcla de audio
VOLUMEN_AUDIO_ORIGINAL = 1 ## 0.3  # 30% volumen para audio original
VOLUMEN_TTS = 1.0  # 100% volumen para TTS

# ==============================================
# FUNCIONES DE TEXTO A VOZ (TTS)
# ==============================================

def tts_con_edge(texto, archivo_salida, voz=TTS_VOICE, rate=TTS_RATE):
    """
    Convierte texto a audio usando Microsoft Edge TTS (gratuito, buena calidad)
    Requiere: pip install edge-tts
    """
    try:
        import asyncio
        import edge_tts
        
        async def generar_audio():
            communicate = edge_tts.Communicate(texto, voz)
            await communicate.save(archivo_salida)
        
        # Ejecutar la función asíncrona
        asyncio.run(generar_audio())
        
        if os.path.exists(archivo_salida):
            return True
        else:
            return False
            
    except ImportError:
        print("  ❌ edge-tts no está instalado. Instala con: pip install edge-tts")
        return False
    except Exception as e:
        print(f"  ❌ Error con Edge TTS: {e}")
        return False

def tts_con_windows(texto, archivo_salida):
    """
    Convierte texto a audio usando Windows TTS nativo
    """
    try:
        import comtypes.client
        
        # Crear objeto TTS de Windows
        speaker = comtypes.client.CreateObject("SAPI.SpVoice")
        
        # Configurar salida a archivo
        stream = comtypes.client.CreateObject("SAPI.SpFileStream")
        stream.Open(archivo_salida, 3, False)  # 3 = SSFMCreateForWrite
        speaker.AudioOutputStream = stream
        
        # Hablar texto
        speaker.Speak(texto)
        
        # Cerrar stream
        stream.Close()
        
        return os.path.exists(archivo_salida)
        
    except ImportError:
        print("  ❌ comtypes no está instalado. Instala con: pip install comtypes")
        return False
    except Exception as e:
        print(f"  ❌ Error con Windows TTS: {e}")
        return False

def tts_con_pyttsx3(texto, archivo_salida):
    """
    Alternativa usando pyttsx3 (multiplataforma)
    """
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        
        # Configurar propiedades (opcional)
        engine.setProperty('rate', 150)  # Velocidad
        engine.setProperty('volume', 0.9)  # Volumen
        
        # Guardar en archivo (pyttsx3 no soporta directamente guardar a archivo)
        # Necesitamos un workaround usando sounddevice
        print("  ⚠️  pyttsx3 requiere configuración adicional para guardar en archivo")
        return False
        
    except ImportError:
        print("  ❌ pyttsx3 no está instalado. Instala con: pip install pyttsx3")
        return False

def texto_a_audio(texto, archivo_salida, grupo_id):
    """
    Convierte texto a audio usando el método configurado
    """
    print(f"  🔊 Convirtiendo texto a audio (Grupo {grupo_id})...")
    print(f"  📝 Texto: {texto[:100]}..." if len(texto) > 100 else f"  📝 Texto: {texto}")
    
    # Limpiar texto para TTS (remover caracteres especiales)
    texto_limpio = texto.replace('\n', ' ').replace('  ', ' ').strip()
    
    if not texto_limpio:
        print("  ⚠️  Texto vacío, omitiendo...")
        return False
    
    if TTS_ENGINE == "edge":
        exito = tts_con_edge(texto_limpio, archivo_salida)
    elif TTS_ENGINE == "win":
        exito = tts_con_windows(texto_limpio, archivo_salida)
    elif TTS_ENGINE == "pyttsx3":
        exito = tts_con_pyttsx3(texto_limpio, archivo_salida)
    else:
        print(f"  ❌ Motor TTS desconocido: {TTS_ENGINE}")
        return False
    
    if exito and os.path.exists(archivo_salida):
        tamano = os.path.getsize(archivo_salida)
        print(f"  ✅ Audio TTS creado: {os.path.basename(archivo_salida)} ({tamano:,} bytes)")
        return True
    else:
        print(f"  ❌ No se pudo crear audio TTS")
        return False

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
archivos_tonos = []

MARGEN_FIN_GRUPO = 1.0  # Margen al final de cada grupo (cambiaste de 0.1 a 1)
TIPO_TONO = "beep"  # Opciones: "beep", "click", "silence", "fade"
DURACION_TONO = 1 ###  0.3  # Duración del tono en segundos


# 1. Crear tono de separación
tono_separador = crear_tono_separador(
    tipo=TIPO_TONO, 
    duracion=DURACION_TONO,
    frecuencia=800
)
if tono_separador:
    archivos_tonos.append(tono_separador)
    print(f"✅ Tono de separación creado: {tono_separador} ({TIPO_TONO}, {DURACION_TONO}s)")

print(f"Extrayendo diálogos agrupando bloques cercanos...\n")
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
for idx_grupo, grupo in enumerate(grupos[:5]):  # Solo primeros 5 grupos para prueba
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
    texto_para_tts = ""
    for subtitle in subs[primer_idx:ultimo_idx + 1]:
        texto_para_tts += subtitle.text + " "
    ### let texto_para_tts = subs[primer_idx] + subs[primer_idx+1]
    archivo_salida = "tts_"+str(primer_idx)+".mp3"
    print(" archivo_salida tts "+archivo_salida)
    tts_audio =  texto_a_audio(texto_para_tts, archivo_salida, primer_idx)
    ####  primero el tts
    if idx_grupo < len(grupos[:50]) - 1 and tts_audio:
        archivos_temporales.append(archivo_salida)
    # Añadir tono de separación (excepto después del último grupo)
    if idx_grupo < len(grupos[:50]) - 1 and tono_separador:
        archivos_temporales.append(tono_separador)
    ##### para q se escuche primero  el tts
    archivos_temporales.append(output_file)
    
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
    
    '''cmd_combinar = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_file,
        '-c', 'copy',  # Copiar sin re-codificar
        '-y',
        output_final
    ]'''
    cmd_combinar = [
    'ffmpeg',
    '-f', 'concat',
    '-safe', '0',
    '-i', lista_file,
    '-c:a', 'libmp3lame',  # <-- Especifica codec MP3
    '-q:a', '2',           # <-- Calidad de MP3 (0-9, 0=mejor)
    '-ar', '44100',        # <-- Sample rate uniforme
    '-ac', '2',            # <-- Canales uniformes (estéreo)
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
    #if os.path.exists(lista_file):
    #    os.remove(lista_file)

print("\n🎧 Archivos generados:")
print(f"  {output_final} (combinado)")
for i, archivo in enumerate(archivos_temporales[:5]):
    if os.path.exists(archivo):
        size_kb = os.path.getsize(archivo) / 1024
        print(f"  {archivo} ({size_kb:.1f} KB)")
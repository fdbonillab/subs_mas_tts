import pysrt
import subprocess
import os
import time
import json
from datetime import datetime

# ==============================================
# CONFIGURACIÓN
# ==============================================

# Archivos de entrada
VIDEO_FILE = 'The.Matrix.1999.mp4'
SRT_FILE = 'The Matrix (1999)-en.srt'

# Configuración de audio
AUDIO_SAMPLE_RATE = 44100  # Hz - TODOS los audios usarán esta tasa
AUDIO_CHANNELS = 2  # Estéreo
AUDIO_FORMAT = 'mp3'
AUDIO_CODEC = 'libmp3lame'
AUDIO_QUALITY = '2'  # Calidad alta

# Configuración de grupos
MAX_ESPACIO_ENTRE_BLOQUES = 2.0
MARGEN_FIN_GRUPO = 1.0

# Configuración de TTS
TTS_ENGINE = "edge"
TTS_VOICE = "en-US-AriaNeural"
TTS_RATE = "+0%"  # Velocidad normal
TTS_PITCH = "+0Hz"  # Tono normal

# Configuración de mezcla
VOLUMEN_AUDIO_ORIGINAL = 0.3
VOLUMEN_TTS = 1.0
SILENCIO_ENTRE_AUDIOS = 1.0  # 1 segundo de silencio

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================

def segundos_a_str(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milisegundos = int((segundos - int(segundos)) * 1000)
    return f"{horas:02}:{minutos:02}:{segs:02}.{milisegundos:03}"

def ejecutar_comando(comando, descripcion=""):
    if descripcion:
        print(f"  {descripcion}...")
    
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if resultado.returncode != 0:
            print(f"  ❌ Error: {resultado.stderr[:200]}")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Excepción: {e}")
        return False

def normalizar_audio(archivo_entrada, archivo_salida):
    """
    Normaliza un archivo de audio a formato estándar
    Esto evita problemas de sample rate y canales diferentes
    """
    print(f"  🔧 Normalizando audio...")
    
    comando = [
        'ffmpeg',
        '-i', archivo_entrada,
        '-ar', str(AUDIO_SAMPLE_RATE),  # Fuerza sample rate
        '-ac', str(AUDIO_CHANNELS),     # Fuerza canales
        '-c:a', AUDIO_CODEC,
        '-q:a', AUDIO_QUALITY,
        '-y',
        archivo_salida
    ]
    
    if ejecutar_comando(comando, "Normalizando formato"):
        if os.path.exists(archivo_salida):
            return True
    return False

def crear_silencio(duracion, archivo_salida):
    """Crea silencio con formato normalizado"""
    print(f"  🔇 Creando {duracion}s de silencio...")
    
    comando = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'anullsrc=channel_layout=stereo:sample_rate={AUDIO_SAMPLE_RATE}',
        '-t', str(duracion),
        '-c:a', AUDIO_CODEC,
        '-q:a', AUDIO_QUALITY,
        '-y',
        archivo_salida
    ]
    
    if ejecutar_comando(comando, "Creando silencio"):
        if os.path.exists(archivo_salida):
            return True
    return False

def obtener_info_audio(archivo_audio):
    """Obtiene información detallada del audio"""
    try:
        comando = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            archivo_audio
        ]
        
        resultado = subprocess.run(comando, capture_output=True, text=True)
        if resultado.returncode == 0:
            return json.loads(resultado.stdout)
    except:
        pass
    return None

def verificar_formato_audio(archivo_audio):
    """Verifica y muestra información del formato de audio"""
    info = obtener_info_audio(archivo_audio)
    if info and 'streams' in info and len(info['streams']) > 0:
        stream = info['streams'][0]
        print(f"    📊 Sample rate: {stream.get('sample_rate', 'N/A')} Hz")
        print(f"    📊 Canales: {stream.get('channels', 'N/A')}")
        print(f"    📊 Codec: {stream.get('codec_name', 'N/A')}")
        return True
    return False

# ==============================================
# FUNCIONES DE TEXTO A VOZ (TTS)
# ==============================================

def tts_con_edge_normalizado(texto, archivo_salida, voz=TTS_VOICE):
    """
    Genera TTS y lo convierte inmediatamente al formato estándar
    """
    try:
        import asyncio
        import edge_tts
        
        # Primero generar con Edge TTS
        archivo_temp = archivo_salida.replace('.mp3', '_temp.mp3')
        
        async def generar_audio():
            communicate = edge_tts.Communicate(texto, voz)
            await communicate.save(archivo_temp)
        
        print(f"  🗣️  Generando TTS con Edge...")
        asyncio.run(generar_audio())
        
        if not os.path.exists(archivo_temp):
            print(f"  ❌ Edge TTS no generó archivo")
            return False
        
        # Verificar formato original
        print(f"  🔍 Verificando formato TTS original...")
        info = obtener_info_audio(archivo_temp)
        if info:
            stream = info['streams'][0]
            print(f"    Original: {stream.get('sample_rate', '?')}Hz, "
                  f"{stream.get('channels', '?')} canales")
        
        # Normalizar al formato estándar
        print(f"  🔄 Normalizando TTS a formato estándar...")
        if normalizar_audio(archivo_temp, archivo_salida):
            # Limpiar temporal
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)
            
            # Verificar formato final
            print(f"  ✅ TTS normalizado correctamente")
            verificar_formato_audio(archivo_salida)
            return True
        else:
            print(f"  ❌ Error normalizando TTS")
            return False
            
    except ImportError:
        print("  ❌ edge-tts no instalado: pip install edge-tts")
        return False
    except Exception as e:
        print(f"  ❌ Error Edge TTS: {e}")
        return False

# ==============================================
# FUNCIONES DE PROCESAMIENTO DE AUDIO
# ==============================================

def extraer_audio_original_normalizado(inicio, fin, archivo_salida, grupo_id):
    """Extrae audio y lo normaliza inmediatamente"""
    print(f"  🎬 Extrayendo audio original (Grupo {grupo_id})...")
    
    inicio_str = segundos_a_str(inicio)
    fin_str = segundos_a_str(fin)
    
    archivo_temp = archivo_salida.replace('.mp3', '_temp.mp3')
    
    # Primero extraer
    comando_extraer = [
        'ffmpeg',
        '-i', VIDEO_FILE,
        '-ss', inicio_str,
        '-to', fin_str,
        '-q:a', AUDIO_QUALITY,
        '-map', '0:a',
        '-y',
        archivo_temp
    ]
    
    if not ejecutar_comando(comando_extraer, "Extrayendo audio"):
        return False
    
    # Luego normalizar
    if normalizar_audio(archivo_temp, archivo_salida):
        # Limpiar temporal
        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)
        
        # Verificar formato
        print(f"  ✅ Audio original normalizado")
        verificar_formato_audio(archivo_salida)
        return True
    
    return False

def crear_secuencia_intercalada(audio_original, audio_tts, archivo_salida, 
                               silencio_duracion=1.0):
    """
    Crea secuencia: [ORIGINAL] + [SILENCIO] + [TTS]
    Asegurando que todos tengan el mismo formato
    """
    print(f"  🔗 Creando secuencia intercalada...")
    
    # Crear silencio normalizado
    archivo_silencio = "temp_silencio_normalizado.mp3"
    if not crear_silencio(silencio_duracion, archivo_silencio):
        print(f"  ⚠️  Error creando silencio")
        return False
    
    # Verificar que todos los archivos existen
    archivos = [audio_original, archivo_silencio, audio_tts]
    for archivo in archivos:
        if not os.path.exists(archivo):
            print(f"  ❌ Archivo no existe: {archivo}")
            return False
    
    # Verificar formatos (debug)
    print(f"  🔍 Verificando formatos...")
    for i, archivo in enumerate(['Original', 'Silencio', 'TTS']):
        info = obtener_info_audio(archivos[i])
        if info and 'streams' in info:
            stream = info['streams'][0]
            print(f"    {archivo}: {stream.get('sample_rate', '?')}Hz, "
                  f"{stream.get('channels', '?')} canales")
    
    # Crear archivo de lista para concatenación
    lista_file = "temp_lista_concat.txt"
    with open(lista_file, 'w', encoding='utf-8') as f:
        for archivo in archivos:
            ruta_abs = os.path.abspath(archivo).replace('\\', '/')
            f.write(f"file '{ruta_abs}'\n")
    
    # CONCATENAR con re-encoding para asegurar compatibilidad
    print(f"  🔄 Concatenando con formato consistente...")
    
    comando = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_file,
        '-c:a', AUDIO_CODEC,
        '-ar', str(AUDIO_SAMPLE_RATE),
        '-ac', str(AUDIO_CHANNELS),
        '-q:a', AUDIO_QUALITY,
        '-y',
        archivo_salida
    ]
    
    exito = ejecutar_comando(comando, "Concatenando secuencia")
    
    # Limpiar temporales
    if os.path.exists(lista_file):
        os.remove(lista_file)
    if os.path.exists(archivo_silencio):
        os.remove(archivo_silencio)
    
    if exito and os.path.exists(archivo_salida):
        # Verificar resultado
        info_final = obtener_info_audio(archivo_salida)
        if info_final:
            stream = info_final['streams'][0]
            print(f"  ✅ Secuencia creada: {stream.get('sample_rate', '?')}Hz, "
                  f"{stream.get('channels', '?')} canales")
        
        # Obtener duraciones
        duracion_final = obtener_duracion_audio(archivo_salida)
        if duracion_final > 0:
            print(f"  ⏱️  Duración total: {duracion_final:.2f}s")
        
        return True
    
    return False

def obtener_duracion_audio(archivo_audio):
    """Obtiene duración en segundos"""
    try:
        comando = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            archivo_audio
        ]
        
        resultado = subprocess.run(comando, capture_output=True, text=True)
        if resultado.returncode == 0:
            datos = json.loads(resultado.stdout)
            return float(datos['format']['duration'])
    except:
        pass
    return 0

# ==============================================
# FUNCIÓN PRINCIPAL MEJORADA
# ==============================================

def main():
    print("=" * 70)
    print("🎬 SRT A AUDIO - VERSIÓN CORREGIDA (FORMATO NORMALIZADO)")
    print("=" * 70)
    print(f"Video: {VIDEO_FILE}")
    print(f"Subtítulos: {SRT_FILE}")
    print(f"Formato audio: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_CHANNELS} canales")
    print(f"Silencio entre audios: {SILENCIO_ENTRE_AUDIOS}s")
    print("=" * 70)
    
    # Verificar ffmpeg
    print("\n🔍 Verificando sistema...")
    if not ejecutar_comando(['ffmpeg', '-version'], "FFmpeg"):
        return
    
    # Verificar archivos
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Video no encontrado: {VIDEO_FILE}")
        return
    
    if not os.path.exists(SRT_FILE):
        print(f"❌ SRT no encontrado: {SRT_FILE}")
        return
    
    # Cargar subtítulos
    print(f"\n📖 Cargando subtítulos...")
    try:
        subs = pysrt.open(SRT_FILE)
        print(f"✅ {len(subs)} subtítulos cargados")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Agrupar subtítulos
    print(f"\n1️⃣  AGRUPANDO SUBTÍTULOS...")
    grupos = []
    grupo_actual = []
    
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
    
    print(f"✅ {len(grupos)} grupos creados")
    
    # Limitar para prueba
    GRUPOS_A_PROCESAR = 3
    grupos = grupos[:GRUPOS_A_PROCESAR]
    print(f"🔧 Procesando {len(grupos)} grupos")
    
    # Directorio temporal
    temp_dir = "audio_temp_normalizado"
    os.makedirs(temp_dir, exist_ok=True)
    
    archivos_finales = []
    
    # 2. PROCESAR CADA GRUPO
    print(f"\n2️⃣  PROCESANDO GRUPOS...")
    
    for idx_grupo, grupo in enumerate(grupos):
        print(f"\n{'─' * 60}")
        print(f"🎯 GRUPO {idx_grupo + 1}/{len(grupos)}")
        print(f"{'─' * 60}")
        
        if len(grupo) == 0:
            continue
        
        # Información del grupo
        primer_idx = grupo[0]
        ultimo_idx = grupo[-1]
        
        sub_inicio = subs[primer_idx]
        sub_fin = subs[ultimo_idx]
        
        inicio_grupo = sub_inicio.start.ordinal / 1000.0
        fin_grupo = sub_fin.end.ordinal / 1000.0
        
        inicio_grupo = max(0, inicio_grupo - 0.1)
        fin_grupo = fin_grupo + MARGEN_FIN_GRUPO
        
        print(f"📊 Información:")
        print(f"  • Subtítulos: {len(grupo)}")
        print(f"  • Tiempo: {segundos_a_str(inicio_grupo)} → {segundos_a_str(fin_grupo)}")
        
        # Extraer texto
        textos_grupo = []
        for sub_idx in grupo:
            sub = subs[sub_idx]
            textos_grupo.append(sub.text)
        
        texto_completo = " ".join(textos_grupo)
        
        # Nombres de archivos
        base_nombre = f"grupo_{idx_grupo + 1:03d}"
        
        archivo_original = os.path.join(temp_dir, f"{base_nombre}_original_norm.mp3")
        archivo_tts = os.path.join(temp_dir, f"{base_nombre}_tts_norm.mp3")
        archivo_secuencia = os.path.join(temp_dir, f"{base_nombre}_secuencia.mp3")
        
        # 2.1 Extraer y normalizar audio original
        print(f"\n🎬 Extrayendo audio original...")
        if extraer_audio_original_normalizado(inicio_grupo, fin_grupo, archivo_original, idx_grupo + 1):
            print(f"  ✅ Audio original listo")
        else:
            print(f"  ⚠️  Creando silencio como fallback")
            duracion = fin_grupo - inicio_grupo
            crear_silencio(duracion, archivo_original)
        
        # 2.2 Generar TTS normalizado
        print(f"\n🗣️  Generando TTS normalizado...")
        if tts_con_edge_normalizado(texto_completo, archivo_tts):
            print(f"  ✅ TTS normalizado listo")
        else:
            print(f"  ⚠️  TTS falló, texto simple")
            texto_simple = f"Diálogo del grupo {idx_grupo + 1}"
            tts_con_edge_normalizado(texto_simple, archivo_tts)
        
        # 2.3 Crear secuencia intercalada
        print(f"\n🔊 Creando secuencia intercalada...")
        if crear_secuencia_intercalada(
            archivo_original, 
            archivo_tts, 
            archivo_secuencia,
            SILENCIO_ENTRE_AUDIOS
        ):
            archivos_finales.append(archivo_secuencia)
            print(f"  ✅ Secuencia creada exitosamente")
        else:
            print(f"  ❌ Error en secuencia, usando solo TTS")
            if os.path.exists(archivo_tts):
                archivos_finales.append(archivo_tts)
        
        # Pausa breve
        if idx_grupo < len(grupos) - 1:
            time.sleep(0.5)
    
    # 3. COMBINAR SECUENCIAS
    print(f"\n{'=' * 70}")
    print("3️⃣  COMBINANDO SECUENCIAS")
    print(f"{'=' * 70}")
    
    if not archivos_finales:
        print("❌ No hay secuencias para combinar")
        return
    
    print(f"📋 Combinando {len(archivos_finales)} secuencias...")
    
    # Verificar que todas las secuencias existen
    secuencias_validas = []
    for archivo in archivos_finales:
        if os.path.exists(archivo):
            secuencias_validas.append(archivo)
            print(f"  ✅ {os.path.basename(archivo)}")
        else:
            print(f"  ❌ {archivo} (no existe)")
    
    if not secuencias_validas:
        print("❌ No hay secuencias válidas")
        return
    
    # Crear lista
    lista_file = os.path.join(temp_dir, "lista_final.txt")
    with open(lista_file, 'w', encoding='utf-8') as f:
        for archivo in secuencias_validas:
            ruta_abs = os.path.abspath(archivo).replace('\\', '/')
            f.write(f"file '{ruta_abs}'\n")
    
    # Archivo final
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_final = f"pelicula_intercalada_{timestamp}.mp3"
    
    print(f"\n🔗 Creando archivo final: {archivo_final}")
    
    # IMPORTANTE: Re-encode al combinar para consistencia
    comando_final = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_file,
        '-c:a', AUDIO_CODEC,
        '-ar', str(AUDIO_SAMPLE_RATE),
        '-ac', str(AUDIO_CHANNELS),
        '-q:a', AUDIO_QUALITY,
        '-y',
        archivo_final
    ]
    
    if ejecutar_comando(comando_final, "Creando archivo final"):
        if os.path.exists(archivo_final):
            tamano = os.path.getsize(archivo_final)
            duracion = obtener_duracion_audio(archivo_final)
            
            # Verificar formato final
            info_final = obtener_info_audio(archivo_final)
            
            print(f"\n{'🎉' * 20}")
            print("¡PROCESO COMPLETADO!")
            print(f"{'🎉' * 20}")
            
            print(f"\n📁 ARCHIVO FINAL:")
            print(f"  • Nombre: {archivo_final}")
            print(f"  • Tamaño: {tamano:,} bytes")
            print(f"  • Duración: {duracion:.2f} segundos")
            
            if info_final and 'streams' in info_final:
                stream = info_final['streams'][0]
                print(f"  • Formato: {stream.get('sample_rate', '?')}Hz, "
                      f"{stream.get('channels', '?')} canales")
            
            print(f"\n🔊 ESTRUCTURA (por grupo):")
            print(f"  1. Audio original de película")
            print(f"  2. {SILENCIO_ENTRE_AUDIOS}s de silencio")
            print(f"  3. TTS leyendo subtítulos")
            
            print(f"\n🎧 PARA PROBAR:")
            print(f"  Abre '{archivo_final}' y verifica que:")
            print(f"  • No hay rallentizado")
            print(f"  • Los audios están intercalados correctamente")
            print(f"  • El TTS suena a velocidad normal")
    
    # Limpiar lista
    if os.path.exists(lista_file):
        os.remove(lista_file)
    
    # 4. TEST RÁPIDO
    print(f"\n{'=' * 70}")
    print("4️⃣  TEST DE VERIFICACIÓN")
    print(f"{'=' * 70}")
    
    if os.path.exists(archivo_final):
        print("🧪 Realizando test rápido...")
        
        # Test 1: Verificar duración
        duracion = obtener_duracion_audio(archivo_final)
        print(f"  ✅ Duración: {duracion:.2f}s")
        
        # Test 2: Verificar formato
        info = obtener_info_audio(archivo_final)
        if info and 'streams' in info:
            stream = info['streams'][0]
            sr = stream.get('sample_rate', '0')
            if sr == str(AUDIO_SAMPLE_RATE):
                print(f"  ✅ Sample rate correcto: {sr}Hz")
            else:
                print(f"  ⚠️  Sample rate diferente: {sr}Hz (esperado: {AUDIO_SAMPLE_RATE}Hz)")
        
        # Test 3: Reproducir un fragmento (opcional)
        respuesta = input("\n¿Reproducir 10 segundos para verificar? (s/n): ")
        if respuesta.lower() == 's':
            test_file = "test_verificacion.mp3"
            comando_test = [
                'ffmpeg',
                '-i', archivo_final,
                '-t', '10',
                '-c', 'copy',
                '-y',
                test_file
            ]
            
            if ejecutar_comando(comando_test, "Extrayendo 10s para test"):
                print("🔊 Reproduciendo test...")
                if os.name == 'nt':
                    os.startfile(test_file)
                print("  Escucha si hay problemas de velocidad o intercalado")
    
    # 5. LIMPIEZA
    print(f"\n{'=' * 70}")
    print("5️⃣  LIMPIEZA")
    print(f"{'=' * 70}")
    
    respuesta = input("¿Eliminar archivos temporales? (s/n): ")
    if respuesta.lower() == 's':
        eliminados = 0
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                    eliminados += 1
                except:
                    pass
        
        try:
            os.rmdir(temp_dir)
        except:
            pass
        
        print(f"✅ {eliminados} archivos eliminados")
    
    print(f"\n{'=' * 70}")
    print("✨ PROCESO TERMINADO - VERIFICA EL AUDIO FINAL")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    print("🎬 CONVERSOR SRT A AUDIO - VERSIÓN CORREGIDA")
    print("=" * 70)
    print("Este código normaliza todos los audios al mismo formato")
    print("para evitar problemas de velocidad e intercalado.")
    print("=" * 70)
    
    # Instalar dependencias si es necesario
    try:
        import edge_tts
        print("✅ edge-tts está instalado")
    except ImportError:
        print("❌ edge-tts no está instalado")
        respuesta = input("¿Instalar edge-tts? (s/n): ")
        if respuesta.lower() == 's':
            subprocess.run(['pip', 'install', 'edge-tts'], capture_output=True)
            print("✅ edge-tts instalado")
    
    main()
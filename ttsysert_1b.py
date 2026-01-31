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

# Configuración de grupos
MAX_ESPACIO_ENTRE_BLOQUES = 2.0  # segundos entre subtítulos para agrupar
MARGEN_FIN_GRUPO = 1.0  # segundos de margen al final de cada grupo

# Configuración de TTS (Text-to-Speech)
TTS_ENGINE = "edge"  # "edge" (Microsoft Edge TTS) o "win" (Windows TTS)
TTS_VOICE = "en-US-AriaNeural"  # Voz para Edge TTS
TTS_RATE = "+0%"  # Velocidad del habla
TTS_VOLUME = "+0%"  # Volumen

# Configuración de mezcla de audio
VOLUMEN_AUDIO_ORIGINAL = 1 ## 0.3  # 30% volumen para audio original
VOLUMEN_TTS = 1.0  # 100% volumen para TTS

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================

def segundos_a_str(segundos):
    """Convierte segundos a formato HH:MM:SS.ms"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milisegundos = int((segundos - int(segundos)) * 1000)
    return f"{horas:02}:{minutos:02}:{segs:02}.{milisegundos:03}"

def ejecutar_comando(comando, descripcion=""):
    """Ejecuta un comando y maneja errores"""
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

# ==============================================
# FUNCIONES DE PROCESAMIENTO DE AUDIO
# ==============================================

def extraer_audio_original(inicio, fin, archivo_salida, grupo_id):
    """
    Extrae audio original de la película
    """
    print(f"  🎬 Extrayendo audio original (Grupo {grupo_id})...")
    print(f"  ⏱️  Tiempo: {inicio} → {fin}")
    
    inicio_str = segundos_a_str(inicio)
    fin_str = segundos_a_str(fin)
    
    comando = [
        'ffmpeg',
        '-i', VIDEO_FILE,
        '-ss', inicio_str,
        '-to', fin_str,
        '-q:a', '2',  # Calidad alta
        '-map', '0:a',
        '-y',
        archivo_salida
    ]
    
    if ejecutar_comando(comando, "Extrayendo audio"):
        if os.path.exists(archivo_salida):
            tamano = os.path.getsize(archivo_salida)
            print(f"  ✅ Audio original extraído: {tamano:,} bytes")
            return True
    
    return False

def mezclar_audios(audio1, audio2, archivo_salida, volumen1=1.0, volumen2=1.0):
    """
    Mezcla dos archivos de audio
    """
    print(f"  🔊 Mezclando audios...")
    
    # Primero, normalizar ambos audios a la misma duración (la más larga)
    # Obtener duración de ambos audios
    duracion1 = obtener_duracion_audio(audio1)
    duracion2 = obtener_duracion_audio(audio2)
    
    duracion_max = max(duracion1, duracion2)
    
    # Comando para mezclar con ffmpeg
    comando = [
        'ffmpeg',
        '-i', audio1,
        '-i', audio2,
        '-filter_complex', 
        f'[0:a]volume={volumen1}[a1];[1:a]volume={volumen2}[a2];[a1][a2]amix=inputs=2:duration=longest',
        '-c:a', 'libmp3lame',
        '-q:a', '2',
        '-y',
        archivo_salida
    ]
    
    if ejecutar_comando(comando, "Mezclando audios"):
        if os.path.exists(archivo_salida):
            tamano = os.path.getsize(archivo_salida)
            print(f"  ✅ Audio mezclado creado: {tamano:,} bytes")
            return True
    
    return False

def obtener_duracion_audio(archivo_audio):
    """Obtiene la duración de un archivo de audio en segundos"""
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
# FUNCIÓN PRINCIPAL
# ==============================================

def main():
    print("=" * 70)
    print("🎬 SRT A AUDIO CON MEZCLA DE AUDIO ORIGINAL")
    print("=" * 70)
    print(f"Video: {VIDEO_FILE}")
    print(f"Subtítulos: {SRT_FILE}")
    print(f"Motor TTS: {TTS_ENGINE}")
    print("=" * 70)
    
    # Verificar dependencias
    print("\n🔍 Verificando dependencias...")
    
    # Verificar ffmpeg
    if not ejecutar_comando(['ffmpeg', '-version'], "Verificando ffmpeg"):
        print("❌ ffmpeg no encontrado. Es requerido.")
        return
    
    # Verificar archivos
    if not os.path.exists(VIDEO_FILE):
        print(f"❌ Video no encontrado: {VIDEO_FILE}")
        return
    
    if not os.path.exists(SRT_FILE):
        print(f"❌ Archivo SRT no encontrado: {SRT_FILE}")
        return
    
    # Cargar subtítulos
    print(f"\n📖 Cargando subtítulos...")
    try:
        subs = pysrt.open(SRT_FILE)
        print(f"✅ {len(subs)} subtítulos cargados")
    except Exception as e:
        print(f"❌ Error cargando SRT: {e}")
        return
    
    # 1. AGRUPAR SUBTÍTULOS
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
    
    print(f"✅ {len(grupos)} grupos creados (max {MAX_ESPACIO_ENTRE_BLOQUES}s entre bloques)")
    
    # Limitar a primeros N grupos para prueba
    GRUPOS_A_PROCESAR = 3  # Cambia esto para procesar más grupos
    grupos = grupos[:GRUPOS_A_PROCESAR]
    print(f"🔧 Procesando {len(grupos)} grupos para prueba")
    
    # Directorio para archivos temporales
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    
    archivos_finales = []
    estadisticas = {
        'grupos_procesados': 0,
        'tts_exitosos': 0,
        'extracciones_exitosas': 0,
        'mezclas_exitosas': 0
    }
    
    # 2. PROCESAR CADA GRUPO
    print(f"\n2️⃣  PROCESANDO GRUPOS...")
    
    for idx_grupo, grupo in enumerate(grupos):
        print(f"\n{'─' * 60}")
        print(f"🎯 GRUPO {idx_grupo + 1}/{len(grupos)}")
        print(f"{'─' * 60}")
        
        if len(grupo) == 0:
            continue
        
        # Obtener información del grupo
        primer_idx = grupo[0]
        ultimo_idx = grupo[-1]
        
        sub_inicio = subs[primer_idx]
        sub_fin = subs[ultimo_idx]
        
        # Calcular tiempos
        inicio_grupo = sub_inicio.start.ordinal / 1000.0
        fin_grupo = sub_fin.end.ordinal / 1000.0
        
        inicio_grupo = max(0, inicio_grupo - 0.1)
        fin_grupo = fin_grupo + MARGEN_FIN_GRUPO
        
        duracion_grupo = fin_grupo - inicio_grupo
        
        print(f"📊 Información:")
        print(f"  • Subtítulos: {len(grupo)}")
        print(f"  • Tiempo: {segundos_a_str(inicio_grupo)} → {segundos_a_str(fin_grupo)}")
        print(f"  • Duración: {duracion_grupo:.2f}s")
        
        # Extraer texto de todos los subtítulos del grupo
        textos_grupo = []
        for sub_idx in grupo:
            sub = subs[sub_idx]
            textos_grupo.append(sub.text)
        
        texto_completo = " ".join(textos_grupo)
        
        # Crear nombres de archivos
        base_nombre = f"grupo_{idx_grupo + 1:03d}"
        
        archivo_audio_original = os.path.join(temp_dir, f"{base_nombre}_original.mp3")
        archivo_tts = os.path.join(temp_dir, f"{base_nombre}_tts.mp3")
        archivo_mezclado = os.path.join(temp_dir, f"{base_nombre}_mezclado.mp3")
        
        # 2.1 Extraer audio original
        print(f"\n🎬 Extrayendo audio original...")
        if extraer_audio_original(inicio_grupo, fin_grupo, archivo_audio_original, idx_grupo + 1):
            estadisticas['extracciones_exitosas'] += 1
        else:
            print(f"  ⚠️  Continuando sin audio original")
            # Crear archivo de silencio como fallback
            crear_silencio(duracion_grupo, archivo_audio_original)
        
        # 2.2 Generar audio TTS
        print(f"\n🗣️  Generando audio TTS...")
        if texto_a_audio(texto_completo, archivo_tts, idx_grupo + 1):
            estadisticas['tts_exitosos'] += 1
        else:
            print(f"  ⚠️  No se pudo generar TTS, usando texto alternativo")
            texto_alternativo = f"Grupo {idx_grupo + 1}"
            texto_a_audio(texto_alternativo, archivo_tts, idx_grupo + 1)
        
        # 2.3 Mezclar ambos audios
        print(f"\n🔊 Mezclando audio original con TTS...")
        if mezclar_audios(
            archivo_audio_original, 
            archivo_tts, 
            archivo_mezclado,
            VOLUMEN_AUDIO_ORIGINAL,
            VOLUMEN_TTS
        ):
            archivos_finales.append(archivo_mezclado)
            estadisticas['mezclas_exitosas'] += 1
            print(f"  ✅ Grupo {idx_grupo + 1} procesado exitosamente")
        else:
            print(f"  ⚠️  Usando solo TTS (falló la mezcla)")
            archivos_finales.append(archivo_tts)
        
        estadisticas['grupos_procesados'] += 1
        
        # Pequeña pausa entre grupos para no sobrecargar
        if idx_grupo < len(grupos) - 1:
            time.sleep(1)
    
    # 3. COMBINAR TODOS LOS GRUPOS
    print(f"\n{'=' * 70}")
    print("3️⃣  COMBINANDO TODOS LOS GRUPOS")
    print(f"{'=' * 70}")
    
    if not archivos_finales:
        print("❌ No hay archivos para combinar")
        return
    
    print(f"📋 Combinando {len(archivos_finales)} archivos...")
    
    # Crear archivo de lista para ffmpeg
    lista_file = os.path.join(temp_dir, "lista_combinar.txt")
    with open(lista_file, 'w', encoding='utf-8') as f:
        for archivo in archivos_finales:
            if os.path.exists(archivo):
                # Usar rutas absolutas
                ruta_abs = os.path.abspath(archivo).replace('\\', '/')
                f.write(f"file '{ruta_abs}'\n")
    
    # Archivo final
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_final = f"pelicula_con_tts_{timestamp}.mp3"
    
    print(f"🔗 Creando archivo final: {archivo_final}")
    
    comando_combinar = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_file,
        '-c', 'copy',
        '-y',
        archivo_final
    ]
    
    if ejecutar_comando(comando_combinar, "Combinando archivos"):
        if os.path.exists(archivo_final):
            tamano = os.path.getsize(archivo_final)
            duracion = obtener_duracion_audio(archivo_final)
            
            print(f"\n{'🎉' * 20}")
            print("¡PROCESO COMPLETADO EXITOSAMENTE!")
            print(f"{'🎉' * 20}")
            
            print(f"\n📊 ESTADÍSTICAS:")
            print(f"  • Grupos procesados: {estadisticas['grupos_procesados']}")
            print(f"  • TTS exitosos: {estadisticas['tts_exitosos']}")
            print(f"  • Extracciones exitosas: {estadisticas['extracciones_exitosas']}")
            print(f"  • Mezclas exitosas: {estadisticas['mezclas_exitosas']}")
            
            print(f"\n📁 ARCHIVO FINAL:")
            print(f"  • Nombre: {archivo_final}")
            print(f"  • Tamaño: {tamano:,} bytes ({tamano/1024/1024:.2f} MB)")
            print(f"  • Duración: {duracion:.2f} segundos")
            print(f"  • Ruta: {os.path.abspath(archivo_final)}")
            
            print(f"\n🔊 CONTENIDO:")
            print("  El archivo contiene para cada grupo:")
            print("  1. Audio original de la película (volumen bajo)")
            print("  2. Voz TTS leyendo los subtítulos (volumen alto)")
            print("  3. Ambos mezclados para mejor comprensión")
            
            print(f"\n🎧 PARA ESCUCHAR:")
            print(f"  Abre '{archivo_final}' con cualquier reproductor de audio")
        else:
            print(f"❌ El archivo final no se creó")
    else:
        print(f"❌ Error al combinar archivos")
    
    # 4. LIMPIEZA (OPCIONAL)
    print(f"\n{'=' * 70}")
    print("4️⃣  LIMPIEZA")
    print(f"{'=' * 70}")
    
    respuesta = input("¿Eliminar archivos temporales? (s/n): ")
    if respuesta.lower() == 's':
        archivos_eliminados = 0
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                    archivos_eliminados += 1
                except:
                    pass
        
        try:
            os.rmdir(temp_dir)
        except:
            pass
        
        print(f"✅ {archivos_eliminados} archivos temporales eliminados")
    else:
        print(f"📁 Archivos temporales guardados en: {temp_dir}")
    
    print(f"\n{'=' * 70}")
    print("✨ PROCESO FINALIZADO")
    print(f"{'=' * 70}")

def crear_silencio(duracion, archivo_salida):
    """Crea un archivo de audio con silencio"""
    comando = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-t', str(duracion),
        '-c:a', 'libmp3lame',
        '-q:a', '2',
        '-y',
        archivo_salida
    ]
    
    subprocess.run(comando, capture_output=True, text=True)

# ==============================================
# INSTALACIÓN DE DEPENDENCIAS
# ==============================================

def instalar_dependencias():
    """Instala las dependencias necesarias"""
    print("📦 Instalando dependencias...")
    
    dependencias = [
        'pysrt',
        'edge-tts',  # Para TTS de Microsoft Edge
        'comtypes',  # Para Windows TTS
    ]
    
    for dep in dependencias:
        print(f"  Instalando {dep}...")
        subprocess.run(['pip', 'install', dep], capture_output=True)
    
    print("✅ Dependencias instaladas")
    print("\n💡 También necesitas ffmpeg instalado en tu sistema PATH")

# ==============================================
# EJECUCIÓN
# ==============================================

if __name__ == "__main__":
    print("=" * 70)
    print("🎬 CONVERSOR SRT A AUDIO CON MEZCLA")
    print("=" * 70)
    print("\nOpciones:")
    print("1. Instalar dependencias")
    print("2. Ejecutar conversión")
    print("3. Salir")
    
    opcion = input("\nSelecciona una opción (1-3): ")
    
    if opcion == "1":
        instalar_dependencias()
    elif opcion == "2":
        main()
    else:
        print("👋 ¡Hasta luego!")
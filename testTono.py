import subprocess
import os
import time

print("🎵 CREANDO UN SOLO MP3 CON TONOS CADA 5 SEGUNDOS")
print("=" * 60)

# Nombre del archivo final
archivo_final = "tonos_con_intervalos.mp3"
archivos_temporales = []

try:
    # 1. Crear tonos individuales
    print("\n1️⃣  CREANDO TONOS INDIVIDUALES:")
    
    for i in range(5):
        frecuencia = 600 + (i * 100)  # 600, 700, 800, 900, 1000 Hz
        archivo_temp = f"tono_temp_{i+1}.mp3"
        archivos_temporales.append(archivo_temp)
        
        print(f"   Tono {i+1}: {frecuencia}Hz...")
        
        comando = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'sine=frequency={frecuencia}:duration=0.5',
            '-ac', '2',
            '-ar', '44100',
            '-codec:a', 'libmp3lame',
            '-qscale:a', '2',
            '-y',
            archivo_temp
        ]
        
        resultado = subprocess.run(comando, 
                                 capture_output=True,
                                 text=True)
        
        if resultado.returncode == 0 and os.path.exists(archivo_temp):
            tamano = os.path.getsize(archivo_temp)
            print(f"     ✓ Creado ({tamano:,} bytes)")
        else:
            print(f"     ✗ Error")
        
        # Crear silencio de 5 segundos (excepto después del último tono)
        if i < 4:
            silencio_temp = f"silencio_{i+1}.mp3"
            archivos_temporales.append(silencio_temp)
            
            print(f"   Silencio {i+1}: 5 segundos...")
            
            comando_silencio = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'anoisesrc=d=5',
                '-ac', '2',
                '-ar', '44100',
                '-codec:a', 'libmp3lame',
                '-qscale:a', '2',
                '-y',
                silencio_temp
            ]
            
            resultado_silencio = subprocess.run(comando_silencio,
                                              capture_output=True,
                                              text=True)
            
            if resultado_silencio.returncode == 0 and os.path.exists(silencio_temp):
                tamano_s = os.path.getsize(silencio_temp)
                print(f"     ✓ Creado ({tamano_s:,} bytes)")
            else:
                print(f"     ✗ Error")
    
    # 2. Combinar todos los archivos en uno solo
    print(f"\n2️⃣  COMBINANDO EN UN SOLO ARCHIVO: {archivo_final}")
    
    # Crear archivo de lista para ffmpeg
    lista_archivos = "lista_combinar.txt"
    with open(lista_archivos, 'w', encoding='utf-8') as f:
        for archivo in archivos_temporales:
            if os.path.exists(archivo):
                f.write(f"file '{os.path.abspath(archivo)}'\n")
    
    # Comando para combinar
    comando_combinar = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', lista_archivos,
        '-c', 'copy',
        '-y',
        archivo_final
    ]
    
    resultado_combinar = subprocess.run(comando_combinar,
                                      capture_output=True,
                                      text=True)
    
    if resultado_combinar.returncode == 0 and os.path.exists(archivo_final):
        tamano_final = os.path.getsize(archivo_final)
        print(f"   ✅ Archivo final creado: {archivo_final}")
        print(f"   📊 Tamaño: {tamano_final:,} bytes")
        
        # Calcular duración aproximada
        # 5 tonos de 0.5s + 4 silencios de 5s = 0.5*5 + 5*4 = 2.5 + 20 = 22.5s
        print(f"   ⏱️  Duración aproximada: 22.5 segundos")
        
    else:
        print(f"   ❌ Error combinando archivos")
        print(f"   Error: {resultado_combinar.stderr[:200]}")
    
    # 3. Limpiar archivos temporales
    print(f"\n3️⃣  LIMPIANDO ARCHIVOS TEMPORALES:")
    
    archivos_a_eliminar = archivos_temporales + [lista_archivos]
    eliminados = 0
    
    for archivo in archivos_a_eliminar:
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
                eliminados += 1
            except:
                print(f"   ⚠️  No se pudo eliminar: {archivo}")
    
    print(f"   ✅ Eliminados: {eliminados} archivos temporales")

except Exception as e:
    print(f"\n❌ ERROR: {e}")

finally:
    print(f"\n{'=' * 60}")
    print("🎉 PROCESO COMPLETADO")
    
    if os.path.exists(archivo_final):
        tamano = os.path.getsize(archivo_final)
        print(f"📁 Archivo creado: {archivo_final}")
        print(f"📊 Tamaño final: {tamano:,} bytes")
        print(f"📍 Ruta: {os.path.abspath(archivo_final)}")
        
        print(f"\n🔊 CONTENIDO DEL ARCHIVO:")
        print("   Tono 1 (600Hz) - 0.5s")
        print("   Silencio - 5s")
        print("   Tono 2 (700Hz) - 0.5s")
        print("   Silencio - 5s")
        print("   Tono 3 (800Hz) - 0.5s")
        print("   Silencio - 5s")
        print("   Tono 4 (900Hz) - 0.5s")
        print("   Silencio - 5s")
        print("   Tono 5 (1000Hz) - 0.5s")
        print(f"\n💡 Total: 5 tonos separados por 5 segundos de silencio")
    else:
        print("❌ No se pudo crear el archivo final")
import subprocess
import random
import os

def crear_beep_audiolibro(frecuencia, duracion=0.15, volumen=0.3, 
                          tipo="suave", output_file=None):
    """
    Crea beeps sutiles para audiolibros
    
    Parámetros:
    -----------
    frecuencia : int
        Frecuencia en Hz (recomendado: 300-800 Hz)
    duracion : float
        Duración en segundos (recomendado: 0.1-0.3s)
    volumen : float
        Nivel de volumen (0.0 a 1.0)
    tipo : str
        "suave", "fade", "corto"
    """
    
    if output_file is None:
        output_file = f'beep_audiolibro_{frecuencia}hz_{tipo}.mp3'
    
    # Base del comando FFmpeg
    base_cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'sine=frequency={frecuencia}:duration={duracion}',
        '-c:a', 'libmp3lame',
        '-q:a', '7',  # Calidad media-alta
        '-y'
    ]
    
    # Aplicar filtros según tipo
    if tipo == "suave":
        # Beep con fade in/out muy suave
        base_cmd.insert(8, f'volume={volumen},afade=t=in:st=0:d=0.05,afade=t=out:st={duracion-0.05}:d=0.05')
        base_cmd.insert(9, '-af')
    elif tipo == "fade":
        # Fade más pronunciado
        base_cmd.insert(8, f'volume={volumen*0.8},afade=t=in:st=0:d={duracion*0.4},afade=t=out:st={duracion*0.6}:d={duracion*0.4}')
        base_cmd.insert(9, '-af')
    elif tipo == "corto":
        # Muy corto y suave
        base_cmd.insert(8, f'volume={volumen*0.6}')
        base_cmd.insert(9, '-af')
    else:
        # Beep simple con volumen controlado
        base_cmd.insert(8, f'volume={volumen}')
        base_cmd.insert(9, '-af')
    
    base_cmd.append(output_file)
    
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Beep creado: {frecuencia}Hz, {duracion}s, {tipo}")
        return output_file
    else:
        print(f"❌ Error: {result.stderr[:150]}")
        return None

def generar_serie_beeps_audiolibro():
    """Genera una serie de beeps optimizados para audiolibros"""
    
    # Frecuencias recomendadas para audiolibros (Hz)
    frecuencias_audiolibro = [
        # Rango bajo-medio: sutiles, no estridentes
        320,   # Muy suave, casi imperceptible
        400,   # Estándar para alertas suaves
        500,   # Más audible pero no molesto
        600,   # Para cambios de capítulo
        750,   # Para énfasis importantes
    ]
    
    # Configuraciones por tipo de uso
    configuraciones = [
        # (frecuencia, duración, volumen, tipo, descripción)
        (400, 0.12, 0.25, "suave", "transicion_capitulo"),
        (500, 0.15, 0.3, "fade", "cambio_escena"),
        (320, 0.08, 0.2, "corto", "nota_al_margen"),
        (600, 0.2, 0.35, "suave", "final_seccion"),
        (750, 0.25, 0.4, "fade", "anuncio_importante"),
    ]
    
    archivos_creados = []
    
    print("\n🎵 GENERANDO BEEPS PARA AUDIOLIBROS 🎵")
    print("=" * 60)
    
    # Opción 1: Probar todas las frecuencias base
    print("\n1. Probando frecuencias base (0.15s, volumen 0.3):")
    for freq in frecuencias_audiolibro:
        archivo = crear_beep_audiolibro(
            frecuencia=freq,
            duracion=0.15,
            volumen=0.3,
            tipo="suave",
            output_file=f"beep_{freq}hz_suave.mp3"
        )
        if archivo:
            archivos_creados.append(archivo)
    
    # Opción 2: Probar configuraciones específicas
    print("\n2. Probando configuraciones específicas:")
    for freq, dur, vol, tipo, desc in configuraciones:
        archivo = crear_beep_audiolibro(
            frecuencia=freq,
            duracion=dur,
            volumen=vol,
            tipo=tipo,
            output_file=f"beep_{desc}_{freq}hz.mp3"
        )
        if archivo:
            archivos_creados.append(archivo)
            print(f"   {desc}: {freq}Hz, {dur}s, vol {vol}")
    
    return archivos_creados

def crear_beep_personalizado():
    """Interfaz para crear beep personalizado"""
    print("\n🎛️  CREAR BEEP PERSONALIZADO")
    print("-" * 40)
    
    try:
        frecuencia = int(input("Frecuencia (Hz, 200-1000 recomendado): ") or 400)
        duracion = float(input("Duración (segundos, 0.05-0.5): ") or 0.15)
        volumen = float(input("Volumen (0.1-0.5 recomendado): ") or 0.3)
        
        print("\nTipos disponibles:")
        print("1. suave - Fade in/out sutil")
        print("2. fade - Fade más pronunciado")
        print("3. corto - Muy breve")
        print("4. normal - Sin efectos")
        
        tipo_opcion = input("Tipo (1-4): ") or "1"
        tipos = {"1": "suave", "2": "fade", "3": "corto", "4": "normal"}
        tipo = tipos.get(tipo_opcion, "suave")
        
        descripcion = input("Descripción (para el nombre de archivo): ") or "personalizado"
        
        archivo = crear_beep_audiolibro(
            frecuencia=frecuencia,
            duracion=duracion,
            volumen=volumen,
            tipo=tipo,
            output_file=f"beep_{descripcion}_{frecuencia}hz.mp3"
        )
        
        if archivo:
            print(f"\n✅ Beep creado exitosamente: {archivo}")
            return archivo
    
    except ValueError as e:
        print(f"❌ Error en los valores ingresados: {e}")
    
    return None

def test_beep_humano():
    """Genera beeps que siguen la curva de sensibilidad del oído humano"""
    
    # Frecuencias que son naturalmente más audibles pero no molestas
    # Basado en la curva de Fletcher-Munson (igual sonoridad)
    frecuencias_naturales = [
        # Pico de sensibilidad del oído humano (~2000-5000 Hz)
        2000,  # Muy audible pero puede ser molesto
        1000,  # Punto de referencia estándar
        800,   # Balanceado
        600,   # Más suave
        400,   # Menos intrusivo
        
        # Frecuencias bajas para efectos sutiles
        250,   # Muy bajo, casi imperceptible
        300,   # Bajo pero presente
    ]
    
    print("\n👂 TEST BASADO EN CURVA DE SENSIBILIDAD HUMANA")
    print("=" * 60)
    
    archivos = []
    for freq in frecuencias_naturales:
        # Ajustar volumen basado en sensibilidad humana
        # El oído es menos sensible a frecuencias bajas y muy altas
        if freq >= 1000:
            volumen = 0.2  # Más bajo porque son más audibles
        elif freq <= 400:
            volumen = 0.35  # Más alto porque son menos audibles
        else:
            volumen = 0.3
        
        archivo = crear_beep_audiolibro(
            frecuencia=freq,
            duracion=0.2,
            volumen=volumen,
            tipo="suave",
            output_file=f"beep_humano_{freq}hz.mp3"
        )
        if archivo:
            archivos.append(archivo)
    
    return archivos

def crear_beep_musical(nota="C4", duracion=0.2, volumen=0.3):
    """Crea beeps basados en notas musicales"""
    
    # Frecuencias de notas musicales (Hz)
    notas_frecuencias = {
        # Octava 3 (bajas)
        "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61,
        "G3": 196.00, "A3": 220.00, "B3": 246.94,
        
        # Octava 4 (medias - ideales para audiolibros)
        "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
        "G4": 392.00, "A4": 440.00, "B4": 493.88,
        
        # Octava 5 (altas)
        "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
        "G5": 783.99, "A5": 880.00, "B5": 987.77,
    }
    
    if nota not in notas_frecuencias:
        print(f"❌ Nota no válida. Opciones: {list(notas_frecuencias.keys())}")
        return None
    
    frecuencia = notas_frecuencias[nota]
    archivo = crear_beep_audiolibro(
        frecuencia=frecuencia,
        duracion=duracion,
        volumen=volumen,
        tipo="suave",
        output_file=f"beep_nota_{nota}.mp3"
    )
    
    return archivo

def generar_playlist_test():
    """Genera un archivo de prueba con varios beeps"""
    
    beeps = [
        (400, 0.15, 0.25, "suave", "Transición"),
        (500, 0.12, 0.3, "fade", "Aviso"),
        (320, 0.1, 0.2, "corto", "Nota"),
        (600, 0.2, 0.35, "suave", "Fin de capítulo"),
    ]
    
    archivos = []
    for freq, dur, vol, tipo, desc in beeps:
        archivo = crear_beep_audiolibro(
            frecuencia=freq,
            duracion=dur,
            volumen=vol,
            tipo=tipo,
            output_file=f"beep_test_{desc.replace(' ', '_').lower()}.mp3"
        )
        if archivo:
            archivos.append(archivo)
    
    # Crear un archivo de texto con la descripción
    with open("beeps_descriptions.txt", "w", encoding="utf-8") as f:
        f.write("PLAYLIST DE BEEPS PARA AUDIOLIBRO\n")
        f.write("=" * 40 + "\n\n")
        
        for archivo, (freq, dur, vol, tipo, desc) in zip(archivos, beeps):
            f.write(f"Archivo: {archivo}\n")
            f.write(f"  Descripción: {desc}\n")
            f.write(f"  Frecuencia: {freq} Hz\n")
            f.write(f"  Duración: {dur} s\n")
            f.write(f"  Volumen: {vol}\n")
            f.write(f"  Tipo: {tipo}\n")
            f.write("-" * 30 + "\n")
    
    print(f"\n📝 Descripciones guardadas en: beeps_descriptions.txt")
    return archivos

# --- INTERFAZ PRINCIPAL ---
def menu_principal():
    """Menú interactivo para probar diferentes beeps"""
    
    while True:
        print("\n" + "=" * 60)
        print("🎧 GENERADOR DE BEEPS PARA AUDIOLIBROS")
        print("=" * 60)
        print("\nOpciones:")
        print("1. Generar serie de beeps recomendados")
        print("2. Crear beep personalizado")
        print("3. Test basado en sensibilidad humana")
        print("4. Beep musical (por nota)")
        print("5. Generar playlist de prueba")
        print("6. Salir")
        
        opcion = input("\nSelecciona una opción (1-6): ").strip()
        
        if opcion == "1":
            generar_serie_beeps_audiolibro()
        
        elif opcion == "2":
            crear_beep_personalizado()
        
        elif opcion == "3":
            test_beep_humano()
        
        elif opcion == "4":
            print("\nNotas disponibles:")
            print("C3, D3, E3, F3, G3, A3, B3")
            print("C4, D4, E4, F4, G4, A4, B4  ← Recomendadas")
            print("C5, D5, E5, F5, G5, A5, B5")
            
            nota = input("\nIngresa nota (ej: C4): ").strip().upper()
            if nota:
                crear_beep_musical(nota=nota)
        
        elif opcion == "5":
            archivos = generar_playlist_test()
            print(f"\n✅ Generados {len(archivos)} beeps de prueba")
            print("Revisa 'beeps_descriptions.txt' para las descripciones")
        
        elif opcion == "6":
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida. Intenta de nuevo.")
        
        # Preguntar si quiere continuar
        if opcion != "6":
            continuar = input("\n¿Quieres probar otra opción? (s/n): ").lower()
            if continuar != 's':
                print("\n👋 ¡Hasta luego!")
                break

# --- EJECUCIÓN RÁPIDA ---
if __name__ == "__main__":
    # Verificar si FFmpeg está instalado
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ FFmpeg no está instalado o no es accesible")
            print("   Descarga: https://ffmpeg.org/download.html")
            exit(1)
        else:
            print("✅ FFmpeg encontrado correctamente")
    except FileNotFoundError:
        print("❌ FFmpeg no está instalado")
        print("   Descarga: https://ffmpeg.org/download.html")
        exit(1)
    
    # Mostrar menú principal
    menu_principal()
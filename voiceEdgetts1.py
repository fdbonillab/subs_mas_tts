import re
import os
import asyncio
import edge_tts

# --- CONFIGURACIÓN ---
SRT_FILE = "sample_subtitulos.srt"      # Cambia por la ruta de tu archivo .srt
OUTPUT_DIR = "audios"                # Carpeta donde se guardarán los MP3
VOICE = "en-US-JennyNeural"          # Voz femenina americana. Puedes cambiar a otra.
# Lista completa de voces: ejecuta `edge-tts --list-voices` en la terminal

# --- Limpia texto de etiquetas HTML ---
def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)   # elimina <i>, <b>, etc.
    text = re.sub(r'\n', ' ', text)       # convierte saltos de línea en espacios
    return text.strip()

# --- Extrae los textos del SRT ---
def extract_texts_from_srt(srt_path):
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Patrón para capturar el texto de cada bloque
    pattern = r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(.*?)\n\n'
    matches = re.findall(pattern, content, re.DOTALL)
    texts = [clean_text(m) for m in matches if clean_text(m)]
    return texts

# --- Genera un MP3 para cada línea ---
async def generate_audio(text, index, voice, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"audio_{index:04d}.mp3")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)
    print(f"✓ {filename} generado")
    return filename

async def main():
    if not os.path.exists(SRT_FILE):
        print(f"Archivo no encontrado: {SRT_FILE}")
        return

    textos = extract_texts_from_srt(SRT_FILE)
    print(f"Se encontraron {len(textos)} fragmentos de diálogo.")

    for i, texto in enumerate(textos):
        await generate_audio(texto, i, VOICE, OUTPUT_DIR)

    print("\n¡Proceso completado! Los audios están en la carpeta:", OUTPUT_DIR)

if __name__ == "__main__":
    asyncio.run(main())
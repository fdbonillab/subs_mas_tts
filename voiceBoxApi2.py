import re
import os
from voicebox import SimpleVoicebox
from voicebox.tts import gTTS  # o el motor que prefieras
from IPython.display import Audio  # si usas Jupyter/Colab

# --- Configuración ---
# Elige el motor TTS que quieras usar
# Opciones: gTTS (online, gratuito), pyttsx3 (offline, voces del sistema),
#          ESpeakNG (offline), etc.
from voicebox.tts import gTTS

voicebox = SimpleVoicebox(tts=gTTS(lang='en'))

# --- Limpiar texto (eliminar etiquetas HTML) ---
def clean_text(text):
    return re.sub(r'<[^>]+>', '', text)

# --- Leer archivo SRT ---
def extract_text_from_srt(srt_path):
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extraer líneas de diálogo
    lines = re.findall(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(.*?)\n\n', content, re.DOTALL)
    texts = []
    for block in lines:
        text = re.sub(r'\n', ' ', block)
        text = clean_text(text)
        if text.strip():
            texts.append(text)
    return texts

# --- Generar audio para cada línea ---
def generate_audio(text, index):
    try:
        # voicebox.say() reproduce el audio, no guarda archivo
        # Para guardar, necesitas usar un sink (ver ejemplo abajo)
        print(f"Generando línea {index+1}: {text[:50]}...")
        voicebox.say(text)
        # Si quieres guardar como archivo, usa el código de la siguiente sección
        print(f"✓ Audio generado para línea {index+1}")
    except Exception as e:
        print(f"✗ Error en línea {index+1}: {e}")

# --- Main ---
if __name__ == "__main__":
    srt_file = "tus_subtitulos.srt"
    if not os.path.exists(srt_file):
        print(f"No se encontró el archivo: {srt_file}")
        exit(1)
    
    textos = extract_text_from_srt(srt_file)
    print(f"Se encontraron {len(textos)} líneas de diálogo.")
    
    for i, texto in enumerate(textos):
        generate_audio(texto, i)
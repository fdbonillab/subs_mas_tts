import requests
import re
import os

# Leer archivo SRT
with open('sample_subtitulos.srt', 'r', encoding='utf-8') as f:
    content = f.read()

# Extraer solo las líneas de texto
lines = re.findall(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(.*?)\n\n', content, re.DOTALL)

# Configurar API de Voicebox (ajusta engine y voz)
url = "http://localhost:17493/generate"
for i, text in enumerate(lines):
    payload = {
        "text": text,
        "engine": "ChatterboxTurbo",  # o el motor que prefieras
        "voice": "Mary",               # elige una voz disponible
        "language": "en"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        audio_data = response.content
        with open(f"audio_{i}.wav", "wb") as f:
            f.write(audio_data)
        print(f"Generado audio para línea {i+1}")
    else:
        print(f"Error en línea {i+1}: {response.text}")
import pysrt
import subprocess
import os
import random

class AudioProcessor:
    def __init__(self, video_path, srt_path):
        self.video = video_path
        self.subs = pysrt.open(srt_path)
        self.temp_files = []
        
    def crear_marcador(self, tipo="default", duracion=0.3):
        """Crea diferentes tipos de marcadores"""
        
        marcadores = {
            "tono": f'sine=frequency=800:duration={duracion}',
            "beep": f'sine=frequency=1000:duration=0.1:sample_rate=44100',
            "click": f'anoisesrc=d={duracion}:c=white',
            "campana": f'sine=frequency=2000:duration=0.5, sine=frequency=1500:duration=0.5',
            "silencioso": f'anoisesrc=d={duracion}:c=pink:r=44100:a=0.1'
        }
        
        filtro = ""
        if tipo == "beep":
            filtro = "-af volume=0.5"
        elif tipo == "silencioso":
            filtro = "-af volume=0.2"
        
        output_file = f'marcador_{tipo}_{random.randint(1000,9999)}.mp3'
        
        cmd = ['ffmpeg', '-f', 'lavfi', '-i', marcadores.get(tipo, marcadores["tono"])]
        if filtro:
            cmd.extend(filtro.split())
        cmd.extend(['-c:a', 'libmp3lame', '-q:a', '9', '-y', output_file])
        
        subprocess.run(cmd, capture_output=True)
        self.temp_files.append(output_file)
        return output_file
    
    def extraer_dialogo(self, sub_idx, margen=0.1):
        """Extrae un diálogo con márgenes"""
        sub = self.subs[sub_idx]
        
        start_sec = sub.start.ordinal / 1000.0 - margen
        end_sec = sub.end.ordinal / 1000.0 + margen
        
        # Formatear tiempo
        def seg_a_str(segundos):
            h = int(segundos // 3600)
            m = int((segundos % 3600) // 60)
            s = int(segundos % 60)
            ms = int((segundos - int(segundos)) * 1000)
            return f"{h:02}:{m:02}:{s:02}.{ms:03}"
        
        start_str = seg_a_str(start_sec)
        end_str = seg_a_str(end_sec)
        
        output_file = f'dialogo_{sub_idx:04d}.mp3'
        
        cmd = [
            'ffmpeg',
            '-i', self.video,
            '-ss', start_str,
            '-to', end_str,
            '-q:a', '2',
            '-map', '0:a',
            '-y',
            output_file
        ]
        
        subprocess.run(cmd, capture_output=True)
        self.temp_files.append(output_file)
        return output_file
    
    def procesar_con_marcadores(self, num_dialogos=5, tipo_marcador="beep"):
        """Procesa diálogos con marcadores entre ellos"""
        
        print(f"Procesando {num_dialogos} diálogos con marcadores tipo '{tipo_marcador}'...\n")
        
        # Crear marcador
        marcador = self.crear_marcador(tipo_marcador)
        
        # Lista para concatenar
        lista_concat = []
        
        for i in range(min(num_dialogos, len(self.subs))):
            # Extraer diálogo
            dialogo_file = self.extraer_dialogo(i)
            lista_concat.append(dialogo_file)
            
            print(f"Diálogo {i+1}: {self.subs[i].text[:50]}...")
            
            # Agregar marcador (excepto después del último)
            if i < min(num_dialogos, len(self.subs)) - 1:
                lista_concat.append(marcador)
                print(f"  [+] Marcador añadido")
        
        # Crear archivo de lista
        lista_file = 'lista_final.txt'
        with open(lista_file, 'w', encoding='utf-8') as f:
            for archivo in lista_concat:
                f.write(f"file '{os.path.abspath(archivo)}'\n")
        
        # Combinar
        output_final = f'dialogos_con_{tipo_marcador}.mp3'
        
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', lista_file,
            '-c', 'copy',
            '-y',
            output_final
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ Archivo creado: {output_final}")
        
        # Limpiar lista
        if os.path.exists(lista_file):
            os.remove(lista_file)
        
        return output_final
    
    def limpiar_temporales(self):
        """Limpia archivos temporales"""
        for temp in self.temp_files:
            if os.path.exists(temp):
                os.remove(temp)
        print(f"Limpieza: {len(self.temp_files)} archivos temporales eliminados")

# Uso
processor = AudioProcessor('The.Matrix.1999.mp4', 'The Matrix (1999)-en.srt')

# Probar diferentes marcadores
tipos_marcadores = ["beep", "tono", "click", "silencioso"]

for tipo in tipos_marcadores:
    print(f"\n{'='*50}")
    print(f"Creando con marcador: {tipo}")
    print('='*50)
    
    output = processor.procesar_con_marcadores(num_dialogos=5, tipo_marcador=tipo)
    
    # Verificar duración
    cmd = ['ffprobe', '-i', output, '-show_entries', 'format=duration', 
           '-v', 'quiet', '-of', 'csv=p=0']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        duracion = float(result.stdout.strip())
        print(f"Duración total: {duracion:.2f} segundos")

# Limpiar
processor.limpiar_temporales()
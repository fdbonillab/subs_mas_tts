import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import seaborn as sns
from scipy import signal
import soundfile as sf
from matplotlib.gridspec import GridSpec

class AudioAnalyzer:
    def __init__(self, title="Audio Analysis"):
        plt.style.use('dark_background')
        sns.set_palette("husl")
        self.title = title
    
    def plot_comparison(self, original_path, processed_path, save_path=None):
        """Comparación completa antes/después"""
        # Cargar audios
        y_orig, sr_orig = librosa.load(original_path, sr=None, mono=True)
        y_proc, sr_proc = librosa.load(processed_path, sr=None, mono=True)
        
        if sr_orig != sr_proc:
            y_proc = librosa.resample(y_proc, orig_sr=sr_proc, target_sr=sr_orig)
            sr_proc = sr_orig
        
        # Crear figura con múltiples subplots
        fig = plt.figure(figsize=(20, 16))
        gs = GridSpec(4, 2, figure=fig, hspace=0.3, wspace=0.2)
        
        # 1. FORMA DE ONDA (superpuesta)
        ax1 = fig.add_subplot(gs[0, :])
        time_orig = np.arange(len(y_orig)) / sr_orig
        time_proc = np.arange(len(y_proc)) / sr_proc
        
        ax1.plot(time_orig, y_orig, alpha=0.7, label='Original', linewidth=0.5)
        ax1.plot(time_proc, y_proc, alpha=0.7, label='Procesado', linewidth=0.5)
        ax1.set_title(f'Forma de Onda Comparativa | {self.title}', fontsize=14)
        ax1.set_xlabel('Tiempo (s)')
        ax1.set_ylabel('Amplitud')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # 2. HISTOGRAMA de amplitudes
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.hist(y_orig, bins=100, alpha=0.5, label='Original', density=True)
        ax2.hist(y_proc, bins=100, alpha=0.5, label='Procesado', density=True)
        ax2.set_title('Distribución de Amplitudes')
        ax2.set_xlabel('Amplitud')
        ax2.set_ylabel('Densidad')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        # 3. RMS en ventanas (ENVOLVENTE)
        ax3 = fig.add_subplot(gs[1, 1])
        hop_length = 512
        
        # Calcular RMS
        rms_orig = librosa.feature.rms(y=y_orig, frame_length=2048, hop_length=hop_length)[0]
        rms_proc = librosa.feature.rms(y=y_proc, frame_length=2048, hop_length=hop_length)[0]
        
        # Tiempos para RMS
        times_rms = librosa.frames_to_time(np.arange(len(rms_orig)), sr=sr_orig, hop_length=hop_length)
        
        ax3.plot(times_rms, librosa.amplitude_to_db(rms_orig, ref=np.max), 
                alpha=0.8, label='Original', linewidth=2)
        ax3.plot(times_rms, librosa.amplitude_to_db(rms_proc, ref=np.max), 
                alpha=0.8, label='Procesado', linewidth=2)
        ax3.set_title('Energía RMS (dB)')
        ax3.set_xlabel('Tiempo (s)')
        ax3.set_ylabel('RMS (dB)')
        ax3.legend()
        ax3.grid(alpha=0.3)
        
        # 4. PICO MÁXIMO por ventana
        ax4 = fig.add_subplot(gs[2, 0])
        
        # Calcular picos en ventanas
        win_size = 2048
        peaks_orig = []
        peaks_proc = []
        peak_times = []
        
        for i in range(0, len(y_orig), win_size):
            win_orig = y_orig[i:i+win_size]
            win_proc = y_proc[i:i+win_size]
            if len(win_orig) > 0:
                peaks_orig.append(np.max(np.abs(win_orig)))
                peaks_proc.append(np.max(np.abs(win_proc)))
                peak_times.append(i / sr_orig)
        
        ax4.plot(peak_times, librosa.amplitude_to_db(peaks_orig, ref=np.max),
                alpha=0.7, label='Original', marker='o', markersize=2, linewidth=1)
        ax4.plot(peak_times, librosa.amplitude_to_db(peaks_proc, ref=np.max),
                alpha=0.7, label='Procesado', marker='o', markersize=2, linewidth=1)
        ax4.set_title('Picos Máximos por Ventana')
        ax4.set_xlabel('Tiempo (s)')
        ax4.set_ylabel('Amplitud Pico (dB)')
        ax4.legend()
        ax4.grid(alpha=0.3)
        
        # 5. CREST FACTOR (Ratio Pico/RMS) - Índice de "picosidad"
        ax5 = fig.add_subplot(gs[2, 1])
        
        # Calcular Crest Factor por ventana
        cf_orig = []
        cf_proc = []
        cf_times = []
        
        for i in range(0, len(y_orig), win_size):
            win_orig = y_orig[i:i+win_size]
            win_proc = y_proc[i:i+win_size]
            if len(win_orig) > 100:  # Ventana válida
                rms_o = np.sqrt(np.mean(win_orig**2))
                rms_p = np.sqrt(np.mean(win_proc**2))
                peak_o = np.max(np.abs(win_orig))
                peak_p = np.max(np.abs(win_proc))
                
                if rms_o > 1e-6 and rms_p > 1e-6:
                    cf_orig.append(peak_o / rms_o)
                    cf_proc.append(peak_p / rms_p)
                    cf_times.append(i / sr_orig)
        
        ax5.plot(cf_times, cf_orig, alpha=0.7, label='Original', linewidth=2)
        ax5.plot(cf_times, cf_proc, alpha=0.7, label='Procesado', linewidth=2)
        ax5.set_title('Crest Factor (Pico/RMS)')
        ax5.set_xlabel('Tiempo (s)')
        ax5.set_ylabel('Crest Factor')
        ax5.legend()
        ax5.grid(alpha=0.3)
        ax5.set_ylim(0, max(max(cf_orig), max(cf_proc)) * 1.1)
        
        # 6. ESPECTROGRAMAS comparativos
        ax6 = fig.add_subplot(gs[3, 0])
        ax7 = fig.add_subplot(gs[3, 1])
        
        # Espectrograma original
        D_orig = librosa.amplitude_to_db(np.abs(librosa.stft(y_orig)), ref=np.max)
        img_orig = librosa.display.specshow(D_orig, sr=sr_orig, x_axis='time', 
                                           y_axis='log', ax=ax6)
        ax6.set_title('Espectrograma - Original')
        ax6.set_xlabel('Tiempo (s)')
        ax6.set_ylabel('Frecuencia (Hz)')
        plt.colorbar(img_orig, ax=ax6, format='%+2.0f dB')
        
        # Espectrograma procesado
        D_proc = librosa.amplitude_to_db(np.abs(librosa.stft(y_proc)), ref=np.max)
        img_proc = librosa.display.specshow(D_proc, sr=sr_proc, x_axis='time', 
                                           y_axis='log', ax=ax7)
        ax7.set_title('Espectrograma - Procesado')
        ax7.set_xlabel('Tiempo (s)')
        ax7.set_ylabel('Frecuencia (Hz)')
        plt.colorbar(img_proc, ax=ax7, format='%+2.0f dB')
        
        # 7. ESTADÍSTICAS de resumen
        stats_text = f"""
        ESTADÍSTICAS COMPARATIVAS
        
        ORIGINAL:
        - RMS medio: {np.mean(y_orig**2)**0.5:.6f}
        - Pico máximo: {np.max(np.abs(y_orig)):.6f} ({librosa.amplitude_to_db(np.max(np.abs(y_orig)), ref=1):.1f} dBFS)
        - Crest factor medio: {np.mean(cf_orig):.2f}:1
        - Rango dinámico: {self.calculate_dynamic_range(y_orig):.1f} dB
        
        PROCESADO:
        - RMS medio: {np.mean(y_proc**2)**0.5:.6f}
        - Pico máximo: {np.max(np.abs(y_proc)):.6f} ({librosa.amplitude_to_db(np.max(np.abs(y_proc)), ref=1):.1f} dBFS)
        - Crest factor medio: {np.mean(cf_proc):.2f}:1
        - Rango dinámico: {self.calculate_dynamic_range(y_proc):.1f} dB
        
        REDUCCIÓN:
        - Reducción de pico: {librosa.amplitude_to_db(np.max(np.abs(y_orig))/np.max(np.abs(y_proc)), ref=1):.1f} dB
        - Compresión: {((1 - np.mean(cf_proc)/np.mean(cf_orig)) * 100):.1f}%
        """
        
        # Añadir texto en un cuadro
        plt.figtext(0.02, 0.02, stats_text, fontfamily='monospace', fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="black", alpha=0.7))
        
        plt.suptitle(f'ANÁLISIS DE AUDIO: {self.title}', fontsize=16, y=0.98)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Gráfico guardado en: {save_path}")
        
        plt.show()
        return fig
    
    def calculate_dynamic_range(self, audio):
        """Calcula el rango dinámico en dB"""
        rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        return np.max(rms_db) - np.min(rms_db[rms_db > -80])  # Ignorar silencio

# Uso:
analyzer = AudioAnalyzer("Reducción de Picos - Balas/Explosiones")
##analyzer.plot_comparison("original.wav", "procesado.wav", "analisis_comparativo.png")
analyzer.plot_comparison("salida_final.mp3", "output.mp3", "analisis_comparativo.png")
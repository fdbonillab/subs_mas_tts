def plot_large_audio_comparison(original_path, processed_path, decimation_factor=100):
    """
    Versión optimizada para archivos de audio largos
    """
    import numpy as np
    import matplotlib.pyplot as plt
    import librosa
    
    # Cargar audio
    y_orig, sr_orig = librosa.load(original_path, sr=None, mono=True)
    y_proc, sr_proc = librosa.load(processed_path, sr=None, mono=True)
    
    # Submuestrear para visualización
    y_orig_plot = y_orig[::decimation_factor]
    y_proc_plot = y_proc[::decimation_factor]
    
    # Crear eje de tiempo submuestreado
    time_orig = np.arange(len(y_orig_plot)) * decimation_factor / sr_orig
    time_proc = np.arange(len(y_proc_plot)) * decimation_factor / sr_proc
    
    # Gráfico simple
    plt.figure(figsize=(15, 6))
    plt.plot(time_orig, y_orig_plot, alpha=0.7, label='Original', linewidth=0.5)
    plt.plot(time_proc, y_proc_plot, alpha=0.7, label='Procesado', linewidth=0.5)
    plt.title(f'Forma de Onda Submuestreada (1 de cada {decimation_factor} muestras)')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Amplitud')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()
    
    # Calcular estadísticas sin cargar todo en memoria a la vez
    print(f"Estadísticas:")
    print(f"- Duración original: {len(y_orig)/sr_orig:.1f} segundos")
    print(f"- Muestras originales: {len(y_orig):,}")
    print(f"- Factor de submuestreo usado: {decimation_factor}")
    print(f"- Muestras graficadas: {len(y_orig_plot):,}")

# Uso:
plot_large_audio_comparison("salida_final.mp3", "output.mp3", decimation_factor=500)
###analyzer.plot_comparison("salida_final.mp3", "output.mp3", "analisis_comparativo.png")
# 1. Verificar FFmpeg básico
import subprocess
result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
print("FFmpeg version output:")
print(result.stdout[:500])
print("\nReturn code:", result.returncode)

# 2. Probar comando simple
test_cmd = [
    'ffmpeg',
    '-f', 'lavfi',
    '-i', 'sine=frequency=400:duration=0.5',
    'test_output.wav'
]
print("\nProbando comando simple...")
result2 = subprocess.run(test_cmd, capture_output=True, text=True)
print("Return code:", result2.returncode)
if result2.returncode != 0:
    print("Error completo:")
    print(result2.stderr)
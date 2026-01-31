# prueba_escena.ps1 - Extraer solo UNA escena para probar

$video = "The_Matrix_1999.mp4"
$srt = "The Matrix (1999)-en.srt"

# Leer primera entrada del SRT
$content = Get-Content $srt -First 20
Write-Host "Primeras líneas del SRT:" -ForegroundColor Yellow
$content
Write-Host ""

# Extraer tiempos manualmente del primer bloque
# Ejemplo si el SRT muestra: 1[crlf]00:00:05,000 --> 00:00:08,000[crlf]Texto
$primerBloque = $content -join "`n"

if ($primerBloque -match '(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})') {
    $startH = [int]$matches[1]
    $startM = [int]$matches[2]
    $startS = [int]$matches[3]
    $startMs = [int]$matches[4]
    
    $endH = [int]$matches[5]
    $endM = [int]$matches[6]
    $endS = [int]$matches[7]
    $endMs = [int]$matches[8]
    
    # Calcular
    $startTotal = $startH*3600 + $startM*60 + $startS + $startMs/1000.0
    $endTotal = $endH*3600 + $endM*60 + $endS + $endMs/1000.0
    $duration = $endTotal - $startTotal
    
    # Formatear CORRECTAMENTE
    $startFF = "{0:00}:{1:00}:{2:00}.{3:000}" -f $startH, $startM, $startS, $startMs
    
    Write-Host "Información extraída:" -ForegroundColor Green
    Write-Host "  Inicio: $startH`:$startM`:$startS,$startMs"
    Write-Host "  Fin: $endH`:$endM`:$endS,$endMs"
    Write-Host "  Duración: $duration segundos"
    Write-Host "  Tiempo FFmpeg: $startFF"
    
    # Comando de prueba
    Write-Host "`nEjecutando FFmpeg..." -ForegroundColor Cyan
    ffmpeg -ss $startFF -i $video -t $duration -c copy "prueba_escena.mp4"
    
    if (Test-Path "prueba_escena.mp4") {
        Write-Host "`n¡Éxito! Escena guardada como 'prueba_escena.mp4'" -ForegroundColor Green
        $size = (Get-Item "prueba_escena.mp4").Length / 1MB
        Write-Host "Tamaño: $($size.ToString('F2')) MB" -ForegroundColor Green
    } else {
        Write-Host "`nError: No se creó el archivo" -ForegroundColor Red
    }
} else {
    Write-Host "No se pudieron extraer tiempos del SRT" -ForegroundColor Red
    Write-Host "Formato encontrado:" -ForegroundColor Yellow
    Write-Host $primerBloque
}
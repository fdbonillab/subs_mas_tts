# Guarda como extraer-escenas.ps1
param(
    [string]$video = "The_Matrix_1999.mp4",
    [string]$srt = "The Matrix (1999)-en.srt",
    [int]$margen = 1  # segundos antes/después
)

# Función para formatear tiempo correctamente
function Format-TimeForFFmpeg {
    param([double]$totalSeconds)
    
    $hours = [math]::Floor($totalSeconds / 3600)
    $minutes = [math]::Floor(($totalSeconds % 3600) / 60)
    $seconds = $totalSeconds % 60
    
    # Asegurar que los milisegundos tengan 3 dígitos
    $milliseconds = [math]::Round(($seconds - [math]::Floor($seconds)) * 1000)
    $seconds = [math]::Floor($seconds)
    
    return "{0:00}:{1:00}:{2:00}.{3:000}" -f $hours, $minutes, $seconds, $milliseconds
}

# Verificar que FFmpeg esté disponible
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: FFmpeg no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Descarga FFmpeg de: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Yellow
    Write-Host "Extrae en C:\ffmpeg\ y añade C:\ffmpeg\bin al PATH" -ForegroundColor Yellow
    exit 1
}

# Verificar que los archivos existan
if (-not (Test-Path $video)) {
    Write-Host "ERROR: Archivo de video no encontrado: $video" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $srt)) {
    Write-Host "ERROR: Archivo SRT no encontrado: $srt" -ForegroundColor Red
    exit 1
}

Write-Host "=" * 60
Write-Host "EXTRACTOR DE ESCENAS CON SRT" -ForegroundColor Cyan
Write-Host "Video: $video"
Write-Host "Subtítulos: $srt"
Write-Host "=" * 60

# Leer archivo SRT
$subtitleContent = Get-Content $srt -Raw -Encoding UTF8
if (-not $subtitleContent) {
    # Intentar con otra codificación
    $subtitleContent = Get-Content $srt -Raw -Encoding Default
}

# Patrón para SRT - versión mejorada
$pattern = '(?m)^(\d+)\s*\r?\n(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*\r?\n(.*?)(?=\r?\n\r?\n|\Z)'

$matches = [regex]::Matches($subtitleContent, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)

if ($matches.Count -eq 0) {
    Write-Host "ERROR: No se encontraron subtítulos en el archivo SRT" -ForegroundColor Red
    Write-Host "Verifica el formato del archivo SRT" -ForegroundColor Yellow
    exit 1
}

Write-Host "Encontrados $($matches.Count) bloques de subtítulos`n" -ForegroundColor Green

# Crear carpeta para resultados
$outputDir = "Escenas_Extraidas"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$counter = 1
$successCount = 0

foreach ($match in $matches) {
    $id = $match.Groups[1].Value
    $startH = [int]$match.Groups[2].Value
    $startM = [int]$match.Groups[3].Value
    $startS = [int]$match.Groups[4].Value
    $startMs = [int]$match.Groups[5].Value
    
    $endH = [int]$match.Groups[6].Value
    $endM = [int]$match.Groups[7].Value
    $endS = [int]$match.Groups[8].Value
    $endMs = [int]$match.Groups[9].Value
    
    $texto = $match.Groups[10].Value.Trim()
    
    # Convertir a segundos totales CON márgenes
    $startTotal = $startH*3600 + $startM*60 + $startS + $startMs/1000.0 - $margen
    if ($startTotal -lt 0) { $startTotal = 0 }  # No permitir tiempos negativos
    
    $endTotal = $endH*3600 + $endM*60 + $endS + $endMs/1000.0 + $margen
    
    # Calcular duración
    $duration = $endTotal - $startTotal
    
    # Formatear tiempos CORRECTAMENTE
    $startFF = Format-TimeForFFmpeg $startTotal
    
    # Crear nombre seguro para archivo
    $nombreSeguro = $texto -replace '[^\p{L}\p{N}\s]', '' -replace '\s+', '_'
    if ($nombreSeguro.Length -gt 30) {
        $nombreSeguro = $nombreSeguro.Substring(0, 30)
    }
    if ([string]::IsNullOrEmpty($nombreSeguro)) {
        $nombreSeguro = "Escena_$id"
    }
    
    $outputFile = "$outputDir\Escena_{0:0000}_{1}.mp4" -f $counter, $nombreSeguro
    
    Write-Host "[$counter/$($matches.Count)] Bloque $id" -ForegroundColor Yellow
    Write-Host "  Texto: $($texto.Substring(0, [Math]::Min(50, $texto.Length)))..." -ForegroundColor Gray
    Write-Host "  Tiempo: $startH`:$startM`:$startS`,$startMs --> $endH`:$endM`:$endS,$endMs" -ForegroundColor Gray
    Write-Host "  Con margen: $startFF (dur: $($duration.ToString('F2'))s)" -ForegroundColor Gray
    Write-Host "  Archivo: $(Split-Path $outputFile -Leaf)" -ForegroundColor Gray
    
    # Construir comando FFmpeg
    $ffmpegArgs = @(
        "-ss", $startFF,
        "-i", "`"$video`"",
        "-t", $duration.ToString('F6'),
        "-c:v", "copy",
        "-c:a", "copy",
        "-avoid_negative_ts", "make_zero",
        "-y",
        "`"$outputFile`""
    )
    
    # Mostrar comando (para depuración)
    # Write-Host "  Comando: ffmpeg $($ffmpegArgs -join ' ')" -ForegroundColor DarkGray
    
    # Ejecutar FFmpeg
    $process = Start-Process -FilePath "ffmpeg" `
        -ArgumentList $ffmpegArgs `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardError "$outputDir\ffmpeg_error_$counter.log"
    
    if ($process.ExitCode -eq 0 -and (Test-Path $outputFile) -and ((Get-Item $outputFile).Length -gt 1024)) {
        Write-Host "  ✓ Extraído exitosamente" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ✗ Error al extraer (código: $($process.ExitCode))" -ForegroundColor Red
        
        # Intentar método alternativo (recompresión) si falla
        Write-Host "  ⚠ Intentando con recompresión..." -ForegroundColor Yellow
        
        $ffmpegArgsAlt = @(
            "-ss", $startFF,
            "-i", "`"$video`"",
            "-t", $duration.ToString('F6'),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",
            "`"$outputFile`""
        )
        
        $processAlt = Start-Process -FilePath "ffmpeg" `
            -ArgumentList $ffmpegArgsAlt `
            -NoNewWindow `
            -Wait `
            -PassThru
        
        if ($processAlt.ExitCode -eq 0 -and (Test-Path $outputFile)) {
            Write-Host "  ✓ Extraído con recompresión" -ForegroundColor Green
            $successCount++
        }
    }
    
    Write-Host ""
    $counter++
}

# Resumen
Write-Host "=" * 60
Write-Host "PROCESO COMPLETADO" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Total de bloques procesados: $($matches.Count)" -ForegroundColor White
Write-Host "Escenas extraídas exitosamente: $successCount" -ForegroundColor Green
Write-Host "Fallos: $($matches.Count - $successCount)" -ForegroundColor $(if (($matches.Count - $successCount) -gt 0) { "Red" } else { "Gray" })
Write-Host "Carpeta de resultados: $(Resolve-Path $outputDir)" -ForegroundColor White

# Mostrar tamaño total
if ($successCount -gt 0) {
    $totalSize = (Get-ChildItem $outputDir\*.mp4 | Measure-Object -Property Length -Sum).Sum
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-Host "Tamaño total: $totalSizeMB MB" -ForegroundColor White
}

Write-Host "`nPresiona cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
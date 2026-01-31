# Guarda como extraer-escenas.ps1
param(
    [string]$video = "The_Matrix_1999.mp4",
    [string]$srt = "The Matrix (1999)-en.srt",
    [int]$margen = 1  # segundos antes/después
)

# Leer archivo SRT y extraer tiempos
$subtitleContent = Get-Content $srt -Raw
$pattern = "(?s)(\d+)\r?\n(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\r?\n(.*?)\r?\n\r?\n"

$matches = [regex]::Matches($subtitleContent, $pattern)

$counter = 1
foreach ($match in $matches) {
    $startH = [int]$match.Groups[2].Value
    $startM = [int]$match.Groups[3].Value
    $startS = [int]$match.Groups[4].Value
    $startMs = [int]$match.Groups[5].Value
    
    $endH = [int]$match.Groups[6].Value
    $endM = [int]$match.Groups[7].Value
    $endS = [int]$match.Groups[8].Value
    $endMs = [int]$match.Groups[9].Value
    
    $texto = $match.Groups[10].Value
    
    # Convertir a segundos totales
    $startTotal = $startH*3600 + $startM*60 + $startS + $startMs/1000 - $margen
    $endTotal = $endH*3600 + $endM*60 + $endS + $endMs/1000 + $margen
    
    # Formatear tiempo para FFmpeg
    $startFF = "{0:00}:{1:00}:{2:00}.{3:000}" -f [Math]::Floor($startTotal/3600), 
        [Math]::Floor(($startTotal%3600)/60), 
        [Math]::Floor($startTotal%60),
        ($startTotal - [Math]::Floor($startTotal))*1000
        
    $duration = $endTotal - $startTotal
    
    # Crear nombre seguro para archivo
    $nombreSeguro = $texto -replace '[^\w\s]', '' -replace '\s+', '_'
    $nombreSeguro = $nombreSeguro.Substring(0, [Math]::Min(30, $nombreSeguro.Length))
    
    # Extraer escena
    $outputFile = "Escena_{0:000}_{1}.mp4" -f $counter, $nombreSeguro
    Write-Host "Extrayendo: $outputFile" -ForegroundColor Yellow
    
    ffmpeg -ss $startFF -i $video -t $duration -c:v copy -c:a copy $outputFile
    
    $counter++
}
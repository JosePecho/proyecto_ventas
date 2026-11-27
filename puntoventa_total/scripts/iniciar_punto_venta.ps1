param([switch]$ReiniciarVista, [switch]$AbrirNavegador)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
Push-Location $projectRoot
try {
    & $pythonPath scripts/mariadb_local.py start
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar MariaDB.' }

    if ($ReiniciarVista) {
        $previewProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
            Where-Object {
                $_.ExecutablePath -eq $pythonPath -and
                $_.CommandLine -like '*manage.py*runserver*127.0.0.1:8000*--settings=config.settings.preview*'
            }
        foreach ($previewProcess in $previewProcesses) {
            & taskkill.exe /PID $previewProcess.ProcessId /T /F
            if ($LASTEXITCODE -ne 0) { throw 'No se pudo detener la vista SQLite anterior.' }
        }
    }

    $listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Output 'El puerto 8000 ya esta ocupado. No se inicio otro servidor.'
        return
    }
    Start-Process -FilePath $pythonPath -ArgumentList 'manage.py','runserver','127.0.0.1:8000','--noreload','--settings=config.settings.development' `
        -WorkingDirectory $projectRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $projectRoot 'reports\punto-venta-server.log') `
        -RedirectStandardError (Join-Path $projectRoot 'reports\punto-venta-server-error.log')
    Write-Output 'Aplicacion iniciada en http://127.0.0.1:8000/ con la conexion de .env.'
    if ($AbrirNavegador) {
        $ready = $false
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            try {
                $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 2
                if ($response.StatusCode -eq 200) { $ready = $true; break }
            }
            catch { Start-Sleep -Milliseconds 500 }
        }
        if (-not $ready) { throw 'La aplicacion no respondio; revisar reports/punto-venta-server-error.log.' }
        Start-Process 'http://127.0.0.1:8000/'
        Start-Process 'http://localhost/phpmyadmin/index.php?route=/database/structure&server=2&db=punto_venta'
    }
}
finally {
    Pop-Location
}

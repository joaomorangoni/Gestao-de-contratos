$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Crie o ambiente .venv e instale as dependências conforme o README.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\node_modules'))) { throw 'Execute npm.cmd install --prefix frontend primeiro.' }
$runtimePath = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
foreach ($port in @(5000, 5173)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Porta $port já está em uso. Encerre o serviço existente antes de iniciar novamente." }
}
$apiProcess = Start-Process -FilePath $pythonPath -ArgumentList 'api_contratos_flask/app.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimePath 'api.log') -RedirectStandardError (Join-Path $runtimePath 'api-error.log')
$webProcess = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList 'node_modules/vite/bin/vite.js --host 127.0.0.1 --strictPort' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimePath 'frontend.log') -RedirectStandardError (Join-Path $runtimePath 'frontend-error.log')
@{api=$apiProcess.Id; frontend=$webProcess.Id} | ConvertTo-Json | Set-Content (Join-Path $runtimePath 'processos.json')
Write-Host 'Frontend: http://127.0.0.1:5173 | API: http://127.0.0.1:5000'
Write-Host 'Logs e identificadores dos processos em .runtime/'

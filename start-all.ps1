$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$frontendCommand = 'pnpm --dir frontend dev'
$backendCommand = 'uv run --directory backend uvicorn app.main:app --app-dir src --reload --host 127.0.0.1 --port 8010'

Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root'; $frontendCommand"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root'; $backendCommand"

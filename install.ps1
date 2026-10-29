# crypto-cli Hermes 스킬 설치 (Windows PowerShell)
# 사용: powershell -ExecutionPolicy Bypass -File .\install.ps1 [-Force] [-Dest <경로>]
param(
    [switch]$Force,
    [string]$Dest
)
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Src  = Join-Path $Root "skills\crypto\crypto-cli"
if (-not $Dest) {
    $HermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $HOME ".hermes" }
    $Dest = Join-Path $HermesHome "skills\crypto\crypto-cli"
}

$Py = $null
foreach ($c in @("py", "python", "python3")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
}
if (-not $Py) { Write-Error "Python 을 찾을 수 없습니다."; exit 1 }

& $Py -c "import cryptography" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] cryptography 설치 중..."
    & $Py -m pip install -r (Join-Path $Root "requirements.txt")
    if ($LASTEXITCODE -ne 0) { Write-Error "cryptography 설치 실패"; exit 1 }
}

if (Test-Path $Dest) {
    if ($Force) { Remove-Item -Recurse -Force $Dest }
    else { Write-Error "이미 존재: $Dest (덮어쓰려면 -Force)"; exit 1 }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
Copy-Item -Recurse $Src $Dest
Write-Host "[OK] 설치: $Dest"

$env:PYTHONIOENCODING = "utf-8"
& $Py (Join-Path $Dest "scripts\selftest.py") | Select-Object -Last 1
Write-Host "새 Hermes 세션에서 스킬이 활성화됩니다."

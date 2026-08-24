# Загрузка проекта на VPS с Windows (PowerShell)
# Usage: .\deploy\upload.ps1 -Server root@123.45.67.89

param(
    [Parameter(Mandatory = $true)]
    [string]$Server
)

$RemoteDir = "/opt/english-tutor-bot"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "==> Uploading to ${Server}:${RemoteDir}"

ssh $Server "mkdir -p $RemoteDir"

# scp recursive (requires OpenSSH client on Windows)
scp -r "$ProjectRoot\bot" "$ProjectRoot\data" "$ProjectRoot\deploy" `
    "$ProjectRoot\requirements.txt" "$ProjectRoot\.env.example" `
    "$ProjectRoot\english-tutor.service" "$ProjectRoot\README.md" `
    "${Server}:${RemoteDir}/"

Write-Host "==> Installing on server"
ssh $Server "chmod +x ${RemoteDir}/deploy/install.sh && bash ${RemoteDir}/deploy/install.sh"

Write-Host ""
Write-Host "Next steps on server:"
Write-Host "  ssh $Server"
Write-Host "  nano ${RemoteDir}/.env"
Write-Host "  systemctl start english-tutor"
Write-Host "  journalctl -u english-tutor -f"

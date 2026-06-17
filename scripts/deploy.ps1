param(
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example. Fill DEEPSEEK_API_KEY for live generation."
}

if ($SkipBuild) {
  docker compose up -d
} else {
  docker compose up --build -d
}

Write-Host ""
Write-Host "PathFinder Lite is starting."
Write-Host "App:    http://localhost:8000/app"
Write-Host "Status: http://localhost:8000/api/status"
Write-Host "Demos:"
Write-Host "  http://localhost:8000/app/external-plan-audit-demo"
Write-Host "  http://localhost:8000/app/admissions-opportunity-demo"

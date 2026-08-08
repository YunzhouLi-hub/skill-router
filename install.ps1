# Install / refresh Skill Router for Cursor + Claude on Windows
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python .\scripts\generate.py --install
Write-Host ""
Write-Host "Installed. Restart Cursor chat (or start a new agent) to pick up skill-router."
Write-Host "Index: $PSScriptRoot\SKILL.md"
Write-Host "Catalog: $PSScriptRoot\skills-catalog.json"

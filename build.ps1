#Requires -Version 7
# Пакует skills/pishi в dist/pishi.zip для загрузки в claude.ai и ChatGPT.
$ErrorActionPreference = 'Stop'

$src = Join-Path $PSScriptRoot 'skills/pishi'
$dist = Join-Path $PSScriptRoot 'dist'
$zip = Join-Path $dist 'pishi.zip'

New-Item -ItemType Directory -Force $dist | Out-Null
Remove-Item $zip -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($src, $zip, [IO.Compression.CompressionLevel]::Optimal, $true)
$zip

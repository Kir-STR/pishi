#Requires -Version 7
# Пакует skills/pishi-sokrashchai в dist/pishi-sokrashchai.zip для загрузки в claude.ai и ChatGPT.
$ErrorActionPreference = 'Stop'

$src = Join-Path $PSScriptRoot 'skills/pishi-sokrashchai'
$dist = Join-Path $PSScriptRoot 'dist'
$zip = Join-Path $dist 'pishi-sokrashchai.zip'

New-Item -ItemType Directory -Force $dist | Out-Null
Remove-Item $zip -ErrorAction SilentlyContinue
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($src, $zip, [IO.Compression.CompressionLevel]::Optimal, $true)
$zip

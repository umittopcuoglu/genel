# Load from .env file or set manually
$envFile = "$(Get-Location)\.env"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '(.+?)=(.+)') {
            $name = $matches[1]
            $value = $matches[2]
            Set-Item -Path "env:$name" -Value $value
        }
    }
    Write-Host "✅ Environment variables loaded from .env"
} else {
    Write-Host "⚠️  .env file not found"
    Write-Host "Please create .env file with DEEPSEEK_API_KEY and GITHUB_PAT"
}

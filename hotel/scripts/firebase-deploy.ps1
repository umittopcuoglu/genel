# HotelOps — Tek tikla Firebase deploy
# Kullanim: PowerShell'de calistir: .\firebase-deploy.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== HotelOps Firebase Deploy ===" -ForegroundColor Cyan

# 1. Firebase CLI kontrol
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Host "Firebase CLI yukleniyor..." -ForegroundColor Yellow
    npm install -g firebase-tools
}

# 2. Login
Write-Host "`nFirebase'e giris yapin (tarayici acilacak)..." -ForegroundColor Yellow
firebase login

# 3. Proje secimi
Write-Host "`nFirebase projelerin:" -ForegroundColor Yellow
firebase projects:list

$projectId = Read-Host "`nKullanmak istediginiz proje ID'sini girin (yoksa: hotelops-demo)"
if ([string]::IsNullOrWhiteSpace($projectId)) {
    $projectId = "hotelops-demo"
    Write-Host "Yeni proje olusturuluyor: $projectId" -ForegroundColor Yellow
    firebase projects:create $projectId --display-name "HotelOps Demo"
}

# 4. Frontend build
Write-Host "`nFrontend build ediliyor..." -ForegroundColor Yellow
Push-Location ..\frontend
if (-not (Test-Path node_modules)) {
    npm install
}
npx next build
Pop-Location

# 5. Firebase config
Push-Location ..
$firebaserc = @{ projects = @{ default = $projectId } } | ConvertTo-Json
Set-Content -Path ".firebaserc" -Value $firebaserc

# 6. Deploy
Write-Host "`nDeploy basliyor..." -ForegroundColor Yellow
firebase deploy --only hosting --project $projectId

Pop-Location

Write-Host "`n=== Tamam! ===" -ForegroundColor Green
Write-Host "Demo URL: https://$projectId.web.app" -ForegroundColor Green

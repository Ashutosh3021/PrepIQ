# PowerShell script to fix API URL port from 8001 to 8000
# Run this in the frontend directory: .\fix-port.ps1

$envFile = ".env.local"

Write-Host "🔍 Checking .env.local file..." -ForegroundColor Cyan

if (Test-Path $envFile) {
    Write-Host "✅ Found .env.local file" -ForegroundColor Green
    
    $content = Get-Content $envFile -Raw
    
    if ($content -match "8001") {
        Write-Host "⚠️  Found port 8001 - fixing to 8000..." -ForegroundColor Yellow
        
        # Replace 8001 with 8000
        $content = $content -replace "localhost:8001", "localhost:8000"
        $content = $content -replace "127\.0\.0\.1:8001", "127.0.0.1:8000"
        $content = $content -replace ":8001", ":8000"
        
        # Save the file
        Set-Content -Path $envFile -Value $content -NoNewline
        
        Write-Host "✅ Fixed! Updated .env.local to use port 8000" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Updated content:" -ForegroundColor Cyan
        Get-Content $envFile | Select-String "NEXT_PUBLIC_API_URL"
    }
    else {
        Write-Host "✅ Port is already correct (8000)" -ForegroundColor Green
        Get-Content $envFile | Select-String "NEXT_PUBLIC_API_URL"
    }
}
else {
    Write-Host "⚠️  .env.local file not found" -ForegroundColor Yellow
    Write-Host "   Creating it with correct configuration..." -ForegroundColor Yellow
    
    $envContent = "# PrepIQ Frontend Environment Variables`n`n# Backend API URL - MUST match your backend server port (8000)`nNEXT_PUBLIC_API_URL=http://localhost:8000`n`n# Supabase Configuration (if using Supabase)`n# NEXT_PUBLIC_SUPABASE_URL=your_supabase_url`n# NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key`n`n# Google Gemini API Key (optional, for frontend AI features)`n# NEXT_PUBLIC_GEMINI_API_KEY=your_gemini_api_key`n"
    
    Set-Content -Path $envFile -Value $envContent
    Write-Host "✅ Created .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔄 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Restart your Next.js dev server (Ctrl+C, then npm run dev)" -ForegroundColor White
Write-Host "   2. Clear browser cache (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "   3. Try logging in again" -ForegroundColor White
Write-Host ""

@echo off
setlocal
title Push MechPulse to GitHub
color 0A

echo =======================================================================
echo    MechPulse - One-Click Push to GitHub
echo    Target: https://github.com/AOUEDidris/MechPulse
echo =======================================================================
echo.
echo Uploading your files to GitHub...
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo =======================================================================
    echo   [SUCCESS] All files uploaded successfully!
    echo   Visit your project: https://github.com/AOUEDidris/MechPulse
    echo =======================================================================
) else (
    echo.
    echo =======================================================================
    echo   [NOTE] If GitHub asked for a password:
    echo   GitHub does NOT accept your account password for git push.
    echo   Instead, use a Personal Access Token (PAT):
    echo     1. Open: https://github.com/settings/tokens
    echo     2. Click "Generate new token (classic)"
    echo     3. Check the "repo" box and click Generate
    echo     4. Copy the token and paste it here when prompted for password!
    echo =======================================================================
)

echo.
pause

@echo off
setlocal enabledelayedexpansion
title GitHub Repository Setup - VibrationGuard AI
echo ========================================================
echo   VibrationGuard AI - GitHub Initialization Script
echo ========================================================
echo.

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [-] Git is not installed or not in your PATH.
    echo [+] Please download and install Git from: https://git-scm.com/download/win
    echo [+] Or install it via Scoop: scoop install git
    echo.
    pause
    exit /b 1
)

echo [+] Git is detected!
echo.
echo Step 1: Initializing git repository...
git init

echo.
echo Step 2: Staging all project files...
git add .

echo.
echo Step 3: Creating initial commit...
git commit -m "feat: initial commit of VibrationGuard AI predictive maintenance system"

echo.
echo Step 4: Renaming branch to main...
git branch -M main

echo.
echo ========================================================
echo Almost done!
echo Please create a new empty repository on your GitHub account,
echo then paste its HTTPS URL below (e.g. https://github.com/username/vibration-guard.git):
set /p REPO_URL="Enter your GitHub Repository URL: "

if "%REPO_URL%"=="" (
    echo [-] No URL entered. You can link it manually later using:
    echo     git remote add origin YOUR_URL
    echo     git push -u origin main
) else (
    git remote remove origin >nul 2>nul
    git remote add origin %REPO_URL%
    echo.
    echo Pushing code to GitHub...
    git push -u origin main
    echo.
    echo [+] Done! Check your repository on GitHub.
)

pause

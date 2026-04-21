@echo off
echo.
echo === SecondBrains GitHub Sync ===
cd /d "%~dp0"
git add .
git diff --cached --quiet && echo No changes to sync today. && goto end
git commit -m "auto sync %date% %time%"
git push origin master
echo.
echo === Done! Your work is saved to GitHub ===
:end
timeout /t 3
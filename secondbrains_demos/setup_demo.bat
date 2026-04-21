@echo off
echo Setting up demo index files...

for /d %%D in (*) do (
    if not exist "%%D\index.html" (
        for %%F in ("%%D\*.html") do (
            echo ^<!DOCTYPE html^> > "%%D\index.html"
            echo ^<html^>^<head^> >> "%%D\index.html"
            echo ^<meta http-equiv="refresh" content="0; url='./%%~nxF'" /^> >> "%%D\index.html"
            echo ^</head^>^<body^>^</body^>^</html^> >> "%%D\index.html"
            echo Created index.html for %%D pointing to %%~nxF
        )
    ) else (
        echo %%D already has index.html - skipping
    )
)
echo Done!
pause
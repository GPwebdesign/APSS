@echo off
setlocal

:: Verifica che siamo nella root del repo APSS
if not exist ".git" (
    echo ERRORE: Esegui questo script dalla root del progetto APSS.
    pause
    exit /b 1
)

:menu
cls
echo ============================================
echo   APSS > Aggiornamento Subtree da GitHub
echo ============================================
echo.
echo  1. Pull rosmaster_project
echo  2. Pull ros2_py_ws
echo  3. Pull entrambi i repo
echo  4. Quit
echo.
set /p "scelta=Scelta: "

if "%scelta%"=="1" goto pull_rosmaster
if "%scelta%"=="2" goto pull_ros2
if "%scelta%"=="3" goto pull_entrambi
if "%scelta%"=="4" goto fine
echo Scelta non valida. Riprova.
timeout /t 2 >nul
goto menu

:pull_rosmaster
echo.
echo [1/1] Pull rosmaster_project...
git subtree pull --prefix=rosmaster_project https://github.com/GPwebdesign/rosmaster_project.git main --squash
if %errorlevel% neq 0 (
    echo ERRORE durante il pull di rosmaster_project.
    goto fine_operazione
)
echo OK > rosmaster_project aggiornato.
goto push_apss

:pull_ros2
echo.
echo [1/1] Pull ros2_py_ws...
git subtree pull --prefix=ros2_py_ws https://github.com/GPwebdesign/ros2_py_ws.git main --squash
if %errorlevel% neq 0 (
    echo ERRORE durante il pull di ros2_py_ws.
    goto fine_operazione
)
echo OK > ros2_py_ws aggiornato.
goto push_apss

:pull_entrambi
echo.
echo [1/2] Pull rosmaster_project...
git subtree pull --prefix=rosmaster_project https://github.com/GPwebdesign/rosmaster_project.git main --squash
if %errorlevel% neq 0 (
    echo ERRORE durante il pull di rosmaster_project.
    goto fine_operazione
)
echo OK > rosmaster_project aggiornato.
echo.
echo [2/2] Pull ros2_py_ws...
git subtree pull --prefix=ros2_py_ws https://github.com/GPwebdesign/ros2_py_ws.git main --squash
if %errorlevel% neq 0 (
    echo ERRORE durante il pull di ros2_py_ws.
    goto fine_operazione
)
echo OK > ros2_py_ws aggiornato.
goto push_apss

:push_apss
echo.
echo [push] Allineamento APSS su GitHub...
git push origin master
if %errorlevel% neq 0 (
    echo ERRORE durante il push di APSS su GitHub.
) else (
    echo OK > github.com/GPwebdesign/APSS aggiornato.
)
goto fine_operazione

:fine_operazione
echo.
pause
goto menu

:fine
exit /b 0

@echo off
setlocal

echo ============================================
echo   ArchAnalyse - Startup
echo ============================================
echo.
echo How would you like to run ArchAnalyse?
echo.
echo   [1] Auto-detect  (use GPU if available, otherwise CPU)
echo   [2] GPU only     (force GPU mode - requires NVIDIA CUDA)
echo   [3] CPU only     (force CPU mode)
echo.
set /p CHOICE="Enter choice [1/2/3] (default: 1): "

if "%CHOICE%"=="" set CHOICE=1
if "%CHOICE%"=="1" goto AUTO
if "%CHOICE%"=="2" goto GPU
if "%CHOICE%"=="3" goto CPU

echo Invalid choice. Defaulting to auto-detect...
goto AUTO

:: ── Auto-detect ──────────────────────────────────────────────────────────────
:AUTO
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo GPU detected, building with CUDA support...
    goto GPU_BUILD
) else (
    echo.
    echo No GPU detected, building CPU only...
    goto CPU_BUILD
)

:: ── Force GPU ─────────────────────────────────────────────────────────────────
:GPU
nvidia-smi >nul 2>&1
if not %errorlevel% == 0 (
    echo.
    echo WARNING: nvidia-smi not found or GPU not accessible.
    echo          Make sure NVIDIA drivers and NVIDIA Container Toolkit are installed.
    echo.
    set /p CONFIRM="Continue anyway? [y/N]: "
    if /i not "%CONFIRM%"=="y" (
        echo Aborted.
        pause
        exit /b 1
    )
)
echo.
echo Building with CUDA support...
goto GPU_BUILD

:: ── Force CPU ─────────────────────────────────────────────────────────────────
:CPU
echo.
echo Building CPU only...
goto CPU_BUILD

:: ── Build & run ───────────────────────────────────────────────────────────────
:GPU_BUILD
set USE_GPU=true
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build --build-arg USE_GPU=true
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
goto DONE

:CPU_BUILD
set USE_GPU=false
docker compose build --build-arg USE_GPU=false
docker compose up -d
goto DONE

:DONE
echo.
echo ============================================
echo   ArchAnalyse is running!
echo   Open http://localhost in your browser.
echo ============================================
echo.
pause
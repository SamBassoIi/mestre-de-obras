@echo off
title AutoCroqui3D - Desenho Tecnico 2 e Autodesk Inventor
echo ======================================================================
echo    AutoCroqui3D - Sistema de Leitura de Croquis e Modelagem CAD
echo ======================================================================
echo.
echo Iniciando o servidor local e abrindo o navegador...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run.py
) else (
    py run.py
)

pause

@echo off
title AutoCroqui3D - Desenho Tecnico 2 e Autodesk Inventor
echo ======================================================================
echo    AutoCroqui3D - Sistema de Leitura de Croquis e Modelagem CAD
echo ======================================================================
echo.
echo Iniciando o servidor local e abrindo o navegador...
echo.

set PYTHON_EXE=C:\Users\samuel.bassoli\portable_python_311\python.exe

if not exist "%PYTHON_EXE%" (
    python run.py
) else (
    "%PYTHON_EXE%" run.py
)

pause

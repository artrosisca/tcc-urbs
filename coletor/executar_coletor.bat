@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  Coletor de dados da URBS
echo ============================================
echo.

echo Instalando dependencias (pode demorar na primeira vez)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo.
echo Desativando suspensao do Windows (energia da tomada)...
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change monitor-timeout-ac 0 >nul 2>&1

echo.
echo Iniciando a coleta a cada 20 segundos.
echo NAO feche esta janela. Para parar, aperte CTRL+C.
echo.
python coletor_urbs.py

pause

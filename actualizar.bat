@echo off
cd /d "%~dp0"

rem Usa Python 3.14 si esta instalado; si no, usa Python 3.13
py -3.14 --version >nul 2>&1 && (set VERSION=-3.14) || (set VERSION=-3.13)

py %VERSION% -X utf8 -u ejecutar_todo.py >> registro_actualizacion.txt 2>&1

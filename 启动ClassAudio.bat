@echo off
chcp 65001 >nul
REM ClassAudio 一键启动脚本 - 使用 aiagent 环境

cd /d "%~dp0"

echo ============================================================
echo ClassAudio - 启动服务
echo ============================================================
echo.
echo 环境: aiagent (Python 3.10)
echo.

REM 清理 Python 缓存（确保加载最新代码）
echo 正在清理 Python 缓存...
for /d /r %%i in (__pycache__) do @if exist "%%i" rd /s /q "%%i" 2>nul
del /s /q *.pyc 2>nul
echo.

D:\Anaconda\envs\aiagent\python.exe run.py

pause

@echo off
echo Clearing Python cache...

REM 删除所有 __pycache__ 目录
for /d /r %%i in (__pycache__) do (
    if exist "%%i" (
        echo Deleting %%i
        rd /s /q "%%i"
    )
)

REM 删除所有 .pyc 文件
del /s /q *.pyc 2>nul

echo Cache cleared!
pause

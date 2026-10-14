@echo off
chcp 65001 >nul
title codex-squeeze
cd /d "%~dp0"
echo 启动中…（这个窗口显示盯会话和自动挤的记录；挤的消息直接发进会话）

where py >nul 2>nul
if not errorlevel 1 goto :runpy
where python >nul 2>nul
if not errorlevel 1 goto :runpython
echo 没有找到 Python。请先安装 Python 3（python.org 下载，安装时勾选 Add python.exe to PATH），然后重新双击本文件。
goto :end

:runpy
py codex-squeeze.py %*
goto :end

:runpython
python codex-squeeze.py %*
goto :end

:end
echo.
echo 已结束。按任意键关闭窗口…
pause >nul

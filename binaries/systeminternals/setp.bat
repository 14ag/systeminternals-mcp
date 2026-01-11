@echo off
set currentDirectory=%~dp0%
REM echo %currentDirectory%
setx path "%currentDirectory%;%path%" /M
(
echo "%path%" >nul | find /i "%currentDirectory%" && echo yes
) || (
echo no
)
pause
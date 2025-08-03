@echo off
echo %~n0
echo.

echo This generates windows executables and demo into dist-folder
echo Note: confirm with 'y'
echo ---------------------

set DIST_DIR=.\dist
set BUILD_DIR=.\build

if exist %BUILD_DIR% rmdir %BUILD_DIR% /S/Q

pyinstaller  insertConditionDistanceCmds.py 

set EL=%ERRORLEVEL%
echo.

if %EL% == 0 goto OK
set MESSAGE=Generation failed (%EL%)
goto FINISH

:OK
set MESSAGE=Generation completed!
echo Restore in-folder and insertConditionDistanceCmds.bat
xcopy /s .\in %DIST_DIR%\insertConditionDistanceCmds\in\
xcopy insertConditionDistanceCmds.bat %DIST_DIR%\insertConditionDistanceCmds

:FINISH
echo.
echo %MESSAGE%
echo.
pause
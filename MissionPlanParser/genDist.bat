@echo off
echo %~n0
echo.

echo This generates windows executables and demo into dist-folder
echo Note: confirm with 'y'
echo ---------------------

set DIST_DIR=.\dist
set BUILD_DIR=.\build

if exist %BUILD_DIR% rmdir %BUILD_DIR% /S/Q

pyinstaller  genFrontBackCmds.py 

set EL=%ERRORLEVEL%
echo.

if %EL% == 0 goto OK
set MESSAGE=Generation failed (%EL%)
goto FINISH

:OK
set MESSAGE=Generation completed!
echo Restore in-folder and genFrontBackCmds.bat
xcopy /s .\in %DIST_DIR%\genFrontBackCmds\in\
xcopy genFrontBackCmds.bat %DIST_DIR%\genFrontBackCmds

:FINISH
echo.
echo %MESSAGE%
echo.
pause
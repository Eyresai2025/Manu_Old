@echo off
 
cd C:\Users\DELL\Desktop\smartqc-manu-gui
set VIRTUAL_ENV=C:\Users\DELL\Desktop\smartqc-manu-gui\manu_env
 
if not defined PROMPT set PROMPT=$P$G
 
if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%
 
set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(manu_env) %PROMPT%
 
if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=
 
if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%
 
set PATH=%VIRTUAL_ENV%\Scripts;%PATH%
 
python ManuGUI.py
pause
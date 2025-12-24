@echo off
setlocal

set "PY_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if exist "%PY_EXE%" goto HAVE_PY_EXE

where py >nul 2>nul
if %errorlevel%==0 (
  py -3.12 -c "import sys" >nul 2>nul
  if %errorlevel%==0 (
    set "PY_CMD=py -3.12"
    goto HAVE_PY_CMD
  )
)

echo Python 3.12 not found. Please install Python 3.12 (64-bit) or fix PATH.
pause
exit /b 1

:HAVE_PY_EXE
"%PY_EXE%" -m pip install -r requirements.txt
goto DONE

:HAVE_PY_CMD
%PY_CMD% -m pip install -r requirements.txt

:DONE
echo successfully done!
pause

@echo off
echo Installing required packages...
pip install -r requirements.txt
echo.
echo Running transfer script...
python run.py
pause

@echo off
echo Setting up Python virtual environment for B-Roll Engine...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
pip install -r requirements.txt

echo Virtual environment setup complete!
echo To activate: call src\python\venv\Scripts\activate.bat
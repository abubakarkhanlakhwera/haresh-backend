@echo off
echo Starting Medical Assistant Backend...
echo.

REM Check if virtual environment exists
if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/Update dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check for .env file
if not exist .env (
    echo WARNING: .env file not found!
    echo Please create a .env file with your OPENAI_API_KEY
    pause
    exit /b 1
)

REM Start the server
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python main.py

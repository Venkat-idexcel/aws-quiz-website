@echo off
echo Starting AWS Quiz Platform...
echo.
echo Make sure PostgreSQL is running on port 5480
echo Database: cretificate_quiz_db
echo.
cd /d "%~dp0"
python app.py
pause
# Windows Command Script to Upload Files to EC2
# Save this as upload_to_ec2.bat
# Edit the variables below with your actual values

@echo off
setlocal

REM ========================================
REM CONFIGURATION - EDIT THESE VALUES
REM ========================================
set EC2_USER=ec2-user
set EC2_HOST=YOUR_EC2_PUBLIC_IP_HERE
set KEY_FILE=C:\path\to\your\key.ppk
set LOCAL_PATH=c:\Users\venkatasai.p\Documents\aws_quiz_website
set REMOTE_PATH=/var/www/aws-quiz-app

REM ========================================
REM DO NOT EDIT BELOW THIS LINE
REM ========================================

echo ==========================================
echo AWS Quiz App - Upload to EC2
echo ==========================================
echo.

REM Check if pscp exists
where pscp >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pscp not found in PATH
    echo Please install PuTTY and add it to your PATH
    echo Download from: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    pause
    exit /b 1
)

echo Uploading files to EC2...
echo From: %LOCAL_PATH%
echo To: %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%
echo.

REM Upload Python files
echo Uploading Python files...
pscp -i %KEY_FILE% %LOCAL_PATH%\*.py %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

REM Upload requirements
echo Uploading requirements.txt...
pscp -i %KEY_FILE% %LOCAL_PATH%\requirements.txt %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

REM Upload templates directory
echo Uploading templates...
pscp -r -i %KEY_FILE% %LOCAL_PATH%\templates %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

REM Upload static directory
echo Uploading static files...
pscp -r -i %KEY_FILE% %LOCAL_PATH%\static %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

REM Upload deployment scripts
echo Uploading deployment scripts...
pscp -i %KEY_FILE% %LOCAL_PATH%\*.sh %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

REM Upload markdown documentation
echo Uploading documentation...
pscp -i %KEY_FILE% %LOCAL_PATH%\*.md %EC2_USER%@%EC2_HOST%:%REMOTE_PATH%/

echo.
echo ==========================================
echo Upload complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Connect to EC2 via PuTTY
echo 2. Run: cd /var/www/aws-quiz-app
echo 3. Run: bash quick_deploy_ec2.sh
echo 4. Run: sudo systemctl start aws-quiz-app
echo.
pause

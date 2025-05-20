@echo off
REM === Start Docker Desktop ===
echo Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

REM === Wait for Docker to be fully ready ===
:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker not ready yet. Waiting...
    timeout /t 3 >nul
    goto wait_docker
)

REM === Navigate to your project directory ===
cd /d "C:\Users\arair\Documents\coding-projects\dollar-tracker-app"

REM === Run Docker Compose ===
echo Starting containers with Docker Compose...
docker compose build --no-cache
docker compose up -d
start http://localhost:8501

REM === Wait for user input before closing ===
pause
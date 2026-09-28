@echo off
echo ==========================================
echo      US CORN DATA PIPELINE
echo ==========================================

:: 0. ENVIRONMENT SETUP (Auto-install dependencies)
echo.
echo [Phase 0] Checking and Installing Dependencies...
python setup_env.py

:: Check if the setup failed
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CRITICAL ERROR] Dependency installation failed. Pipeline stopped.
    pause
    exit /b %ERRORLEVEL%
)

:: 1. SETUP ENV VARS
:: Get the full path to the key file
set DBT_GOOGLE_KEYFILE=%CD%\keys\service_account.json

:: 2. RUN INGESTION (Python)
echo.
echo [Phase 1] Ingestion: Scraping and Uploading...
python main.py %*

:: 3. RUN TRANSFORMATION (dbt)
echo.
echo [Phase 2] Transformation: Running dbt...
cd data_transformation

:: Install dbt deps if needed
dbt deps --profiles-dir .

:: Run the models, pointing to the local profiles.yml (current dir)
dbt run --profiles-dir .

:: Go back to root
cd ..

:: 4. RUN DATA QUALITY / TESTING
echo.
echo [Phase 3] Data Quality & Testing...

:: Navigate into the nested folder
cd "Data Quality and Testing\my_ag_project"

:: Run the python pipeline script
python run_pipeline.py

:: Return to root (Go up 2 levels)
cd ..\..

echo.
echo ==========================================
echo      ALL JOBS COMPLETE
echo ==========================================
pause
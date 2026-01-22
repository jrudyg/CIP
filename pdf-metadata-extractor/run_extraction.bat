@echo off
REM ============================================================================
REM CIP Contract Metadata Extraction - Recurring Run Script
REM ============================================================================
REM
REM Purpose: Extract metadata from Active Contracts and import to CIP database
REM Usage: Double-click or run from command line
REM Frequency: Run weekly or when new contracts are added
REM
REM Features:
REM - Only processes new/changed files (SHA256 cache)
REM - 3-5x faster than initial run
REM - Automatic CIP database import
REM - Summary report generation
REM
REM ============================================================================

echo.
echo ================================================================================
echo CIP Contract Metadata Extraction
echo ================================================================================
echo.

REM Change to pdf-metadata-extractor directory
cd /d C:\Users\jrudy\CIP\pdf-metadata-extractor

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Run extraction (only processes new/changed files via cache)
echo ================================================================================
echo Running metadata extraction...
echo ================================================================================
echo Source: OneDrive\Contract Management\01 Active Contracts
echo Output: outputs\recurring
echo Workers: 6 (parallel processing)
echo Format: JSON
echo Caching: ENABLED (only processes new/changed files)
echo.

python main.py "C:\Users\jrudy\OneDrive - Diakonia Group, LLC\Contract Management - Documents\01 Active Contracts" --recursive --workers 6 --format json -o ".\outputs\recurring"

if errorlevel 1 (
    echo.
    echo ERROR: Extraction failed
    echo Check logs directory for details
    pause
    exit /b 1
)

echo.
echo [OK] Extraction complete
echo.

REM Import to CIP database
echo ================================================================================
echo Importing metadata to CIP database...
echo ================================================================================
echo.

python C:\Users\jrudy\CIP\scripts\import_metadata_extraction.py

if errorlevel 1 (
    echo.
    echo ERROR: Database import failed
    pause
    exit /b 1
)

echo.
echo [OK] Database import complete
echo.

REM Generate HTML report
echo ================================================================================
echo Generating HTML report...
echo ================================================================================
echo.

python generate_html_report.py

if errorlevel 1 (
    echo WARNING: HTML report generation failed
) else (
    echo [OK] HTML report created
)

echo.
echo ================================================================================
echo Extraction Complete!
echo ================================================================================
echo.
echo Next steps:
echo   - Review extraction results in outputs\recurring\exports\
echo   - Check CIP database for updated contract metadata
echo   - Review priority contracts for execution status
echo.
echo To run again: Just double-click this script or run from command line
echo Caching ensures only new/changed files are processed (fast re-runs)
echo.

deactivate
pause

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

REM Generate summary report
echo ================================================================================
echo Generating summary report...
echo ================================================================================
echo.

python -c "import json; from pathlib import Path; from datetime import datetime; import sqlite3; json_path = max(Path('outputs/recurring/exports').glob('metadata_export_*.json'), key=lambda p: p.stat().st_mtime); data = json.load(open(json_path)); conn = sqlite3.connect('C:/Users/jrudy/CIP/data/contracts.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM contract_metadata'); total = cursor.fetchone()[0]; cursor.execute('SELECT execution_status, COUNT(*) FROM contract_metadata GROUP BY execution_status'); statuses = cursor.fetchall(); print('\n' + '='*80); print('EXTRACTION SUMMARY'); print('='*80); print(f'Date: {datetime.now().strftime(\"%%Y-%%m-%%d %%H:%%M:%%S\")}'); print(f'Total contracts in database: {total}'); print(f'\nExecution Status:'); [print(f'  {s[0]:25s}: {s[1]:3d}') for s in statuses]; print('\nFiles:'); print(f'  Extraction results: {json_path.name}'); print(f'  Session state: session_state.json'); print(f'  Logs: logs/'); print('='*80); conn.close()"

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

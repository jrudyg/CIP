@echo off
REM CIP Monitor - Real-time monitoring
REM Usage: monitor health|logs|errors|tail|dashboard
python "%~dp0tools\monitoring\cip_monitor.py" %*

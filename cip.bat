@echo off
REM CIP Manager - Start, stop, restart CIP services
REM Usage: cip start|stop|restart|status [backend|frontend|all]
python "%~dp0tools\monitoring\cip_manager.py" %*

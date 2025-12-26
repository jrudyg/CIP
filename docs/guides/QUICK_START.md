# CIP - Quick Start Guide

## Starting the Application

You have **3 options** for running CIP locally:

### Option 1: Minimized Windows (Recommended)
```bash
start-cip.bat
```
- Starts both backend and frontend in **minimized windows**
- You can see logs by clicking on the minimized windows
- Easy to debug if something goes wrong
- **Close the windows** to stop the servers

### Option 2: Completely Hidden (Cleanest)
```bash
start-cip-hidden.bat
```
- Runs both servers **completely in background**
- No visible windows at all
- Automatically opens browser to http://localhost:8501
- Must use `stop-cip.bat` to stop servers

### Option 3: Manual (For Development)
```bash
# Terminal 1
cd C:\Users\jrudy\CIP
python backend\api.py

# Terminal 2
cd C:\Users\jrudy\CIP\frontend
streamlit run app.py
```
- Full control and visibility of logs
- Best for active development/debugging
- Requires 2 open terminals

## Stopping the Application

### Stop All Servers
```bash
stop-cip.bat
```
Stops all CIP backend and frontend processes.

### Manual Stop
- **Option 1/3:** Close the terminal windows
- **Option 2:** Run `stop-cip.bat` (required since processes are hidden)

## Quick Access URLs

- **Frontend (Streamlit):** http://localhost:8501
- **Backend API:** http://127.0.0.1:5000
- **API Docs:** http://127.0.0.1:5000/api/health

## Troubleshooting

### "Port already in use" Error
```bash
# Stop all existing processes
stop-cip.bat

# Then restart
start-cip.bat
```

### Check if Servers are Running
```bash
# Check backend (port 5000)
netstat -ano | findstr :5000

# Check frontend (port 8501)
netstat -ano | findstr :8501
```

### View Logs
- **Option 1:** Click on the minimized window titles
- **Option 2:** Logs are not visible (use Option 1 or 3 for debugging)
- **Option 3:** Visible directly in terminals

## Production Deployment

For production, consider:
1. **Windows Service** using NSSM (Non-Sucking Service Manager)
2. **Docker Compose** for containerized deployment
3. **Cloud hosting** (AWS, Azure, Google Cloud)

See `DEPLOYMENT.md` for detailed production setup instructions.

---

**Recommended for Daily Use:** `start-cip.bat` (minimized windows)
**Recommended for Demos:** `start-cip-hidden.bat` (cleanest, no visible windows)
**Recommended for Development:** Manual option (full log visibility)

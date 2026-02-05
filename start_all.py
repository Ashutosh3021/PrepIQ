#!/usr/bin/env python3
"""
PrepIQ Application Startup Script
Starts both backend and frontend services on their documented default ports:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    print("🚀 Starting PrepIQ Application")
    print("=" * 50)
    print("Documentation Default Ports:")
    print("- Backend:  http://localhost:8000")
    print("- Frontend: http://localhost:3000")
    print("=" * 50)
    
    # Get project root directory
    project_root = Path(__file__).parent.absolute()
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    # Change to backend directory and start backend
    print("\n🔧 Starting Backend Server...")
    os.chdir(backend_dir)
    
    backend_process = subprocess.Popen([
        sys.executable, "start_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Check if backend started successfully
    if backend_process.poll() is not None:
        print("❌ Backend failed to start")
        stderr = backend_process.stderr.read()
        print(f"Error: {stderr}")
        return
    
    print("✅ Backend Server Started")
    
    # Change to frontend directory and start frontend
    print("\n🎨 Starting Frontend Server...")
    os.chdir(frontend_dir)
    
    frontend_process = subprocess.Popen([
        "npm", "run", "dev:default"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Monitor both processes
    try:
        print("✅ Frontend Server Started")
        print("\n🎯 Applications Running:")
        print("- Backend:  http://localhost:8000")
        print("- Frontend: http://localhost:3000")
        print("\nPress Ctrl+C to stop both servers")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for processes to terminate
        backend_process.wait(timeout=5)
        frontend_process.wait(timeout=5)
        
        print("✅ Servers stopped successfully")

if __name__ == "__main__":
    main()
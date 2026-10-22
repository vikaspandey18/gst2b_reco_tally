import os
import sys
import time
import socket
import threading
import webbrowser
import uvicorn
from app.main import app

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("==================================================================")
    print(" GST 2B & TALLY BOOK RECONCILIATION APPLICATION")
    print("==================================================================")
    print(" Status: Running successfully!")
    print(f" Local URL:   http://localhost:8000")
    print(f" Network URL: http://{local_ip}:8000 (Share with colleagues on Wi-Fi)")
    print(" Keep this window open while using the application.")
    print(" Press Ctrl+C in this window to close.")
    print("==================================================================")

    # Automatically open browser
    threading.Thread(target=open_browser, daemon=True).start()

    # Run uvicorn server directly with app instance
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

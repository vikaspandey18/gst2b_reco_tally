import socket
import uvicorn

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("==================================================================")
    print(" Starting GST 2B & Tally Book Reconciliation Server (Offline)")
    print(f" Access locally on this PC:    http://localhost:8000")
    print(f" Access from other PC / Wi-Fi: http://{local_ip}:8000")
    print(" SQLite Database: storage/db/reco_offline.db")
    print(" Excel Exports:   storage/exports/")
    print("==================================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


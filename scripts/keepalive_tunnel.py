import subprocess
import time
import sys

port = sys.argv[1] if len(sys.argv) > 1 else "5173"

while True:
    print(f"Starting tunnel on port {port}...")
    try:
        proc = subprocess.Popen(["npx", "-y", "localtunnel", "--port", str(port)])
        proc.wait()
    except Exception as e:
        print(f"Tunnel process exception: {e}")
    print("Tunnel exited. Re-initiating in 3 seconds...")
    time.sleep(3)

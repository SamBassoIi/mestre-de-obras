"""AutoCroqui3D Main Application Runner.
Starts the local server and opens the application in your default web browser.
"""

import sys
import os
import webbrowser
import uvicorn

# Ensure the root project directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print("=" * 70)
    print("📐 AutoCroqui3D — Desenho Técnico 2 & Autodesk Inventor")
    print(f"🚀 Iniciando servidor em {url}")
    print("💡 Pressione CTRL+C no terminal para encerrar.")
    print("=" * 70)

    # Automatically open browser after 1 second
    try:
        import threading
        import time
        def open_browser():
            time.sleep(1.2)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()
    except Exception:
        pass

    uvicorn.run("server.app:app", host=host, port=port, log_level="info", reload=False)

if __name__ == "__main__":
    main()

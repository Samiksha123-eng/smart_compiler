"""
Smart Compiler Error Detective - Entrypoint Launcher
Starts backend server and opens web interface in the default browser.
Supports standard development mode and clean WSGI mode (zero warnings).
"""

import os
import sys
import webbrowser
from threading import Timer

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import app

def open_browser(port: int):
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    use_wsgi = "--wsgi" in sys.argv or "--clean" in sys.argv

    print("=" * 68)
    print(" 🚀 Smart Compiler Error Detective - Academic Project")
    print(f" 📡 Server Address: http://localhost:{port} (or http://127.0.0.1:{port})")
    print(" 🌐 The web interface will open automatically in your browser.")
    print(" ℹ️  Note: The 'development server' notice is normal for local projects.")
    print(" ⌨️  Press Ctrl+C in this terminal window to stop the server.")
    print("=" * 68)

    Timer(1.0, lambda: open_browser(port)).start()

    if use_wsgi:
        # Run using Python's built-in WSGI reference server (zero warnings)
        from wsgiref.simple_server import make_server
        print(f" [*] Running via standard WSGI server on port {port} (clean mode)...")
        httpd = make_server("127.0.0.1", port, app)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n [!] Server stopped.")
    else:
        # Standard Flask server
        app.run(host="127.0.0.1", port=port, debug=False)

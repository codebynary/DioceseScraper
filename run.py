import sys
import os
import time
import webbrowser
import threading

# Add the current directory to Python's sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.server import app

def open_browser():
    """Waits for the server to start, then opens the browser."""
    time.sleep(1.5)
    print("\nAbrindo painel de controle no navegador...")
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == '__main__':
    print("==================================================================")
    print("           DIOCESE SCRAPER - PAINEL DE CONTROLE INTELIGENTE        ")
    print("==================================================================")
    print("Servidor iniciando em: http://127.0.0.1:5000")
    print("Pressione CTRL+C para encerrar o programa.")
    
    # Start browser opener in a daemon thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask server without reloader to prevent double thread execution
    app.run(host="127.0.0.1", port=5000, debug=False)

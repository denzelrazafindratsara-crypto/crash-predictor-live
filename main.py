import os
import json
import math
import time
import threading
import websocket
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Configuration du stockage
DATA_FILE = "crash_history.csv"

# Initialisation du fichier CSV s'il n'existe pas
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("timestamp,multiplier,flight_time_ms\n")

def save_data(multiplier):
    """Calcule les ms et enregistre le crash dans le CSV"""
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        # Formule mathématique : ln(m) / 0.00006
        ms = round(math.log(float(multiplier)) / 0.00006) if float(multiplier) > 1 else 0
        
        with open(DATA_FILE, "a") as f:
            f.write(f"{ts},{multiplier},{ms}\n")
        print(f"✅ CRASH ENREGISTRÉ : {multiplier}x | {ms}ms")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")

def on_message(ws, message):
    """Traite les messages reçus du WebSocket"""
    try:
        payload = json.loads(message)
        # Structure type 'f' pour les données de vol (vu sur tes captures)
        if payload.get("type") == "f":
            data = payload.get("data", {})
            m = data.get("m") # Le multiplicateur
            s = data.get("s") # Le statut ('c' pour crash)
            
            if s == "c" and m is not None:
                save_data(m)
    except Exception as e:
        # On ne print que les erreurs graves pour ne pas polluer les logs
        pass

def on_error(ws, error):
    print(f"🚨 ERREUR WEBSOCKET : {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"🔌 CONNEXION FERMÉE : {close_msg} (Code: {close_status_code})")
    print("Tentative de reconnexion dans 5 secondes...")
    time.sleep(5)
    run_ws()

def run_ws():
    """Lance la connexion WebSocket avec déguisement et trace"""
    url = os.getenv("WS_URL")
    if not url:
        print("❌ ERREUR : La variable d'environnement WS_URL est vide !")
        return

    # Active le mode debug pour voir les détails de connexion dans les logs Railway
    websocket.enableTrace(True)

    # Déguisement en navigateur Chrome sur Android
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

    print(f"🚀 Tentative de connexion WebSocket...")
    
    ws = websocket.WebSocketApp(
        url,
        header=headers,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

@app.get("/")
def home():
    lines = 0
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            lines = len(f.readlines()) - 1
    return {
        "projet": "Crash Predictor Live",
        "status": "Running",
        "donnees_recoltees": lines,
        "note": "Rafraîchis cette page pour voir le compteur augmenter."
    }

if __name__ == "__main__":
    # 1. Lancement du WebSocket dans un thread séparé
    ws_thread = threading.Thread(target=run_ws, daemon=True)
    ws_thread.start()

    # 2. Lancement du serveur Web API
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

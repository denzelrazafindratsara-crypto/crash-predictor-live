import os
import json
import math
import time
import threading
import websocket
from fastapi import FastAPI

app = FastAPI()

# Nom du fichier où seront stockées tes données
DATA_FILE = "crash_history.csv"

# Initialisation du fichier CSV s'il n'existe pas
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("timestamp,multiplier,flight_time_ms\n")

def save_data(multiplier):
    """Calcule les ms et enregistre dans le CSV"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    # Ta formule : ln(m) / 0.00006
    ms = round(math.log(multiplier) / 0.00006) if multiplier > 1 else 0
    
    with open(DATA_FILE, "a") as f:
        f.write(f"{ts},{multiplier},{ms}\n")
    print(f" Enregistré : {multiplier}x | {ms}ms")

def on_message(ws, message):
    try:
        payload = json.loads(message)
        # Format détecté sur tes captures : type 'f'
        if payload.get("type") == "f":
            data = payload.get("data", {})
            m = data.get("m") # Multiplicateur
            s = data.get("s") # État (status)
            
            # Détection du crash : s == "c" d'après tes images
            if s == "c":
                save_data(m)
    except Exception as e:
        print(f"Erreur : {e}")

def run_ws():
    url = os.getenv("WS_URL")
    ws = websocket.WebSocketApp(url, on_message=on_message)
    ws.run_forever()

@app.get("/")
def status():
    # Permet de vérifier combien de lignes tu as récoltées
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            lines = len(f.readlines()) - 1
        return {"status": "Récolte en cours", "lignes_recoltees": lines}
    return {"status": "Fichier non trouvé"}

if __name__ == "__main__":
    import uvicorn
    threading.Thread(target=run_ws, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

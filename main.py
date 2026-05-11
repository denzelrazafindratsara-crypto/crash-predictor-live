import os, time, threading, websocket, json, sys, math
from fastapi import FastAPI
import uvicorn

# Fonction de log ultra-agressive pour forcer l'affichage sur Railway
def log(msg):
    print(f"DEBUG_BOT: {msg}", flush=True)
    sys.stdout.flush()

app = FastAPI()
DATA_FILE = "crash_history.csv"

# Initialisation du fichier CSV
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("timestamp,multiplier,flight_time_ms\n")
    log("Fichier CSV créé.")

def run_ws():
    url = os.getenv("WS_URL")
    if not url:
        log("ERREUR CRITIQUE: La variable WS_URL n'est pas configurée dans Railway !")
        return
    
    log(f"Connexion WebSocket lancée sur : {url[:20]}...")
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if data.get("type") == "f":
                res = data.get("data", {})
                if res.get("s") == "c": # Crash
                    m = res.get("m", 1.0)
                    ms = round(math.log(float(m)) / 0.00006) if float(m) > 1 else 0
                    with open(DATA_FILE, "a") as f:
                        f.write(f"{time.ctime()},{m},{ms}\n")
                    log(f"MATCH ENREGISTRÉ : {m}x")
        except Exception as e:
            pass

    # Déguisement pour éviter le blocage casino
    headers = {"User-Agent": "Mozilla/5.0 (Android 10; Mobile; rv:114.0) Gecko/114.0 Firefox/114.0"}
    
    ws = websocket.WebSocketApp(url, header=headers, on_message=on_message)
    ws.run_forever()

# --- C'EST ICI QUE CA SE JOUE POUR RAILWAY ---
@app.on_event("startup")
def startup_event():
    log("Le serveur Railway démarre... Lancement du thread WebSocket.")
    thread = threading.Thread(target=run_ws)
    thread.daemon = True
    thread.start()
    log("Thread WebSocket activé avec succès.")

@app.get("/")
def read_root():
    lines = 0
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            lines = len(f.readlines()) - 1
    return {"status": "OK", "recolte_actuelle": lines, "message": "Si 'recolte' est à 0, vérifie tes logs Railway."}

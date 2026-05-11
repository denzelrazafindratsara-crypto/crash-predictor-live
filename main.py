import os
import json
import math
import time
import threading
import websocket
from fastapi import FastAPI
import uvicorn
import sys

app = FastAPI()
DATA_FILE = "crash_history.csv"

# Forcer l'affichage des logs
def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("timestamp,multiplier,flight_time_ms\n")

def save_data(multiplier):
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        ms = round(math.log(float(multiplier)) / 0.00006) if float(multiplier) > 1 else 0
        with open(DATA_FILE, "a") as f:
            f.write(f"{ts},{multiplier},{ms}\n")
        log(f"✅ CRASH : {multiplier}x")
    except Exception as e:
        log(f"❌ Erreur save: {e}")

def on_message(ws, message):
    try:
        payload = json.loads(message)
        if payload.get("type") == "f":
            data = payload.get("data", {})
            m, s = data.get("m"), data.get("s")
            if s == "c" and m:
                save_data(m)
    except:
        pass

def run_ws():
    url = os.getenv("WS_URL")
    if not url:
        log("❌ WS_URL MANQUANT")
        return

    # On active le mode debug pour voir TOUT dans Railway
    websocket.enableTrace(True)
    
    # Extraction de l'origine (ex: https://monsite.com)
    # Très important pour que le casino accepte la connexion
    origin = url.replace("wss://", "https://").split("/")[0]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/114.0.0.0 Mobile Safari/537.36",
        "Origin": origin
    }

    log(f"🚀 CONNEXION EN COURS SUR : {url[:30]}...")
    
    ws = websocket.WebSocketApp(
        url,
        header=headers,
        on_message=on_message,
        on_error=lambda ws, e: log(f"🚨 ERR: {e}"),
        on_close=lambda ws, c, m: log("🔌 FERMÉ")
    )
    ws.run_forever()

@app.get("/")
def home():
    lines = 0
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            lines = len(f.readlines()) - 1
    return {"status": "online", "recolte": lines}

if __name__ == "__main__":
    threading.Thread(target=run_ws, daemon=True).start()
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

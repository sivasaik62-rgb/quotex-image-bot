import requests
import time
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import os

# ==============================
# TELEGRAM CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")  # Railway Variables lo TOKEN set cheyyi
BASE_URL = "https://api.telegram.org/bot" + TOKEN

# ==============================
# TELEGRAM HELPERS
# ==============================
def send_message(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def get_image(file_id):
    info = requests.get(
        BASE_URL + "/getFile",
        params={"file_id": file_id}
    ).json()
    path = info["result"]["file_path"]
    return requests.get(
        f"https://api.telegram.org/file/bot{TOKEN}/{path}"
    ).content

# ==============================
# IMAGE ANALYSIS (AGGRESSIVE)
# ==============================
def analyze_image(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = np.array(img)

    h, w, _ = img.shape

    # focus on right side (latest candles)
    crop = img[int(h*0.3):int(h*0.85), int(w*0.55):int(w*0.9)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Candle direction (brightness bias)
    avg = np.mean(gray)
    candle = "bullish" if avg > 138 else "bearish"

    # Wick / rejection (LOOSENED)
    edges = cv2.Canny(gray, 50, 150)
    edge_strength = np.mean(edges)

    wick = "strong" if edge_strength > 18 else "weak"

    return candle, wick

# ==============================
# AGGRESSIVE DECISION ENGINE
# ==============================
def aggressive_decide(candle, wick):
    if candle == "bullish":
        return (
            "📈 CALL\n\n"
            "Reason:\n"
            "• Bullish momentum detected\n"
            f"• Wick: {wick}\n"
            "• Aggressive continuation bias\n\n"
            "Risk: HIGH\n"
            "Entry: NEXT 1-minute candle"
        )

    if candle == "bearish":
        return (
            "📉 PUT\n\n"
            "Reason:\n"
            "• Bearish pressure detected\n"
            f"• Wick: {wick}\n"
            "• Aggressive pullback bias\n\n"
            "Risk: HIGH\n"
            "Entry: NEXT 1-minute candle"
        )

    return (
        "⛔ NO TRADE\n\n"
        "Reason:\n"
        "• Unclear structure\n"
        "Risk: HIGH"
    )

# ==============================
# MESSAGE HANDLER
# ==============================
def handle_message(message):
    chat_id = message["chat"]["id"]

    if "photo" in message:
        file_id = message["photo"][-1]["file_id"]
        img_bytes = get_image(file_id)

        candle, wick = analyze_image(img_bytes)
        decision = aggressive_decide(candle, wick)

        send_message(
            chat_id,
            f"🤖 AUTO IMAGE SIGNAL (1M) – AGGRESSIVE\n\n"
            f"Detected:\n"
            f"• Candle: {candle}\n"
            f"• Wick: {wick}\n\n"
            f"{decision}"
        )

# ==============================
# BOT LOOP
# ==============================
last_update_id = None
print("🔥 AUTO IMAGE BOT v4 AGGRESSIVE RUNNING...")

while True:
    updates = requests.get(
        BASE_URL + "/getUpdates",
        params={"offset": last_update_id}
    ).json()

    for update in updates.get("result", []):
        last_update_id = update["update_id"] + 1
        if "message" in update:
            handle_message(update["message"])

    time.sleep(1)


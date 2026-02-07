import requests
import time
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

# ==============================
# TELEGRAM CONFIG (HARDCODED)
# ==============================
TOKEN = "8501955227:AAG9nfxSoN84lLMp3D7wfSwIjwAuH69C3_U"
BASE_URL = f"https://api.telegram.org/bot{8501955227:AAG9nfxSoN84lLMp3D7wfSwIjwAuH69C3_U}"

# ==============================
# TELEGRAM FUNCTIONS
# ==============================
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def get_file_bytes(file_id):
    r = requests.get(f"{BASE_URL}/getFile", params={"file_id": file_id})
    file_path = r.json()["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    return requests.get(file_url).content

# ==============================
# IMAGE ANALYSIS (SIMPLE + AGGRESSIVE)
# ==============================
def analyze_image(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = np.array(img)

    h, w, _ = img.shape
    crop = img[int(h*0.35):int(h*0.85), int(w*0.55):int(w*0.9)]

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    avg = np.mean(gray)
    candle = "bullish" if avg > 135 else "bearish"

    edges = cv2.Canny(gray, 50, 150)
    strength = np.mean(edges)

    wick = "strong" if strength > 15 else "weak"

    return candle, wick

# ==============================
# SIGNAL LOGIC
# ==============================
def generate_signal(candle, wick):
    if candle == "bullish":
        return (
            "📈 CALL\n\n"
            "Reason:\n"
            "• Bullish momentum detected\n"
            f"• Wick: {wick}\n"
            "• Aggressive entry\n\n"
            "Entry: NEXT 1-minute candle\n"
            "Risk: HIGH"
        )

    if candle == "bearish":
        return (
            "📉 PUT\n\n"
            "Reason:\n"
            "• Bearish pressure detected\n"
            f"• Wick: {wick}\n"
            "• Aggressive entry\n\n"
            "Entry: NEXT 1-minute candle\n"
            "Risk: HIGH"
        )

# ==============================
# MAIN LOOP
# ==============================
print("🔥 AUTO IMAGE BOT v5 CLEAN RUNNING...")

offset = None

while True:
    updates = requests.get(
        f"{BASE_URL}/getUpdates",
        params={"offset": offset, "timeout": 30}
    ).json()

    for update in updates.get("result", []):
        offset = update["update_id"] + 1

        if "message" in update and "photo" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            file_id = update["message"]["photo"][-1]["file_id"]

            img_bytes = get_file_bytes(file_id)
            candle, wick = analyze_image(img_bytes)
            signal = generate_signal(candle, wick)

            send_message(
                chat_id,
                f"🤖 AUTO IMAGE SIGNAL (1M)\n\n"
                f"Detected:\n"
                f"• Candle: {candle}\n"
                f"• Wick: {wick}\n\n"
                f"{signal}"
            )

    time.sleep(1)




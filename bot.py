import requests
import time
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

# ==============================
# TELEGRAM CONFIG
# ==============================
TOKEN = "8501955227:AAG9nfxSoN84lLMp3D7wfSwIjwAuH69C3_U"
BASE_URL = "https://api.telegram.org/bot" + TOKEN

# ==============================
# TELEGRAM HELPERS
# ==============================
def send_message(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def download_image(file_id):
    r = requests.get(BASE_URL + "/getFile", params={"file_id": file_id})
    file_path = r.json()["result"]["file_path"]
    return requests.get(
        "https://api.telegram.org/file/bot" + TOKEN + "/" + file_path
    ).content

# ==============================
# IMAGE ANALYSIS – TREND MODE
# ==============================
def analyze_image(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = np.array(img)

    h, w, _ = img.shape

    # focus only chart area (right half)
    crop = img[int(h*0.35):int(h*0.85), int(w*0.45):int(w*0.9)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # split into past vs latest candles
    left = gray[:, :gray.shape[1]//2]
    right = gray[:, gray.shape[1]//2:]

    left_avg = np.mean(left)
    right_avg = np.mean(right)

    # TREND MODE DECISION
    if right_avg > left_avg:
        direction = "CALL"
    else:
        direction = "PUT"

    return direction

# ==============================
# BOT LOOP – EVERY CANDLE
# ==============================
print("🔥 EVERY CANDLE TREND BOT RUNNING...")

offset = None

while True:
    updates = requests.get(
        BASE_URL + "/getUpdates",
        params={"offset": offset, "timeout": 30}
    ).json()

    for update in updates.get("result", []):
        offset = update["update_id"] + 1

        if "message" in update and "photo" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            file_id = update["message"]["photo"][-1]["file_id"]

            img_bytes = download_image(file_id)
            decision = analyze_image(img_bytes)

            send_message(
                chat_id,
                "🤖 EVERY CANDLE SIGNAL (1M)\n\n"
                f"ACTION: {decision}\n\n"
                "Rule:\n"
                "• Trend-follow mode\n"
                "• Same direction for next candle\n\n"
                "Risk: HIGH\n"
                "Note: Fixed stake only"
            )

    time.sleep(1)

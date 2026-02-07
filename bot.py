import requests, time, cv2, numpy as np
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
# IMAGE ANALYSIS (AUTO)
# ==============================
def analyze_image(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = np.array(img)

    h, w, _ = img.shape
    crop = img[int(h*0.3):int(h*0.85), int(w*0.5):int(w*0.8)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Candle direction
    avg = np.mean(gray)
    candle = "bullish" if avg > 140 else "bearish"

    # Wick strength
    edges = cv2.Canny(gray, 50, 150)
    wick_strength = np.mean(edges)

    if wick_strength > 30:
        wick = "strong"
    else:
        wick = "weak"

    return candle, wick

# ==============================
# AUTO DECISION ENGINE
# ==============================
def auto_decide(candle, wick):
    if candle == "bullish" and wick == "strong":
        return (
            "📈 CALL\n\n"
            "Reason:\n"
            "• Bullish candle pressure\n"
            "• Strong rejection detected\n"
            "Entry: Next 1-minute candle\n"
            "Risk: MEDIUM"
        )

    if candle == "bearish" and wick == "strong":
        return (
            "📉 PUT\n\n"
            "Reason:\n"
            "• Bearish candle pressure\n"
            "• Strong rejection detected\n"
            "Entry: Next 1-minute candle\n"
            "Risk: MEDIUM"
        )

    return (
        "⛔ NO TRADE\n\n"
        "Reason:\n"
        "• Weak or unclear candle structure\n"
        "• High noise (1-minute TF)\n"
        "Risk: HIGH"
    )

# ==============================
# MESSAGE HANDLER
# ==============================
def handle_message(msg):
    chat_id = msg["chat"]["id"]

    if "photo" in msg:
        file_id = msg["photo"][-1]["file_id"]
        img = get_image(file_id)

        candle, wick = analyze_image(img)
        decision = auto_decide(candle, wick)

        send_message(
            chat_id,
            f"🤖 AUTO IMAGE SIGNAL (1M)\n\n"
            f"Detected:\n"
            f"• Candle: {candle}\n"
            f"• Wick: {wick}\n\n"
            f"{decision}"
        )

# ==============================
# BOT LOOP
# ==============================
last_update_id = None
print("🤖 AUTO IMAGE BOT v4 RUNNING...")

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

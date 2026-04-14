"""Currency detector Telegram bot.

Send a photo of an Indian currency note (₹200 or ₹500) and the bot
replies with the denomination + confidence overlaid on the image.
"""

import io
import logging
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

load_dotenv()

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MODEL_PATH = Path(__file__).parent / "model" / "best.pt"

_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
_LONG_POLL_TIMEOUT = 20
_CONFIDENCE_THRESHOLD = 0.50

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_model: YOLO | None = None


def _get_model() -> YOLO:
    global _model
    if _model is None:
        logger.info("Loading model from %s …", MODEL_PATH)
        _model = YOLO(str(MODEL_PATH))
        logger.info("Model loaded.")
    return _model


# ------------------------------------------------------------------ #
# Image annotation                                                     #
# ------------------------------------------------------------------ #

def _annotate(image_bytes: bytes, label: str) -> bytes:
    """Overlay label text on the image and return annotated JPEG bytes."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36
        )
    except Exception:
        font = ImageFont.load_default()

    padding = 10
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Dark background rectangle
    draw.rectangle(
        [padding, padding, padding + text_w + padding * 2, padding + text_h + padding * 2],
        fill=(0, 0, 0, 180),
    )
    # White text
    draw.text((padding * 2, padding * 2), label, fill="white", font=font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ------------------------------------------------------------------ #
# Telegram API helpers                                                 #
# ------------------------------------------------------------------ #

def _get_updates(offset: int) -> list[dict]:
    try:
        r = requests.get(
            f"{_API}/getUpdates",
            params={"offset": offset, "timeout": _LONG_POLL_TIMEOUT},
            timeout=_LONG_POLL_TIMEOUT + 5,
        )
        return r.json().get("result", [])
    except Exception:
        return []


def _send_text(chat_id: int, text: str) -> None:
    try:
        requests.post(
            f"{_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as exc:
        logger.error("send_message failed: %s", exc)


def _send_photo(chat_id: int, image_bytes: bytes, caption: str) -> None:
    try:
        requests.post(
            f"{_API}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption},
            files={"photo": ("result.jpg", image_bytes, "image/jpeg")},
            timeout=15,
        )
    except Exception as exc:
        logger.error("send_photo failed: %s", exc)


def _download_photo(file_id: str) -> bytes | None:
    try:
        r = requests.get(f"{_API}/getFile", params={"file_id": file_id}, timeout=10)
        file_path = r.json()["result"]["file_path"]
        img = requests.get(
            f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}",
            timeout=15,
        )
        return img.content
    except Exception as exc:
        logger.error("download_photo failed: %s", exc)
        return None


# ------------------------------------------------------------------ #
# Per-message handler                                                  #
# ------------------------------------------------------------------ #

def _handle_update(update: dict) -> None:
    msg = update.get("message", {})
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    if TELEGRAM_CHAT_ID and str(chat_id) != str(TELEGRAM_CHAT_ID):
        return

    photos = msg.get("photo", [])
    if not photos:
        return  # ignore non-photo messages

    image_bytes = _download_photo(photos[-1]["file_id"])
    if not image_bytes:
        _send_text(chat_id, "Failed to download your photo. Please try again.")
        return

    try:
        model = _get_model()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = model.predict(img, verbose=False)
        result = results[0]

        top1_idx = result.probs.top1
        top1_conf = float(result.probs.top1conf)
        class_name = result.names[top1_idx]  # e.g. "200" or "500"

        if top1_conf >= _CONFIDENCE_THRESHOLD:
            label = f"\u20b9{class_name} \u2014 {top1_conf:.0%}"
            annotated = _annotate(image_bytes, label)
            _send_photo(chat_id, annotated, caption=label)
            logger.info("Classified: %s (%.0f%%)", class_name, top1_conf * 100)
        else:
            _send_text(chat_id, "Could not identify \u2014 please send a clearer photo.")
            logger.info("Low confidence: %.0f%% for class %s", top1_conf * 100, class_name)

    except Exception as exc:
        logger.error("Inference failed: %s", exc)
        _send_text(chat_id, "Something went wrong. Please try again.")


# ------------------------------------------------------------------ #
# Main poll loop                                                       #
# ------------------------------------------------------------------ #

def main() -> None:
    if not TELEGRAM_TOKEN:
        raise EnvironmentError("TELEGRAM_TOKEN not set in .env")

    logger.info("Currency detector bot started. Waiting for photos …")
    offset = 0

    while True:
        try:
            updates = _get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                _handle_update(update)
        except Exception as exc:
            logger.error("Polling error: %s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()

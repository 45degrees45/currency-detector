# Currency Detector

Detects and classifies Indian currency notes using a custom-trained YOLOv8 model. Send a photo of a note to the Telegram bot and receive the denomination (e.g. ₹200, ₹500) with confidence score overlaid on the image.

**Stack:** Python · YOLOv8 (Ultralytics) · Telegram Bot API · Pillow · Jupyter Notebook

## Quick Start

```bash
cp .env.example .env          # add TELEGRAM_TOKEN + TELEGRAM_CHAT_ID
pip install -r requirements.txt
python bot.py                  # start the Telegram bot
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full component diagram.

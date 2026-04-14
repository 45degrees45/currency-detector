# Currency Detector — Design Spec
**Date:** 2026-04-14
**Status:** Approved

---

## Goal

A Telegram bot that accepts a photo of an Indian currency note and replies with the denomination and confidence score, overlaid on the original image.

**Phase 1 scope:** ₹200 and ₹500 notes only. Standalone project — not integrated into kensho yet.

---

## Architecture

```
Colab (training):
  dataset/train/200/ + dataset/train/500/
    → YOLOv8n-cls fine-tune
    → export best.pt

Local (inference):
  User sends photo to Telegram bot
    → bot.py loads best.pt
    → YOLO classify
    → PIL overlays label + confidence
    → bot sends annotated image back
```

---

## Components

### 1. Dataset
- Source: public Indian currency datasets from Kaggle or Roboflow
- Classes: `200`, `500`
- Minimum: 100–300 images per class
- Structure:
  ```
  dataset/
  ├── train/
  │   ├── 200/
  │   └── 500/
  └── val/
      ├── 200/
      └── 500/
  ```

### 2. Training Notebook (`train.ipynb`)
- Runs on Google Colab (free GPU)
- Downloads dataset, trains `yolov8n-cls.pt`
- Exports `best.pt` for download to local machine

### 3. Telegram Bot (`bot.py`)
- Built with `python-telegram-bot`
- Loads `model/best.pt` on startup
- On receiving any photo:
  - Runs YOLOv8 classification
  - If confidence ≥ 50%: overlays "₹500 — 94%" on image, sends back
  - If confidence < 50%: replies with text — *"Could not identify — please send a clearer photo"*
- No slash commands needed for Phase 1

---

## Project Structure

```
currency-detector/
├── bot.py
├── train.ipynb
├── model/
│   └── best.pt          # added after Colab training
├── requirements.txt
└── .env                 # TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
```

---

## Requirements

```
ultralytics
python-telegram-bot
Pillow
python-dotenv
```

---

## Success Criteria

- Bot correctly identifies ₹200 vs ₹500 with ≥ 85% accuracy on test photos
- Response includes annotated image with label and confidence
- Low-confidence photos return a clear fallback message

---

## Out of Scope (Phase 1)

- ₹10, ₹20, ₹50, ₹100, ₹2000 denominations
- Fake note detection
- Integration with kensho CCTV
- Bounding box detection (classification only)

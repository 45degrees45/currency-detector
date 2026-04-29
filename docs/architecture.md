# Architecture — Currency Detector

A YOLOv8-based Indian currency note classifier that accepts photos via a Telegram bot, runs local inference using trained model weights, and replies with the detected denomination and confidence overlaid on the image.

```mermaid
flowchart TD
    subgraph Training["Training (offline)"]
        DS[("dataset/\nTrain / Val / Test\nper denomination")]
        NB["train.ipynb\n(Ultralytics YOLOv8)"]
        DS --> NB
        NB --> W["model/best.pt\n(trained weights)"]
    end

    subgraph Bot["Telegram Bot (bot.py)"]
        direction TB
        USER["User sends\ncurrency photo"]
        TG["Telegram API\ngetUpdates · getFile\nsendMessage · sendPhoto"]
        DL["Download photo\nbytes"]
        YOLO["YOLOv8 classify\n(Ultralytics)"]
        ANN["Annotate image\n(PIL — label + confidence)"]
        REPLY["Send annotated\nphoto back to user"]

        USER -->|"photo message"| TG
        TG -->|"long-poll updates"| DL
        DL --> YOLO
        W -->|"load on first call"| YOLO
        YOLO -->|"top1 class + confidence"| ANN
        ANN --> REPLY
        REPLY -->|"sendPhoto"| TG
        TG -->|"annotated JPEG + caption"| USER
    end

    subgraph DevServer["Dev Server (serve.py)"]
        HTTP["HTTP server :9999\nmarkdown renderer\n+ file upload"]
    end

    ENV[".env\nTELEGRAM_TOKEN\nTELEGRAM_CHAT_ID"]
    ENV --> Bot
```

## Components

| File | Role |
|------|------|
| `bot.py` | Telegram long-poll bot — downloads photos, runs inference, annotates and replies |
| `model/best.pt` | YOLOv8 classification weights trained on Indian currency notes |
| `train.ipynb` | Training notebook — loads dataset, trains YOLOv8, exports `best.pt` |
| `indian-currency-notes-classification.ipynb` | Exploratory classification notebook |
| `serve.py` | Local HTTP dev server (port 9999) for browsing project files and uploading images |
| `dataset/` | Train / Val / Test images organised by denomination subfolder |
| `.env` | `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` secrets |

# Lab 7 - Corporate Communication Web App

Python web application for Lab 7. The app supports scheduled meetings,
participant invitations, general and private chats, file sharing, embedded
LiveKit meetings, recording metadata, and basic notifications.

## Stack

- FastAPI
- Jinja2 + HTMX + small vanilla JS
- SQLAlchemy + SQLite
- local file storage for chat attachments
- pytest

## Run

```bash
cd Lab7
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LIVEKIT_URL=ws://localhost:7880
export LIVEKIT_API_KEY=your_api_key
export LIVEKIT_API_SECRET=your_api_secret
python main.py
```

Open `http://127.0.0.1:8000`.

## Docker

One-command local start:

```bash
cd Lab7
make up
```

This starts:

- the FastAPI web app on `http://127.0.0.1:18000`
- a local LiveKit server in dev mode on `ws://127.0.0.1:7880`

For the lab setup, Docker Compose uses LiveKit's local dev credentials:

- `LIVEKIT_API_KEY=devkey`
- `LIVEKIT_API_SECRET=secret`

Stop the stack:

```bash
cd Lab7
make down
```

## Demo Accounts

- `alice` / `alice123`
- `bob` / `bob123`
- `carol` / `carol123`

## Tests

```bash
cd Lab7
make test
```

## LiveKit

The meeting room now uses the LiveKit SDK instead of an embed-only provider.
To make video calls work locally you need a running LiveKit server or LiveKit Cloud
project plus these environment variables:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

## Team Split

The project is intentionally divided into 3 defense zones:

- Person 1:
  - backend architecture, DB, repositories, auth, meetings, invitations.
- Person 2:
  - chats, WebSocket realtime, file uploads, notifications.
- Person 3:
  - UI/templates, page UX, LiveKit integration, browser-side meeting flow.

Detailed defense-oriented documentation:

- [DEFENSE_GUIDE.md](/home/zikkurat/dev/ookp/Lab7/docs/DEFENSE_GUIDE.md:1)

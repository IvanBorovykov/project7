# Lab 7 Defense Guide

## Project Goal

`Lab7` is a corporate communication web application built for the lab work on
architectural and design patterns. The system combines:

- scheduled online meetings;
- participant invitations and attendance statuses;
- public and private chats;
- file sharing in chats;
- video meetings through `LiveKit`;
- recording metadata for meetings;
- notifications and recent activity.

## Architecture

The project uses a layered structure:

- Presentation layer:
  - FastAPI page routes
  - FastAPI API routes
  - WebSocket endpoints
  - Jinja templates and small browser-side JavaScript
- Application layer:
  - auth service
  - meetings service
  - chat service
  - notification service
  - LiveKit integration service
- Data layer:
  - SQLAlchemy models
  - repository classes
  - SQLite persistence

## Patterns Used

- `Repository`
  - isolates queries and persistence operations from route handlers.
- `Service Layer`
  - keeps business logic out of the HTTP layer.
- `Facade`
  - `LiveKitFacade` hides token generation and room config details.
- `Observer-like notifications`
  - application events create in-app notifications for invites and private messages.
- `Strategy`
  - local file storage is isolated behind a dedicated storage service.

## Main Functional Scenarios

1. User logs in with a seeded demo account.
2. Organizer creates a meeting and invites participants.
3. Invited user accepts or declines the invite.
4. Users open a private or general chat and exchange messages/files.
5. Users open the meeting page and join the LiveKit room.
6. Organizer stores recording status and external recording link metadata.

## Team Responsibility Split

### Person 1: Core Backend And Scheduling

Owns:

- database schema and SQLAlchemy models;
- repositories;
- authentication/session flow;
- meeting creation, validation, invitation rules, participation statuses;
- meeting recording metadata logic.

Defends:

- application architecture;
- persistence layer;
- validation rules;
- business logic for meetings and invitations.

Key files:

- `app/models.py`
- `app/database.py`
- `app/repositories/*`
- `app/services/meetings.py`
- `app/services/auth.py`

### Person 2: Realtime Chat And File Exchange

Owns:

- general and private chat logic;
- WebSocket message broadcasting;
- notification broadcasting;
- file upload validation and storage;
- chat persistence and attachment linking.

Defends:

- realtime flow;
- chat lifecycle;
- file exchange behavior;
- notification delivery flow.

Key files:

- `app/services/chats.py`
- `app/services/files.py`
- `app/ws/manager.py`
- `app/routes/ws.py`
- chat-related route handlers in `app/routes/api.py`

### Person 3: Web UI And Video Integration

Owns:

- Jinja templates and page UX;
- browser-side JavaScript for chat and LiveKit room control;
- LiveKit room integration and participant token flow;
- visual presentation of dashboard, meetings, chats, and profile pages.

Defends:

- frontend flow;
- page interactions;
- LiveKit meeting integration;
- end-to-end user scenario demonstration.

Key files:

- `app/templates/*`
- `app/static/css/app.css`
- `app/static/js/chat.js`
- `app/static/js/notifications.js`
- `app/static/js/livekit-room.js`
- `app/services/livekit.py`

## Recommended Defense Flow

1. Show login with demo user.
2. Open dashboard and explain main modules.
3. Create a meeting and invite two users.
4. Log in as invited user and accept the meeting.
5. Open private chat and send a message with a file.
6. Show notification creation.
7. Open meeting page and show LiveKit controls.
8. Explain recording metadata flow.
9. Point to tests and Docker launch flow.

## Local Launch

### Docker

```bash
cd Lab7
make up
```

Application URL:

- `http://127.0.0.1:18000`

Stop:

```bash
make down
```

### Tests

```bash
cd Lab7
make test
```

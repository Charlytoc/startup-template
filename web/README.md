## Web Realtime Demo

This Next.js app mirrors the minimal mobile flow:

- auth against Django (`/api/auth/login`, `/api/auth/signup`)
- send messages to `POST /api/agentic-chat/messages`
- receive async responses over Socket.IO (`agentic-chat-message`)

## Setup

1) Copy env template:

```bash
cp .env.local.example .env.local
```

2) Ensure backend stack is running:

- Django API on `http://localhost:8000`
- Realtime service on `http://localhost:3001`

3) Start web app:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

# LiveKit Demo Project 🚀

A complete demonstration of a Real-Time Video/Audio application using LiveKit.

## 📂 Project Structure

- **`installer/`**: Scripts to setup LiveKit Server (local or prod).
- **`backend/`**: NestJS API for generating Access Tokens.
- **`frontend/`**: Next.js 15 application for video conferencing.
- **`agent/`**: Python AI Agent (Voice Pipeline with OpenAI/Silero).

## 🛠️ Prerequisites

- Docker & Docker Compose
- Node.js (v18+)
- Python (3.9+)

---

## 🚀 Quick Start

### 1. Start LiveKit Server
Use the installer script to spin up a local LiveKit instance.

```bash
cd installer
./install.sh
# Select option [1] for Dev Mode
```
*   **Server URL**: `ws://localhost:7880`
*   **API Key**: `devkey`
*   **API Secret**: `secret`

### 2. Start Backend (API)
The backend generates tokens for the frontend.

```bash
cd backend
npm install
npm run start:dev
```
*   Running on: `http://localhost:3000`

### 3. Start Frontend (Client)
The web interface to join rooms.

```bash
cd frontend
npm install
npm run dev
```
*   Running on: `http://localhost:3001` (or 3000 if backend isn't blocking, but usually 3001)

### 4. Run AI Agent (Optional)
A voice assistant that joins the room.

```bash
cd agent
./install.sh      # Setup venv and install dependencies
./venv/bin/python agent.py start
```

## 🔧 Configuration

### Backend (`backend/.env`)
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### Frontend (`frontend/.env`)
```env
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_API_URL=http://localhost:3000
```

### Agent (`agent/.env` - Create if needed)
You may need to set OpenAI API keys for the agent to work.
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=sk-proj-...
```
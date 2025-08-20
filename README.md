# simple-mcp-server
# 🧠 Simple MCP Server with React Frontend

This is a beginner-friendly implementation of a Model Context Protocol (MCP)-style server with a React + Tailwind + shadcn/ui frontend. It demonstrates how to build and test context-aware, tool-augmented interactions with LLMs.

---

## 🚀 Features

- 🧠 MCP-style FastAPI server
- 🔢 Built-in calculator tool routing
- 👤 User-specific context + permissions
- 🧑‍💻 React + Vite frontend (w/ Tailwind & shadcn/ui)
- 🌐 LLM integration via OpenAI (GPT-4)

---

## 📦 Backend Setup (Python)

### Requirements
- Python 3.9+
- `openai`, `fastapi`, `uvicorn`, `pydantic`

### Install & Run
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
export OPENAI_API_KEY=your-openai-key  # Or set it in code (not recommended)
uvicorn mcp_server:app --reload
```

### Example API Request
```json
{
  "user_id": "user123",
  "task": "calculate 3 + 7 * 2",
  "use_tools": true
}
```

### Example Response
```json
{
  "tool_used": "calculator",
  "result": "17"
}
```

---

## 💻 Frontend Setup (Vite + React)

### Install
```bash
cd mcp-client
npm install
npm run dev
```

### Tailwind + shadcn/ui Setup
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Configure `tsconfig.json`:
"baseUrl": ".",
"paths": { "@/*": ["src/*"] }

# Vite alias (vite.config.ts):
import path from "path";
resolve: {
  alias: {
    "@": path.resolve(__dirname, "./src")
  }
}

# Add shadcn/ui components
npx shadcn@latest init
npx shadcn@latest add card button input
```

---

## 🧠 Folder Structure
```
.
├── backend/
│   └── mcp_server.py
├── mcp-client/
│   ├── src/
│   │   ├── MCPClient.tsx
│   │   └── App.tsx
│   └── tailwind.config.js
```

---

## ✨ Roadmap Ideas
- [ ] Add more tools (e.g. weather, todo, code runner)
- [ ] Multi-user profiles / auth
- [ ] Memory + session history
- [ ] Streaming LLM responses
- [ ] Deployment (Render + Vercel)

---


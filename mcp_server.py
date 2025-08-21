from fastapi import FastAPI, Request
from pydantic import BaseModel
import openai
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import re
import math
import ast
import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # loads .env from current working directory

# ---------- API Keys (via environment) ----------
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# ---------- App ----------
app = FastAPI(title="Simple MCP-style Server (Tools Expanded)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- In-memory context / permissions / state ----------
USER_CONTEXTS = {
    "user123": {"name": "Abhiram", "role": "Software Engineer", "project": "Simple MCP Server"},
    "guest":   {"name": "Guest", "role": "Viewer"},
    "admin42": {"name": "Admin", "role": "Admin"},
}

# Granular tool permissions by user
USER_PERMISSIONS = {
    "user123": [
        "tool:calculator",
        "tool:weather",
        "tool:stocks",
        "tool:todo",
        "tool:code_eval",
        "llm:fallback",
    ],
    "guest": [
        "tool:calculator",
        "tool:weather",      # mock weather only
    ],
    "admin42": [
        "tool:calculator",
        "tool:weather",
        "tool:stocks",
        "tool:todo",
        "tool:code_eval",
        "tool:weather_real", # real APIs
        "tool:stocks_real",  # real APIs
        "llm:fallback",
    ],
}

# Per-user todo lists
USER_TODOS = {uid: [] for uid in USER_CONTEXTS.keys()}

# ---------- Request schema ----------
class MCPRequest(BaseModel):
    use_tools: bool = True
    user_id: str
    task: str

# ---------- Safe math evaluator used by calculator/code_eval ----------
ALLOWED_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
ALLOWED_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
    ast.USub, ast.UAdd, ast.Call, ast.Name, ast.Tuple, ast.List,
}

def safe_eval(expr: str):
    node = ast.parse(expr, mode="eval")
    def _eval(n):
        if type(n) not in ALLOWED_NODES:
            raise ValueError(f"Disallowed expression: {type(n).__name__}")
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Num):
            return n.n
        if isinstance(n, ast.BinOp):
            left, right = _eval(n.left), _eval(n.right)
            if isinstance(n.op, ast.Add): return left + right
            if isinstance(n.op, ast.Sub): return left - right
            if isinstance(n.op, ast.Mult): return left * right
            if isinstance(n.op, ast.Div): return left / right
            if isinstance(n.op, ast.Pow): return left ** right
            if isinstance(n.op, ast.Mod): return left % right
            if isinstance(n.op, ast.FloorDiv): return left // right
            raise ValueError("Unsupported binary operator")
        if isinstance(n, ast.UnaryOp):
            val = _eval(n.operand)
            if isinstance(n.op, ast.UAdd): return +val
            if isinstance(n.op, ast.USub): return -val
            raise ValueError("Unsupported unary operator")
        if isinstance(n, ast.Name):
            if n.id in ALLOWED_NAMES: return ALLOWED_NAMES[n.id]
            raise ValueError(f"Unknown name: {n.id}")
        if isinstance(n, ast.Call):
            func = _eval(n.func)
            args = [_eval(a) for a in n.args]
            return func(*args)
        if isinstance(n, (ast.Tuple, ast.List)):
            return [_eval(e) for e in n.elts]
        raise ValueError("Unsupported expression node")
    return _eval(node)

# ---------- Tools ----------
# Calculator: wraps safe_eval to return structured output
def tool_calculator(payload: str):
    expr = payload.strip()
    try:
        return {"tool": "calculator", "input": expr, "result": str(safe_eval(expr))}
    except Exception as e:
        return {"tool": "calculator", "input": expr, "error": str(e)}

# Mock weather
MOCK_WEATHER = {
    "detroit": {"temp_c": 22, "conditions": "Partly cloudy"},
    "mumbai": {"temp_c": 29, "conditions": "Humid, chance of showers"},
    "san francisco": {"temp_c": 18, "conditions": "Foggy AM, sunny PM"},
}
def tool_weather(city: str):
    key = city.lower().strip()
    data = MOCK_WEATHER.get(key)
    if not data:
        return {"tool": "weather", "city": city, "error": "City not found in mock data"}
    return {"tool": "weather", "city": city, "data": data}

# Real weather (OpenWeatherMap)
def tool_weather_real(city: str):
    if not OPENWEATHER_API_KEY:
        return {"tool": "weather_real", "error": "OPENWEATHER_API_KEY not set"}
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            )
            r.raise_for_status()
            data = r.json()
        out = {
            "city": city,
            "temp_c": data.get("main", {}).get("temp"),
            "conditions": (data.get("weather") or [{}])[0].get("description"),
            "wind_mps": data.get("wind", {}).get("speed"),
        }
        return {"tool": "weather_real", "data": out}
    except httpx.HTTPError as e:
        return {"tool": "weather_real", "city": city, "error": str(e)}

# Mock stocks
MOCK_STOCKS = {
    "AAPL": 228.42,
    "MSFT": 456.13,
    "GOOGL": 176.05,
}
def tool_stocks(ticker: str):
    t = ticker.upper().strip()
    price = MOCK_STOCKS.get(t)
    if price is None:
        return {"tool": "stocks", "ticker": t, "error": "Ticker not found in mock data"}
    return {"tool": "stocks", "ticker": t, "price": price}

# Real stocks (Alpha Vantage GLOBAL_QUOTE)
def tool_stocks_real(ticker: str):
    if not ALPHAVANTAGE_API_KEY:
        return {"tool": "stocks_real", "error": "ALPHAVANTAGE_API_KEY not set"}
    t = ticker.upper().strip()
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": t, "apikey": ALPHAVANTAGE_API_KEY},
            )
            r.raise_for_status()
            data = r.json().get("Global Quote", {})
        if not data:
            return {"tool": "stocks_real", "ticker": t, "error": "No quote returned"}
        out = {
            "ticker": t,
            "price": float(data.get("05. price")) if data.get("05. price") else None,
            "change": float(data.get("09. change")) if data.get("09. change") else None,
            "percent_change": data.get("10. change percent"),
        }
        return {"tool": "stocks_real", "data": out}
    except httpx.HTTPError as e:
        return {"tool": "stocks_real", "ticker": t, "error": str(e)}

# Todo
def tool_todo(user_id: str, command: str):
    USER_TODOS.setdefault(user_id, [])
    cmd = command.strip()
    if cmd.startswith("add "):
        item = cmd[4:].strip()
        USER_TODOS[user_id].append(item)
        return {"tool": "todo", "action": "add", "item": item, "list": USER_TODOS[user_id]}
    if cmd == "list":
        return {"tool": "todo", "action": "list", "list": USER_TODOS[user_id]}
    if cmd == "clear":
        USER_TODOS[user_id] = []
        return {"tool": "todo", "action": "clear", "list": USER_TODOS[user_id]}
    return {"tool": "todo", "error": "Commands: 'todo add <text>', 'todo list', 'todo clear'"}

# Code eval (math-only)
def tool_code_eval(code: str):
    try:
        result = safe_eval(code)
        return {"tool": "code_eval", "input": code, "result": result}
    except Exception as e:
        return {"tool": "code_eval", "input": code, "error": str(e)}

# LLM fallback (only if permitted)
def tool_llm_fallback(user_ctx: dict, task: str):
    if not openai.api_key:
        return {"tool": "llm_fallback", "error": "OPENAI_API_KEY not set"}
    system = (
        "You are a helpful assistant. Use the provided user context when relevant. "
        "If the task seems to require tools, explain what tool would be appropriate."
    )
    context_lines = [f"{k}: {v}" for k, v in user_ctx.items()]
    user_prompt = "User Context:\n" + "\n".join(context_lines) + f"\n\nTask:\n{task}"
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user_prompt}],
        )
        content = resp.choices[0].message["content"]
        return {"tool": "llm_fallback", "answer": content}
    except Exception as e:
        return {"tool": "llm_fallback", "error": str(e)}

# ---------- Registry ----------
TOOL_REGISTRY = {
    "calculator":  tool_calculator,
    "weather":     tool_weather,
    "weather_real": tool_weather_real,
    "stocks":      tool_stocks,
    "stocks_real": tool_stocks_real,
    "todo":        tool_todo,
    "code_eval":   tool_code_eval,
}

# ---------- Router (explicit + implicit) ----------
EXPLICIT_SYNTAX = re.compile(r"^use\s+([a-z_]+)\s*:\s*(.+)$", re.IGNORECASE)

def route_task(user_id: str, task: str):
    """
    Explicit:  'use weather: Detroit', 'use weather_real: Mumbai', 'use stocks_real: AAPL'
    Implicit:  'weather in Detroit', 'stock price AAPL',
               'calculate 2*(3+4)', 'todo add buy milk', 'python: sin(pi/2)'
    """
    t = task.strip()

    # 1) Explicit
    m = EXPLICIT_SYNTAX.match(t)
    if m:
        tool, payload = m.group(1).lower(), m.group(2)
        return tool, payload

    # 2) Implicit patterns
    if t.lower().startswith("python:"):
        return "code_eval", t.split(":", 1)[1]
    if t.lower().startswith("calculate"):
        return "calculator", t.split("calculate", 1)[1]
    if t.lower().startswith("todo "):
        return "todo", t[5:]

    m = re.search(r"weather\s+(?:in|for)\s+(.+)", t, re.IGNORECASE)
    if m:
        return "weather", m.group(1)

    m = re.search(r"stock\s+price\s+([A-Za-z.]+)", t, re.IGNORECASE)
    if m:
        return "stocks", m.group(1)

    # calculator fallback if it looks like math
    if re.fullmatch(r"[\d\s+\-*/%().^]+", t):
        return "calculator", t

    return None, None

# ---------- Endpoint ----------
@app.post("/mcp")
def handle_request(req: MCPRequest):
    user_ctx = USER_CONTEXTS.get(req.user_id, {})
    perms = set(USER_PERMISSIONS.get(req.user_id, []))

    if not req.use_tools:
        return {"error": "Tool usage disabled for this request"}

    tool_name, payload = route_task(req.user_id, req.task)

    # No matching tool → LLM fallback if allowed
    if tool_name is None:
        if "llm:fallback" in perms:
            out = tool_llm_fallback(user_ctx, req.task)
            out.update({"user": req.user_id, "context": user_ctx})
            return out
        return {
            "error": ("No matching tool. Try: "
                      "'use weather: Detroit', 'use weather_real: Detroit', "
                      "'stock price AAPL', 'use stocks_real: AAPL', "
                      "'todo add buy milk', 'calculate 2*(3+4)', or 'python: sin(pi/2)'.")
        }

    # Permission check
    if f"tool:{tool_name}" not in perms:
        return {"error": f"User not permitted to use tool '{tool_name}'"}

    # Execute tool
    if tool_name == "todo":
        out = TOOL_REGISTRY[tool_name](req.user_id, payload)
    else:
        out = TOOL_REGISTRY[tool_name](payload)

    # Attach context for observability
    out.update({"user": req.user_id, "context": user_ctx})
    return out

# ---------- Main ----------
if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="127.0.0.1", port=8000, reload=True)

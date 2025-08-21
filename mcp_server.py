from fastapi import FastAPI, Request
from pydantic import BaseModel
import openai
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Simple MCP-style Server (Tools Expanded)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Simulated in-memory storage for context and permissions ---
USER_CONTEXTS = {
    "user123": {
        "name": "Abhiram",
        "role": "Software Engineer",
        "project": "Simple MCP Server"
    }
}

# --- Simulated in-memory storage for permissions ---
USER_PERMISSIONS = {
# Grant access to specific tools per user
    "user123": [
        "tool:calculator",
        "tool:weather",
        "tool:stocks",
        "tool:todo",
        "tool:code_eval",
        # "llm:fallback", # uncomment if you wire up an LLM fallback
    ]
}

class MCPRequest(BaseModel):
    # --- Request schema ---
    use_tools: bool = True # keep default on for the playground
    user_id: str
    task: str

# Safe arithmetic evaluator (supports + - * / ** // % parentheses and math.*)
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

# Mock weather tool
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


# Mock stocks tool
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


# Simple TODO manager
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



# ======================
# API Endpoint
# ======================


@app.post("/mcp")
def handle_request(req: MCPRequest):
    user_ctx = USER_CONTEXTS.get(req.user_id, {})
    perms = set(USER_PERMISSIONS.get(req.user_id, []))


    if not req.use_tools:
        return {"error": "Tool usage disabled for this request"}


tool_name, payload = route_task(req.user_id, req.task)


if tool_name is None:
    # Optional: send to an LLM fallback if permitted
    if "llm:fallback" in perms:
        return {"note": "No matching tool; would route to LLM here."}
    return {"error": "No matching tool. Try: 'use weather: Detroit', 'weather in Mumbai', 'stock price AAPL', 'todo add buy milk', 'calculate 2*(3+4)', or 'python: sin(pi/2)'."}


if f"tool:{tool_name}" not in perms:
    return {"error": f"User not permitted to use tool '{tool_name}'"}


# Execute tool
if tool_name == "todo":
    out = TOOL_REGISTRY[tool_name](req.user_id, payload)
else:
    out = TOOL_REGISTRY[tool_name](payload)


# Attach minimal context echo for observability
out.update({"user": req.user_id, "context": user_ctx})
return out


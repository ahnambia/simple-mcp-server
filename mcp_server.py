from fastapi import FastAPI, Request
from pydantic import BaseModel
import openai
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
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
    "user123": ["basic_model", "tool:calculator"]
}

# --- Define the input format for the MCP server ---
class MCPRequest(BaseModel):
    user_id: str
    task: str
    use_tools: bool = False


# --- Tool registry example ---
def simple_calculator(expr: str):
    try:
        return str(eval(expr))
    except:
        return "Invalid expression"

# --- Route: Main endpoint to process LLM tasks ---
@app.post("/mcp")
def handle_request(req: MCPRequest):
    user_ctx = USER_CONTEXTS.get(req.user_id, {})
    permissions = USER_PERMISSIONS.get(req.user_id, [])


    context_lines = [f"{key}: {value}" for key, value in user_ctx.items()]
    context_str = "\n".join(context_lines)


    # If tools are allowed and requested, offer tool context
    tool_instructions = ""
    if req.use_tools and "tool:calculator" in permissions:
        tool_instructions = "\nYou may use a calculator tool. Example: 'calculate 5+3*2'."

    prompt = f"""
You are a helpful assistant.
User context:
{context_str}
{tool_instructions}


User task: {req.task}
"""

    # --- Process the request using OpenAI ---
    # Simulate tool handling if calculator is explicitly called
    if "calculate" in req.task.lower() and req.use_tools:
        expr = req.task.lower().split("calculate")[-1].strip()
        result = simple_calculator(expr)
        return {"tool_used": "calculator", "result": result}


    # Otherwise, route to OpenAI (you must have an API key set up)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )


    return {"response": response.choices[0].message["content"]}

# --- Run the FastAPI server ---
if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="127.0.0.1", port=8000, reload=True)
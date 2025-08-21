import { useState } from "react";
import axios from "axios";

// shadcn/ui
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type ApiResponse = Record<string, any>;

const USERS = [
  { id: "guest", label: "Guest (limited)" },
  { id: "user123", label: "User123 (standard)" },
  { id: "admin42", label: "Admin42 (all tools)" },
];

const EXAMPLES: { label: string; value: string }[] = [
  { label: "Calc", value: "calculate 2*(3+4)" },
  { label: "Weather (mock)", value: "weather in Mumbai" },
  { label: "Stocks (mock)", value: "stock price AAPL" },
  { label: "TODO add", value: "todo add read MCP spec" },
  { label: "TODO list", value: "todo list" },
  { label: "Python math", value: "python: sin(pi/2)" },
  { label: "Weather (real)", value: "use weather_real: Detroit" },
  { label: "Stocks (real)", value: "use stocks_real: AAPL" },
  { label: "LLM fallback", value: "Write a one-sentence project status based on my context." },
];

export default function MCPClient() {
  const [userId, setUserId] = useState("user123");
  const [useTools, setUseTools] = useState(true);
  const [task, setTask] = useState("");
  const [response, setResponse] = useState<ApiResponse | null>(null);
  const [raw, setRaw] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string>("");

  const sendRequest = async () => {
    setLoading(true);
    setErrorText("");
    setResponse(null);
    setRaw("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/mcp", {
        user_id: userId,
        task,
        use_tools: useTools,
      });
      setResponse(res.data);
      setRaw(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setErrorText(err?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const renderPretty = (data: ApiResponse | null) => {
    if (!data) return null;

    const tool = data.tool || data.tool_used;
    const note = data.note;
    const error = data.error;

    // Common pretty views
    if (error) {
      return (
        <div className="text-red-600 text-sm">
          <strong>Error:</strong> {String(error)}
        </div>
      );
    }

    if (tool === "calculator") {
      return (
        <div className="text-sm">
          <div><strong>Tool:</strong> calculator</div>
          <div><strong>Input:</strong> {String(data.input)}</div>
          <div><strong>Result:</strong> {String(data.result)}</div>
        </div>
      );
    }

    if (tool === "code_eval") {
      return (
        <div className="text-sm">
          <div><strong>Tool:</strong> code_eval</div>
          <div><strong>Input:</strong> {String(data.input)}</div>
          <div><strong>Result:</strong> {String(data.result)}</div>
        </div>
      );
    }

    if (tool === "todo") {
      return (
        <div className="text-sm">
          <div><strong>Tool:</strong> todo</div>
          {data.action && <div><strong>Action:</strong> {String(data.action)}</div>}
          {data.item && <div><strong>Item:</strong> {String(data.item)}</div>}
          {Array.isArray(data.list) && (
            <div><strong>List:</strong> {data.list.join(", ") || "(empty)"} </div>
          )}
        </div>
      );
    }

    if (tool === "weather" || tool === "weather_real") {
      const d = data.data || {};
      return (
        <div className="text-sm">
          <div><strong>Tool:</strong> {tool}</div>
          <div><strong>City:</strong> {String(d.city || data.city || "(n/a)")}</div>
          <div><strong>Temp (°C):</strong> {String(d.temp_c ?? "(n/a)")}</div>
          <div><strong>Conditions:</strong> {String(d.conditions ?? "(n/a)")}</div>
          {"wind_mps" in d && <div><strong>Wind (m/s):</strong> {String(d.wind_mps)}</div>}
        </div>
      );
    }

    if (tool === "stocks" || tool === "stocks_real") {
      const d = data.data || {};
      return (
        <div className="text-sm">
          <div><strong>Tool:</strong> {tool}</div>
          <div><strong>Ticker:</strong> {String(d.ticker || data.ticker || "(n/a)")}</div>
          <div><strong>Price:</strong> {String(d.price ?? data.price ?? "(n/a)")}</div>
          {"change" in d && <div><strong>Change:</strong> {String(d.change)}</div>}
          {"percent_change" in d && <div><strong>% Change:</strong> {String(d.percent_change)}</div>}
        </div>
      );
    }

    if (tool === "llm_fallback") {
      return (
        <div className="text-sm">
          <div><strong>Tool:</strong> llm_fallback</div>
          <div className="mt-1 whitespace-pre-wrap">{String(data.answer || "")}</div>
        </div>
      );
    }

    if (note) {
      return <div className="text-sm">{String(note)}</div>;
    }

    // Default: raw JSON fallback
    return (
      <pre className="whitespace-pre-wrap text-sm bg-muted p-2 rounded">
        {raw}
      </pre>
    );
  };

  return (
    <div className="max-w-xl mx-auto mt-10 space-y-4">
      <Card>
        <CardContent className="p-4 space-y-3">
          <h2 className="text-xl font-semibold">🧠 MCP Task Tester</h2>

          {/* User + Use Tools */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">User:</label>
              <select
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="border rounded px-2 py-1"
              >
                {USERS.map((u) => (
                  <option key={u.id} value={u.id}>{u.label}</option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useTools}
                onChange={(e) => setUseTools(e.target.checked)}
              />
              Use tools
            </label>
          </div>

          {/* Examples */}
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setTask(ex.value)}
                className="text-xs border rounded px-2 py-1 hover:bg-accent"
                type="button"
              >
                {ex.label}
              </button>
            ))}
          </div>

          {/* Task input */}
          <Input
            placeholder="Type your task (e.g. use weather_real: Detroit)"
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />

          <Button onClick={sendRequest} disabled={loading || !task.trim()}>
            {loading ? "Processing..." : "Send to MCP Server"}
          </Button>

          {errorText && (
            <div className="text-sm text-red-600">Error: {errorText}</div>
          )}
        </CardContent>
      </Card>

      {response && (
        <Card>
          <CardContent className="p-4 space-y-2">
            <h3 className="font-medium mb-1">Response</h3>
            {renderPretty(response)}
            {/* Always show raw for debugging */}
            <details className="mt-2">
              <summary className="text-sm cursor-pointer">Raw JSON</summary>
              <pre className="whitespace-pre-wrap text-xs bg-muted p-2 rounded mt-1">
                {raw}
              </pre>
            </details>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

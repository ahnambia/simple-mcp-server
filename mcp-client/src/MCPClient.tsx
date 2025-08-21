import { useState } from "react";
import axios from "axios";
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
  { label: "Stocks (real)", value: "use stocks_real: PANW" },
  { label: "LLM fallback", value: "Write a one-sentence project status based on my context." },
];

export default function MCPClient() {
  const [userId, setUserId] = useState("user123");
  const [useTools, setUseTools] = useState(true);
  const [task, setTask] = useState("");
  const [response, setResponse] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState<string>("");

  const sendRequest = async () => {
    setLoading(true);
    setErrorText("");
    setResponse(null);

    try {
      const res = await axios.post("http://127.0.0.1:8000/mcp", {
        user_id: userId,
        task,
        use_tools: useTools,
      });
      setResponse(res.data);
    } catch (err: any) {
      setErrorText(err?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid h-full grid-rows-1 gap-6 lg:grid-cols-2">
      {/* Left panel: controls */}
      <Card className="border-white/10 bg-white/5 backdrop-blur-sm h-full">
        <CardContent className="p-6 h-full flex flex-col">
          {/* Controls header */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400">User</label>
              <select
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="border-white/15 bg-slate-900/60 text-slate-100 rounded-md px-2 py-1 text-sm"
              >
                {USERS.map((u) => (
                  <option key={u.id} value={u.id}>{u.label}</option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-xs text-slate-300">
              <input
                type="checkbox"
                checked={useTools}
                onChange={(e) => setUseTools(e.target.checked)}
              />
              Use tools
            </label>
          </div>

          {/* Examples */}
          <div className="mt-4 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setTask(ex.value)}
                className="text-xs rounded-full px-3 py-1 border border-white/10 bg-black/25 hover:bg-black/35 text-slate-200"
                type="button"
              >
                {ex.label}
              </button>
            ))}
          </div>

          {/* Input + send button */}
          <div className="mt-4 space-y-3">
            <Input
              placeholder="Type your task (e.g. use weather_real: Detroit)"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              className="bg-black/30 border-white/10 text-slate-100 placeholder:text-slate-400"
            />
            <Button
              onClick={sendRequest}
              disabled={loading || !task.trim()}
              className="w-full bg-pink-600 hover:bg-pink-500 text-white shadow-lg shadow-pink-600/20"
            >
              {loading ? "Processing..." : "Send to MCP Server"}
            </Button>
            {errorText && (
              <div className="text-sm text-rose-300/90 bg-rose-500/10 border border-rose-400/20 rounded-md px-3 py-2">
                <strong className="mr-1">Error:</strong>{errorText}
              </div>
            )}
          </div>

          {/* Filler to push content at top, keeps layout nice on tall screens */}
          <div className="flex-1" />
        </CardContent>
      </Card>

      {/* Right panel: response */}
      <Card className="border-white/10 bg-white/5 backdrop-blur-sm h-full overflow-hidden">
        <CardContent className="p-6 h-full overflow-auto space-y-5">
          <h3 className="text-sm font-medium text-slate-200">Response</h3>
          <PrettyResponse data={response} />
        </CardContent>
      </Card>
    </div>
  );
}

/** High-contrast, readable response renderer (no Raw JSON) */
function PrettyResponse({ data }: { data: ApiResponse | null }) {
  if (!data) return (
    <div className="text-slate-400 text-sm">Run a request to see output.</div>
  );

  const tool = data.tool || data.tool_used;
  const error = data.error;
  const note = data.note;

  // Errors: high contrast red
  if (error) {
    return (
      <div className="rounded-lg border border-rose-400/30 bg-rose-500/15 p-4 text-rose-50">
        <div className="text-xs tracking-wide uppercase text-rose-200/80 mb-1">Error</div>
        <div className="text-base">{String(error)}</div>
      </div>
    );
  }

  // Helper to render small info cards
  const Info = ({ label, value }: { label: string; value?: any }) => (
    <div className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
      <div className="text-[10px] uppercase tracking-wider text-slate-300/80">{label}</div>
      <div className="text-slate-50 text-base">{value ?? "(n/a)"}</div>
    </div>
  );

  if (tool === "calculator" || tool === "code_eval") {
    return (
      <div className="grid sm:grid-cols-2 gap-3">
        <Info label="Tool" value={tool} />
        {data.input && <Info label="Input" value={String(data.input)} />}
        <Info label="Result" value={String(data.result)} />
      </div>
    );
  }

  if (tool === "todo") {
    return (
      <div className="grid sm:grid-cols-2 gap-3">
        <Info label="Tool" value="todo" />
        {data.action && <Info label="Action" value={String(data.action)} />}
        {data.item && <Info label="Item" value={String(data.item)} />}
        <div className="sm:col-span-2">
          <Info label="List" value={(Array.isArray(data.list) && data.list.length)
            ? (data.list as any[]).join(", ")
            : "(empty)"} />
        </div>
      </div>
    );
  }

  if (tool === "weather" || tool === "weather_real") {
    const d = data.data || {};
    return (
      <div className="grid sm:grid-cols-2 gap-3">
        <Info label="Tool" value={tool} />
        <Info label="City" value={String(d.city || data.city)} />
        <Info label="Temp (°C)" value={String(d.temp_c)} />
        <Info label="Conditions" value={String(d.conditions)} />
        {"wind_mps" in d && <Info label="Wind (m/s)" value={String(d.wind_mps)} />}
      </div>
    );
  }

  if (tool === "stocks" || tool === "stocks_real") {
    const d = data.data || {};
    return (
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <Info label="Tool" value={tool} />
        <Info label="Ticker" value={String(d.ticker || data.ticker)} />
        <Info label="Price" value={String(d.price ?? data.price)} />
        {"change" in d && <Info label="Change" value={String(d.change)} />}
        {"percent_change" in d && <Info label="% Change" value={String(d.percent_change)} />}
      </div>
    );
  }

  if (tool === "llm_fallback") {
    return (
      <div className="rounded-lg border border-white/10 bg-slate-900/40 p-4 text-slate-50">
        <div className="text-[10px] uppercase tracking-wider text-slate-300/80 mb-1">LLM Fallback</div>
        <div className="whitespace-pre-wrap leading-relaxed">{String(data.answer || "")}</div>
      </div>
    );
  }

  if (note) {
    return <div className="text-slate-200">{String(note)}</div>;
  }

  // Unknown payload shape → render a compact summary that’s still readable
  return (
    <div className="rounded-lg border border-white/10 bg-slate-900/40 p-4 text-slate-50">
      <div className="text-[10px] uppercase tracking-wider text-slate-300/80 mb-1">Result</div>
      <pre className="whitespace-pre-wrap text-[13px] leading-6">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

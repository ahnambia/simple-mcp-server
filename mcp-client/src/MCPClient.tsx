import { useState } from "react";
import axios from "axios";

// If you're using shadcn/ui
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function MCPClient() {
  const [task, setTask] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const sendRequest = async () => {
    setLoading(true);
    setResponse("");
    try {
      const res = await axios.post("http://127.0.0.1:8000/mcp", {
        user_id: "user123",
        task,
        use_tools: true,
      });
      setResponse(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setResponse("Error: " + err.message);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-xl mx-auto mt-10 space-y-4">
      <Card>
        <CardContent className="p-4">
          <h2 className="text-xl font-semibold mb-2">🧠 MCP Task Tester</h2>
          <Input
            placeholder="Type your task, e.g. calculate 3*7 or summarize..."
            value={task}
            onChange={(e) => setTask(e.target.value)}
            className="mb-2"
          />
          <Button onClick={sendRequest} disabled={loading}>
            {loading ? "Processing..." : "Send to MCP Server"}
          </Button>
        </CardContent>
      </Card>

      {response && (
        <Card>
          <CardContent className="p-4">
            <h3 className="font-medium mb-1">Response:</h3>
            <pre className="whitespace-pre-wrap text-sm bg-muted p-2 rounded">
              {response}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

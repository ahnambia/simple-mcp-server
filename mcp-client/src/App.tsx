import MCPClient from "./MCPClient";

export default function App() {
  return (
    <div className="h-screen w-screen bg-[radial-gradient(1200px_600px_at_10%_-10%,rgba(236,72,153,0.15),transparent),radial-gradient(1000px_500px_at_90%_10%,rgba(59,130,246,0.15),transparent)] bg-slate-950 text-slate-100">
      {/* Top bar */}
      <header className="sticky top-0 z-10 backdrop-blur bg-slate-900/70 border-b border-white/10">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-pink-500/20 text-pink-300 text-lg">🧠</span>
            <h1 className="text-lg font-semibold">MCP Task Tester</h1>
          </div>
          <span className="text-xs text-slate-300">Demo UI</span>
        </div>
      </header>

      {/* Main content area */}
      <main className="mx-auto max-w-7xl px-4 py-6 h-[calc(100vh-64px)]">
        {/* Two panels that fill the height */}
        <MCPClient />
      </main>
    </div>
  );
}

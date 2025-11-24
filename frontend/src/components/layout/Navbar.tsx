import { Link } from "react-router-dom";
import { useWsStore } from "@/stores/wsStore";

export function Navbar() {
  const { status, connect, disconnect } = useWsStore();

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold">MineCompanion AI</h1>
          <Link to="/monitor" className="text-sm text-muted-foreground hover:text-primary transition-colors">
            监控面板
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              status === "connected" ? "bg-green-500" :
              status === "connecting" ? "bg-yellow-500" :
              "bg-red-500"
            }`} />
            <span className="text-sm">{status}</span>
          </div>

          <button
            onClick={() => status === "connected" ? disconnect() : connect()}
            className="px-3 py-1 text-sm border rounded hover:bg-accent"
          >
            {status === "connected" ? "Disconnect" : "Connect"}
          </button>
        </div>
      </div>
    </nav>
  );
}

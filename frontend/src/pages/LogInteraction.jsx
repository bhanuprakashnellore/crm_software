import { useState } from "react";
import InteractionForm from "../components/InteractionForm";
import ChatPanel from "../components/ChatPanel";

export default function LogInteraction() {
  const [mode, setMode] = useState("chat");

  return (
    <div>
      <h1 className="page-title">Log Interaction</h1>
      <p className="page-subtitle">
        Capture an HCP interaction the way that fits the moment — a quick structured form after a visit, or a
        natural conversation with Field Copilot while you're still walking to the car.
      </p>

      <div className="mode-toggle">
        <button className={mode === "chat" ? "active" : ""} onClick={() => setMode("chat")}>
          💬 Conversational
        </button>
        <button className={mode === "form" ? "active" : ""} onClick={() => setMode("form")}>
          📋 Structured Form
        </button>
      </div>

      {mode === "form" ? <InteractionForm /> : <ChatPanel />}
    </div>
  );
}

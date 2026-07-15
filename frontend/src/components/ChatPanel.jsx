import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { addUserMessage, sendChatMessage, resetConversation } from "../features/chat/chatSlice";

const SUGGESTIONS = [
  "Log a visit with Dr. Anika Rao — discussed CardioMax dosing, left 10 samples, she was very positive.",
  "What did we last discuss with Dr. Meera Iyer?",
  "Change the sentiment of interaction 1 to positive and note that 5 more samples were requested.",
  "Schedule a follow-up with Dr. Vikram Sinha in 2 weeks about the endocrinology trial data.",
];

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, status } = useSelector((state) => state.chat);
  const threadId = useSelector((state) => state.chat.threadId);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, status]);

  const send = (text) => {
    const message = (text ?? input).trim();
    if (!message || status === "loading") return;
    dispatch(addUserMessage(message));
    dispatch(sendChatMessage({ message, threadId }));
    setInput("");
  };

  return (
    <div>
      <div className="chat-panel">
        <div className="chat-messages" ref={scrollRef}>
          {messages.length === 0 && (
            <div style={{ color: "var(--text-muted)", fontSize: 14 }}>
              Talk to Field Copilot the way you'd brief a colleague — it can log interactions, edit them, look up
              HCPs, pull interaction history, and schedule follow-ups.
              <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="btn secondary small"
                    style={{ textAlign: "left" }}
                    onClick={() => send(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, idx) => (
            <div key={idx} className={`chat-bubble ${m.role}`}>
              <div>{m.text}</div>
              {m.toolCalls?.length > 0 && (
                <div>
                  {m.toolCalls.map((tc, i) => (
                    <span className="tool-call-tag" key={i}>
                      🛠 {tc.tool}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {status === "loading" && (
            <div className="chat-bubble assistant">Field Copilot is thinking…</div>
          )}
        </div>
        <div className="chat-input-row">
          <input
            type="text"
            placeholder="Describe an interaction, ask for history, or request an edit…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button className="btn" onClick={() => send()} disabled={status === "loading"}>
            Send
          </button>
        </div>
      </div>
      <div className="chat-hint">
        Thread: {threadId.slice(0, 8)} ·{" "}
        <a href="#" onClick={(e) => { e.preventDefault(); dispatch(resetConversation()); }}>
          start a new conversation
        </a>
      </div>
    </div>
  );
}

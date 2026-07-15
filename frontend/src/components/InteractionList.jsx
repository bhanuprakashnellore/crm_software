import { useState } from "react";
import { useDispatch } from "react-redux";
import { updateInteraction, deleteInteraction } from "../features/interactions/interactionsSlice";

const SENTIMENTS = ["positive", "neutral", "negative"];

function EditRow({ interaction, onDone }) {
  const dispatch = useDispatch();
  const [summary, setSummary] = useState(interaction.summary || "");
  const [sentiment, setSentiment] = useState(interaction.sentiment);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await dispatch(
        updateInteraction({ id: interaction.id, payload: { summary, sentiment } })
      ).unwrap();
      onDone();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ marginTop: 10 }}>
      <div className="form-field">
        <label>Summary</label>
        <textarea value={summary} onChange={(e) => setSummary(e.target.value)} />
      </div>
      <div className="form-field" style={{ maxWidth: 200 }}>
        <label>Sentiment</label>
        <select value={sentiment} onChange={(e) => setSentiment(e.target.value)}>
          {SENTIMENTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <button className="btn small" onClick={save} disabled={saving}>
        {saving ? "Saving…" : "Save changes"}
      </button>{" "}
      <button className="btn secondary small" onClick={onDone}>
        Cancel
      </button>
    </div>
  );
}

export default function InteractionList({ interactions, hcpNameById = {} }) {
  const dispatch = useDispatch();
  const [editingId, setEditingId] = useState(null);

  if (!interactions.length) {
    return <p style={{ color: "var(--text-muted)", fontSize: 14 }}>No interactions logged yet.</p>;
  }

  return (
    <div>
      {interactions.map((interaction) => (
        <div className="interaction-item" key={interaction.id}>
          <div className="interaction-item-header">
            <div>
              <div className="interaction-item-title">
                {hcpNameById[interaction.hcp_id] || `HCP #${interaction.hcp_id}`} &middot;{" "}
                {interaction.purpose || "Interaction"}
              </div>
              <div className="interaction-item-meta">
                {interaction.interaction_date} · {interaction.channel.replace("_", " ")} · logged via{" "}
                {interaction.source}
              </div>
            </div>
            <div>
              <span className={`badge ${interaction.sentiment}`}>{interaction.sentiment}</span>
              {interaction.compliance_flag && (
                <span className="badge warning" style={{ marginLeft: 6 }}>
                  compliance review
                </span>
              )}
            </div>
          </div>

          {interaction.summary && <p style={{ fontSize: 14, margin: "6px 0" }}>{interaction.summary}</p>}

          {(interaction.products_discussed?.length > 0 || interaction.topics_discussed?.length > 0) && (
            <div className="tag-row">
              {interaction.topics_discussed?.map((t) => (
                <span className="tag" key={`t-${t}`}>
                  {t}
                </span>
              ))}
              {interaction.products_discussed?.map((p) => (
                <span className="tag" key={`p-${p}`}>
                  💊 {p}
                </span>
              ))}
            </div>
          )}

          {interaction.follow_up_required && (
            <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
              📅 Follow-up due {interaction.follow_up_date || "TBD"}
              {interaction.follow_up_notes ? ` — ${interaction.follow_up_notes}` : ""}
            </p>
          )}

          <div style={{ marginTop: 10 }}>
            {editingId === interaction.id ? (
              <EditRow interaction={interaction} onDone={() => setEditingId(null)} />
            ) : (
              <>
                <button className="btn secondary small" onClick={() => setEditingId(interaction.id)}>
                  Edit
                </button>{" "}
                <button
                  className="btn secondary small"
                  onClick={() => dispatch(deleteInteraction(interaction.id))}
                >
                  Delete
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

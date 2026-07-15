import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchHcps } from "../features/hcps/hcpsSlice";
import { createInteraction } from "../features/interactions/interactionsSlice";

const CHANNELS = ["in_person", "video_call", "phone_call", "email", "conference"];
const SENTIMENTS = ["positive", "neutral", "negative"];

const initialForm = {
  hcp_id: "",
  rep_name: "Demo Rep",
  interaction_date: new Date().toISOString().slice(0, 10),
  channel: "in_person",
  purpose: "",
  topics_discussed: "",
  products_discussed: "",
  materials_shared: "",
  samples_distributed: "",
  sentiment: "neutral",
  summary: "",
  raw_notes: "",
  follow_up_required: false,
  follow_up_date: "",
  follow_up_notes: "",
};

function parseCsv(value) {
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

function parseSamples(value) {
  const result = {};
  parseCsv(value).forEach((pair) => {
    const [product, qty] = pair.split(":").map((p) => p.trim());
    if (product) result[product] = Number(qty) || 0;
  });
  return result;
}

export default function InteractionForm() {
  const dispatch = useDispatch();
  const hcps = useSelector((state) => state.hcps.items);
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    dispatch(fetchHcps());
  }, [dispatch]);

  const handleChange = (field) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.hcp_id) return;
    setSubmitting(true);
    setSubmitted(false);
    try {
      await dispatch(
        createInteraction({
          ...form,
          hcp_id: Number(form.hcp_id),
          topics_discussed: parseCsv(form.topics_discussed),
          products_discussed: parseCsv(form.products_discussed),
          materials_shared: parseCsv(form.materials_shared),
          samples_distributed: parseSamples(form.samples_distributed),
          follow_up_date: form.follow_up_date || null,
        })
      ).unwrap();
      setForm(initialForm);
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="form-grid">
        <div className="form-field">
          <label>Healthcare Professional</label>
          <select value={form.hcp_id} onChange={handleChange("hcp_id")} required>
            <option value="">Select an HCP&hellip;</option>
            {hcps.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} {h.specialty ? `— ${h.specialty}` : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Rep Name</label>
          <input type="text" value={form.rep_name} onChange={handleChange("rep_name")} />
        </div>
        <div className="form-field">
          <label>Interaction Date</label>
          <input type="date" value={form.interaction_date} onChange={handleChange("interaction_date")} />
        </div>
        <div className="form-field">
          <label>Channel</label>
          <select value={form.channel} onChange={handleChange("channel")}>
            {CHANNELS.map((c) => (
              <option key={c} value={c}>
                {c.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Purpose</label>
          <input
            type="text"
            placeholder="e.g. product_detailing, sample_drop"
            value={form.purpose}
            onChange={handleChange("purpose")}
          />
        </div>
        <div className="form-field">
          <label>Sentiment</label>
          <select value={form.sentiment} onChange={handleChange("sentiment")}>
            {SENTIMENTS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>Topics Discussed (comma separated)</label>
          <input type="text" value={form.topics_discussed} onChange={handleChange("topics_discussed")} />
        </div>
        <div className="form-field">
          <label>Products Discussed (comma separated)</label>
          <input type="text" value={form.products_discussed} onChange={handleChange("products_discussed")} />
        </div>
        <div className="form-field">
          <label>Materials Shared (comma separated)</label>
          <input type="text" value={form.materials_shared} onChange={handleChange("materials_shared")} />
        </div>
        <div className="form-field">
          <label>Samples Distributed (Product:Qty, comma separated)</label>
          <input
            type="text"
            placeholder="e.g. CardioMax:10, GlucoEase:5"
            value={form.samples_distributed}
            onChange={handleChange("samples_distributed")}
          />
        </div>
        <div className="form-field full">
          <label>Summary</label>
          <textarea value={form.summary} onChange={handleChange("summary")} />
        </div>
        <div className="form-field full">
          <label>Raw Notes</label>
          <textarea value={form.raw_notes} onChange={handleChange("raw_notes")} />
        </div>
        <div className="form-field">
          <label>
            <input
              type="checkbox"
              checked={form.follow_up_required}
              onChange={handleChange("follow_up_required")}
              style={{ marginRight: 6 }}
            />
            Follow-up required
          </label>
        </div>
        {form.follow_up_required && (
          <>
            <div className="form-field">
              <label>Follow-up Date</label>
              <input type="date" value={form.follow_up_date} onChange={handleChange("follow_up_date")} />
            </div>
            <div className="form-field full">
              <label>Follow-up Notes</label>
              <textarea value={form.follow_up_notes} onChange={handleChange("follow_up_notes")} />
            </div>
          </>
        )}
      </div>
      <button className="btn" type="submit" disabled={submitting}>
        {submitting ? "Saving…" : "Log Interaction"}
      </button>
      {submitted && (
        <span style={{ marginLeft: 12, color: "var(--positive)", fontSize: 13, fontWeight: 600 }}>
          Interaction logged successfully.
        </span>
      )}
    </form>
  );
}

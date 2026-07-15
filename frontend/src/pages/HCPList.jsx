import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { fetchHcps } from "../features/hcps/hcpsSlice";

export default function HCPList() {
  const dispatch = useDispatch();
  const hcps = useSelector((state) => state.hcps.items);
  const [query, setQuery] = useState("");

  useEffect(() => {
    dispatch(fetchHcps());
  }, [dispatch]);

  const filtered = hcps.filter((h) =>
    [h.name, h.specialty, h.institution].filter(Boolean).some((f) => f.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div>
      <h1 className="page-title">HCP Directory</h1>
      <p className="page-subtitle">Every healthcare professional your team has engaged with.</p>

      <input
        type="text"
        className="search-input"
        placeholder="Search by name, specialty, institution…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Specialty</th>
              <th>Institution</th>
              <th>Tier</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((h) => (
              <tr key={h.id}>
                <td>{h.name}</td>
                <td>{h.specialty || "—"}</td>
                <td>{h.institution || "—"}</td>
                <td>{h.engagement_tier || "—"}</td>
                <td>
                  <Link to={`/hcps/${h.id}`}>View profile →</Link>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: "var(--text-muted)" }}>
                  No HCPs match your search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

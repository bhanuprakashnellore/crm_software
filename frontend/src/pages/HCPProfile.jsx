import { useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchHcps } from "../features/hcps/hcpsSlice";
import { fetchInteractions } from "../features/interactions/interactionsSlice";
import InteractionList from "../components/InteractionList";

export default function HCPProfile() {
  const { hcpId } = useParams();
  const dispatch = useDispatch();
  const hcps = useSelector((state) => state.hcps.items);
  const interactions = useSelector((state) => state.interactions.items);
  const hcp = hcps.find((h) => String(h.id) === hcpId);

  useEffect(() => {
    dispatch(fetchHcps());
    dispatch(fetchInteractions(Number(hcpId)));
  }, [dispatch, hcpId]);

  if (!hcp) {
    return <p style={{ color: "var(--text-muted)" }}>Loading HCP profile…</p>;
  }

  return (
    <div>
      <Link to="/hcps" style={{ fontSize: 13 }}>
        ← Back to directory
      </Link>
      <h1 className="page-title" style={{ marginTop: 10 }}>
        {hcp.name}
      </h1>
      <p className="page-subtitle">
        {hcp.specialty} {hcp.institution ? `· ${hcp.institution}` : ""} {hcp.city ? `· ${hcp.city}` : ""}
      </p>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="form-grid">
          <div>
            <strong>Engagement tier:</strong> {hcp.engagement_tier || "—"}
          </div>
          <div>
            <strong>NPI:</strong> {hcp.npi_number || "—"}
          </div>
          <div>
            <strong>Email:</strong> {hcp.email || "—"}
          </div>
          <div>
            <strong>Phone:</strong> {hcp.phone || "—"}
          </div>
        </div>
        {hcp.notes && <p style={{ marginTop: 10 }}>{hcp.notes}</p>}
      </div>

      <div className="section-header">
        <h3>Interaction history</h3>
        <Link to="/log-interaction" className="btn small">
          + Log new interaction
        </Link>
      </div>
      <InteractionList interactions={interactions} hcpNameById={{ [hcp.id]: hcp.name }} />
    </div>
  );
}

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { fetchHcps } from "../features/hcps/hcpsSlice";
import { fetchInteractions } from "../features/interactions/interactionsSlice";
import InteractionList from "../components/InteractionList";

export default function Dashboard() {
  const dispatch = useDispatch();
  const hcps = useSelector((state) => state.hcps.items);
  const interactions = useSelector((state) => state.interactions.items);

  useEffect(() => {
    dispatch(fetchHcps());
    dispatch(fetchInteractions());
  }, [dispatch]);

  const hcpNameById = Object.fromEntries(hcps.map((h) => [h.id, h.name]));
  const pendingFollowUps = interactions.filter((i) => i.follow_up_required).length;
  const flagged = interactions.filter((i) => i.compliance_flag).length;

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Snapshot of your HCP engagement activity.</p>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{hcps.length}</div>
          <div className="stat-label">HCPs tracked</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{interactions.length}</div>
          <div className="stat-label">Interactions logged</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{pendingFollowUps}</div>
          <div className="stat-label">Pending follow-ups</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{flagged}</div>
          <div className="stat-label">Compliance flags</div>
        </div>
      </div>

      <div className="section-header">
        <h3>Recent interactions</h3>
        <Link to="/log-interaction" className="btn small">
          + Log new interaction
        </Link>
      </div>
      <InteractionList interactions={interactions.slice(0, 6)} hcpNameById={hcpNameById} />
    </div>
  );
}

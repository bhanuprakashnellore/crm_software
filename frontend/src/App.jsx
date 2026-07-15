import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import HCPList from "./pages/HCPList";
import HCPProfile from "./pages/HCPProfile";
import LogInteraction from "./pages/LogInteraction";

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/log-interaction" element={<LogInteraction />} />
          <Route path="/hcps" element={<HCPList />} />
          <Route path="/hcps/:hcpId" element={<HCPProfile />} />
        </Routes>
      </main>
    </div>
  );
}

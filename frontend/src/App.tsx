import { BrowserRouter, Route, Routes } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";
import Assets from "./pages/Assets";
import AttackSurface from "./pages/AttackSurface";
import Changes from "./pages/Changes";
import Dashboard from "./pages/Dashboard";
import Findings from "./pages/Findings";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/attack-surface" element={<AttackSurface />} />
          <Route path="/assets" element={<Assets />} />
          <Route path="/changes" element={<Changes />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

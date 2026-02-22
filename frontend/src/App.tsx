import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "./components/common/AppShell";
import { Baseline } from "./pages/Baseline";
import { GraphExplorer } from "./pages/GraphExplorer";
import { Home } from "./pages/Home";
import { Investigations } from "./pages/Investigations";
import { Login } from "./pages/Login";
import { Patterns } from "./pages/Patterns";
import { Search } from "./pages/Search";
import { SharedInvestigation } from "./pages/SharedInvestigation";
import { useAuthStore } from "./stores/auth";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function App() {
  const restore = useAuthStore((s) => s.restore);

  useEffect(() => {
    restore();
  }, [restore]);

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/search" element={<Search />} />
        <Route path="/graph/:entityId" element={<GraphExplorer />} />
        <Route path="/patterns" element={<Patterns />} />
        <Route path="/patterns/:entityId" element={<Patterns />} />
        <Route
          path="/baseline/:entityId"
          element={
            <RequireAuth>
              <Baseline />
            </RequireAuth>
          }
        />
        <Route
          path="/investigations"
          element={
            <RequireAuth>
              <Investigations />
            </RequireAuth>
          }
        />
        <Route
          path="/investigations/shared/:token"
          element={<SharedInvestigation />}
        />
        <Route
          path="/investigations/:investigationId"
          element={
            <RequireAuth>
              <Investigations />
            </RequireAuth>
          }
        />
      </Routes>
    </AppShell>
  );
}

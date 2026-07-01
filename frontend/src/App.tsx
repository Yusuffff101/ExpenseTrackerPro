import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { TOKEN_KEY } from "./api";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";

function ProtectedRoute() {
  return localStorage.getItem(TOKEN_KEY) ? <Outlet /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>
      <Route path="*" element={<Navigate to={localStorage.getItem(TOKEN_KEY) ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
}

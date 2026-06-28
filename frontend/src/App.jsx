import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Landing from './components/pages/Landing';
import Login from './components/pages/Login';
import Register from './components/pages/Register';
import Onboarding from './components/pages/Onboarding';
import Dashboard from './components/pages/Dashboard';
import Preferences from './components/pages/Preferences';
import Schedule from './components/pages/Schedule';
import Reports from './components/pages/Reports';
import ReportDetail from './components/pages/ReportDetail';
import Profile from './components/pages/Profile';
import { Loader } from 'lucide-react';
import VerifyEmail from './components/pages/Verifyemail';
import ReportFeedback from "./components/pages/ReportFeedback";

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }
  return isAuthenticated ? <Layout>{children}</Layout> : <Navigate to="/login" />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
    path="/verify-email"
    element={<VerifyEmail />}
/>
      <Route
        path="/onboarding"
        element={
          <PrivateRoute>
            <Onboarding />
          </PrivateRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/preferences"
        element={
          <PrivateRoute>
            <Preferences />
          </PrivateRoute>
        }
      />
      <Route
          path="/report-feedback/:reportId"
          element={<ReportFeedback />}
      />
      <Route
        path="/schedule"
        element={
          <PrivateRoute>
            <Schedule />
          </PrivateRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <PrivateRoute>
            <Reports />
          </PrivateRoute>
        }
      />
      <Route
        path="/reports/:id"
        element={
          <PrivateRoute>
            <ReportDetail />
          </PrivateRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;

import { Route, Routes } from 'react-router-dom';

import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminPage } from './pages/AdminPage';
import { DashboardPage } from './pages/DashboardPage';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { NewReportPage } from './pages/NewReportPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { OperatorPage } from './pages/OperatorPage';
import { RegisterPage } from './pages/RegisterPage';
import { ReportDetailPage } from './pages/ReportDetailPage';

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="reports/:reportId" element={<ReportDetailPage />} />
        <Route
          path="reports/new"
          element={
            <ProtectedRoute allowedRoles={['citizen']}>
              <NewReportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="operator"
          element={
            <ProtectedRoute allowedRoles={['operator', 'admin']}>
              <OperatorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;

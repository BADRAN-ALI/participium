import type { ReactElement } from 'react';
import { Navigate } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth';
import { domIdAttrs } from '../domIds';
import type { UserRole } from '../types/api';

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  children: ReactElement;
}

export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return <section className="card" {...domIdAttrs('protected-route-loading')}>Loading session...</section>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

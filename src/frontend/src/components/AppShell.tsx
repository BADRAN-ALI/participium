import { Link, NavLink, Outlet } from 'react-router-dom';

import { BACKEND_BASE_URL } from '../config';
import { useAuth } from '../hooks/useAuth';
import { domIdAttrs } from '../domIds';

export function AppShell() {
  const { user, logout } = useAuth();

  async function handleLogout(): Promise<void> {
    await logout();
  }

  return (
    <div className="app-shell" {...domIdAttrs('app-shell')}>
      <header className="topbar" {...domIdAttrs('app-topbar')}>
        <div id="app-brand-block">
          <Link className="brand" to="/" {...domIdAttrs('brand-link')}>Participium</Link>
          <p className="tagline" id="app-tagline">Civic issue reporting platform</p>
        </div>
        <nav className="nav-links" {...domIdAttrs('main-navigation')}>
          <NavLink to="/" {...domIdAttrs('nav-home')}>Home</NavLink>
          {user?.role === 'citizen' ? <NavLink to="/reports/new" {...domIdAttrs('nav-new-report')}>New Report</NavLink> : null}
          {user ? <NavLink to="/dashboard" {...domIdAttrs('nav-dashboard')}>Dashboard</NavLink> : null}
          {user && ['operator', 'admin'].includes(user.role) ? (
            <NavLink to="/operator" {...domIdAttrs('nav-operator')}>Operator</NavLink>
          ) : null}
          {user?.role === 'admin' ? <NavLink to="/admin" {...domIdAttrs('nav-admin')}>Admin</NavLink> : null}
          {user ? (
            <button className="ghost-button" onClick={handleLogout} {...domIdAttrs('logout-button')}>Logout</button>
          ) : (
            <>
              <NavLink to="/login" {...domIdAttrs('nav-login')}>Login</NavLink>
              <NavLink to="/register" {...domIdAttrs('nav-register')}>Register</NavLink>
            </>
          )}
          <a href={`${BACKEND_BASE_URL}/apidocs/`} target="_blank" rel="noreferrer" {...domIdAttrs('nav-swagger')}>Swagger</a>
        </nav>
      </header>
      <main className="page-container" {...domIdAttrs('page-container')}>
        <Outlet />
      </main>
    </div>
  );
}

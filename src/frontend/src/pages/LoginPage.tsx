import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiError } from '../api/http';
import { useAuth } from '../hooks/useAuth';
import { domIdAttrs } from '../domIds';
import type { UserDto } from '../types/api';

function getLandingPath(user: UserDto): string {
  if (user.role === 'admin') {
    return '/admin';
  }
  if (user.role === 'operator') {
    return '/operator';
  }
  return '/dashboard';
}

export function LoginPage() {
  const navigate = useNavigate();
  const { user, login } = useAuth();
  const [identifier, setIdentifier] = useState<string>('citizen@example.com');
  const [password, setPassword] = useState<string>('Citizen123!');
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (user) {
      navigate(getLandingPath(user), { replace: true });
    }
  }, [navigate, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const authenticatedUser = await login(identifier, password);
      setError('');
      navigate(getLandingPath(authenticatedUser), { replace: true });
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to log in.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="card auth-card" {...domIdAttrs('login-page')}>
      <h1 id="login-title">Login</h1>
      <p className="muted-text" id="login-description">Use one of the seeded demo accounts or a previously registered user.</p>
      <form className="form-grid" onSubmit={handleSubmit} {...domIdAttrs('login-form')}>
        <label id="login-identifier-label">
          Username or email
          <input
            type="text"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            {...domIdAttrs('login-identifier')}
            required
          />
        </label>
        <label id="login-password-label">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            {...domIdAttrs('login-password')}
            required
          />
        </label>
        <div className="button-row" id="login-actions">
          <button type="submit" disabled={isSubmitting} {...domIdAttrs('login-submit')}>
            {isSubmitting ? 'Signing in...' : 'Login'}
          </button>
        </div>
      </form>
      {error ? <p className="error-text" {...domIdAttrs('login-error')}>{error}</p> : null}
      <div className="card card-inline hint-box" {...domIdAttrs('login-demo-accounts')}>
        <strong id="login-demo-accounts-title">Demo accounts</strong>
        <ul className="clean-list" id="login-demo-accounts-list">
          <li id="login-demo-citizen-account"><code id="login-demo-citizen-email">citizen@example.com</code> / <code id="login-demo-citizen-password">Citizen123!</code></li>
          <li id="login-demo-operator-account"><code id="login-demo-operator-email">operator@example.com</code> / <code id="login-demo-operator-password">Operator123!</code></li>
          <li id="login-demo-admin-account"><code id="login-demo-admin-email">admin@example.com</code> / <code id="login-demo-admin-password">Admin123!</code></li>
        </ul>
      </div>
    </section>
  );
}

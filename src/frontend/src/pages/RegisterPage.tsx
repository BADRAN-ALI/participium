import { FormEvent, useState } from 'react';

import { ApiError, apiClient } from '../api/http';
import { domIdAttrs } from '../domIds';

interface RegistrationFormState {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

const initialForm: RegistrationFormState = {
  username: '',
  firstName: '',
  lastName: '',
  email: '',
  password: '',
};

export function RegisterPage() {
  const [form, setForm] = useState<RegistrationFormState>(initialForm);
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [verificationUrl, setVerificationUrl] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const response = await apiClient.register({
        username: form.username,
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
      });
      setError('');
      setSuccessMessage(`Account created for ${response.user.email}. Verify the email before logging in.`);
      setVerificationUrl(response.verification_url ?? '');
      setForm({ ...initialForm, email: response.user.email });
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to register.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="card auth-card" {...domIdAttrs('register-page')}>
      <h1 id="register-title">Create account</h1>
      <p className="muted-text" id="register-description">Citizens can create reports, follow published issues and exchange messages with operators.</p>
      <form className="form-grid" onSubmit={handleSubmit} {...domIdAttrs('register-form')}>
        <label id="register-username-label">
          Username
          <input
            type="text"
            value={form.username}
            onChange={(event) => setForm({ ...form, username: event.target.value })}
            {...domIdAttrs('register-username')}
            required
          />
        </label>
        <label id="register-first-name-label">
          First name
          <input
            type="text"
            value={form.firstName}
            onChange={(event) => setForm({ ...form, firstName: event.target.value })}
            {...domIdAttrs('register-first-name')}
            required
          />
        </label>
        <label id="register-last-name-label">
          Last name
          <input
            type="text"
            value={form.lastName}
            onChange={(event) => setForm({ ...form, lastName: event.target.value })}
            {...domIdAttrs('register-last-name')}
            required
          />
        </label>
        <label id="register-email-label">
          Email
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            {...domIdAttrs('register-email')}
            required
          />
        </label>
        <label id="register-password-label">
          Password
          <input
            type="password"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            {...domIdAttrs('register-password')}
            required
          />
        </label>
        <div className="button-row" id="register-actions">
          <button type="submit" disabled={isSubmitting} {...domIdAttrs('register-submit')}>
            {isSubmitting ? 'Creating account...' : 'Register'}
          </button>
        </div>
      </form>
      {error ? <p className="error-text" {...domIdAttrs('register-error')}>{error}</p> : null}
      {successMessage ? <p className="success-text" {...domIdAttrs('register-success')}>{successMessage}</p> : null}
      {verificationUrl ? (
        <div className="card card-inline hint-box" {...domIdAttrs('verification-box')}>
          <p id="verification-description">Verification link exposed for local/demo environments.</p>
          <a href={verificationUrl} target="_blank" rel="noreferrer" {...domIdAttrs('verification-link')}>
            Open verification link
          </a>
        </div>
      ) : null}
    </section>
  );
}

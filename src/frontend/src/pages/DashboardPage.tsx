import { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ApiError, apiClient } from '../api/http';
import { useAuth } from '../hooks/useAuth';
import { DOM_ID_PREFIXES, childDomId, prefixedDomId, domIdAttrs } from '../domIds';
import type { NotificationDto, ReportSummaryDto } from '../types/api';

interface ProfileFormState {
  username: string;
  firstName: string;
  lastName: string;
  emailNotificationsEnabled: boolean;
  profilePicture: File | null;
}

const initialForm: ProfileFormState = {
  username: '',
  firstName: '',
  lastName: '',
  emailNotificationsEnabled: true,
  profilePicture: null,
};

function formatDateTime(value: string | null): string {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleString();
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, clearSession, refreshCurrentUser } = useAuth();
  const [form, setForm] = useState<ProfileFormState>(initialForm);
  const [reports, setReports] = useState<ReportSummaryDto[]>([]);
  const [notifications, setNotifications] = useState<NotificationDto[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);

  useEffect(() => {
    if (!user) {
      return;
    }
    setForm({
      username: user.username,
      firstName: user.first_name,
      lastName: user.last_name,
      emailNotificationsEnabled: user.email_notifications_enabled,
      profilePicture: null,
    });
  }, [user]);

  useEffect(() => {
    Promise.all([apiClient.getMyReports(), apiClient.getMyNotifications()])
      .then(([nextReports, nextNotifications]) => {
        setReports(nextReports);
        setNotifications(nextNotifications);
        setError('');
      })
      .catch((apiError: unknown) => {
        setError(apiError instanceof ApiError ? apiError.message : 'Unable to load dashboard data.');
      });
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const nextFile = event.target.files?.[0] ?? null;
    setForm((currentForm) => ({ ...currentForm, profilePicture: nextFile }));
  }

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsSaving(true);
    try {
      const payload = new FormData();
      payload.append('username', form.username);
      payload.append('first_name', form.firstName);
      payload.append('last_name', form.lastName);
      if (form.emailNotificationsEnabled) {
        payload.append('email_notifications_enabled', 'true');
      }
      if (form.profilePicture) {
        payload.append('profile_picture', form.profilePicture);
      }
      await apiClient.updateCurrentUser(payload);
      await refreshCurrentUser();
      setStatusMessage('Profile updated.');
      setError('');
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to update profile.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteAccount(): Promise<void> {
    const confirmed = window.confirm('Delete the current account and personal data?');
    if (!confirmed) {
      return;
    }
    try {
      await apiClient.deleteCurrentUser();
      clearSession();
      navigate('/', { replace: true });
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to delete account.');
    }
  }

  async function markNotificationAsRead(notificationId: number): Promise<void> {
    try {
      const updatedNotification = await apiClient.markNotificationAsRead(notificationId);
      setNotifications((currentNotifications) =>
        currentNotifications.map((notification) =>
          notification.id === notificationId ? updatedNotification : notification,
        ),
      );
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to update notification.');
    }
  }

  return (
    <div className="page-grid" {...domIdAttrs('dashboard-page')}>
      <section className="card" {...domIdAttrs('profile-section')}>
        <h1 id="dashboard-title">User dashboard</h1>
        <p className="muted-text" id="dashboard-description">Manage your profile, notifications and submitted reports.</p>
        <form className="form-grid" onSubmit={handleProfileSubmit} {...domIdAttrs('profile-form')}>
          <label id="profile-username-label">
            Username
            <input
              type="text"
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              {...domIdAttrs('profile-username')}
              required
            />
          </label>
          <label id="profile-first-name-label">
            First name
            <input
              type="text"
              value={form.firstName}
              onChange={(event) => setForm({ ...form, firstName: event.target.value })}
              {...domIdAttrs('profile-first-name')}
              required
            />
          </label>
          <label id="profile-last-name-label">
            Last name
            <input
              type="text"
              value={form.lastName}
              onChange={(event) => setForm({ ...form, lastName: event.target.value })}
              {...domIdAttrs('profile-last-name')}
              required
            />
          </label>
          <label id="profile-email-label">
            Email
            <input type="email" value={user?.email ?? ''} readOnly {...domIdAttrs('profile-email')} />
          </label>
          <label className="checkbox-row" id="profile-email-notifications-label">
            <input
              type="checkbox"
              checked={form.emailNotificationsEnabled}
              onChange={(event) => setForm({ ...form, emailNotificationsEnabled: event.target.checked })}
              {...domIdAttrs('profile-email-notifications')}
            />
            Email notifications enabled
          </label>
          <label id="profile-picture-label">
            Profile picture
            <input type="file" accept="image/*" onChange={handleFileChange} {...domIdAttrs('profile-picture')} />
          </label>
          <div className="button-row" id="profile-actions">
            <button type="submit" disabled={isSaving} {...domIdAttrs('profile-save')}>
              {isSaving ? 'Saving...' : 'Save profile'}
            </button>
            <button type="button" className="danger-button" onClick={handleDeleteAccount} {...domIdAttrs('delete-account-button')}>
              Delete account
            </button>
          </div>
        </form>
        {statusMessage ? <p className="success-text" {...domIdAttrs('profile-success')}>{statusMessage}</p> : null}
        {error ? <p className="error-text" {...domIdAttrs('dashboard-error')}>{error}</p> : null}
      </section>

      <section className="split-grid" {...domIdAttrs('dashboard-lists-section')}>
        <div className="card" {...domIdAttrs('my-reports-card')}>
          <h2 id="my-reports-title">My reports</h2>
          <table className="data-table" {...domIdAttrs('my-reports-table')}>
            <thead id="my-reports-table-head">
              <tr id="my-reports-header-row">
                <th id="my-reports-header-id">ID</th>
                <th id="my-reports-header-title">Title</th>
                <th id="my-reports-header-status">Status</th>
                <th id="my-reports-header-created">Created</th>
                <th id="my-reports-header-actions"></th>
              </tr>
            </thead>
            <tbody id="my-reports-table-body">
              {reports.map((report) => {
                const rowId = prefixedDomId(DOM_ID_PREFIXES.myReportRow, report.id);
                return (
                  <tr key={report.id} {...domIdAttrs(rowId)}>
                    <td id={childDomId(rowId, 'id')}>#{report.id}</td>
                    <td id={childDomId(rowId, 'title')}>{report.title}</td>
                    <td id={childDomId(rowId, 'status')}>{report.status}</td>
                    <td id={childDomId(rowId, 'created')}>{formatDateTime(report.created_at)}</td>
                    <td id={childDomId(rowId, 'actions')}>
                      <Link to={`/reports/${report.id}`} {...domIdAttrs(childDomId(rowId, 'open-link'))}>Open</Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="card" {...domIdAttrs('notifications-card')}>
          <h2 id="notifications-title">Notifications</h2>
          <ul className="stack-list" {...domIdAttrs('notifications-list')}>
            {notifications.map((notification) => (
              <li
                key={notification.id}
                className={notification.is_read ? 'list-card is-muted' : 'list-card'}
                {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id))}
              >
                <div className="list-card-header" id={childDomId(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id), 'header')}>
                  <strong id={childDomId(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id), 'title')}>{notification.title}</strong>
                  <span id={childDomId(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id), 'created')}>{formatDateTime(notification.created_at)}</span>
                </div>
                <p id={childDomId(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id), 'body')}>{notification.body}</p>
                <div className="button-row compact-row" id={childDomId(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id), 'actions')}>
                  {notification.report_id ? (
                    <Link
                      to={`/reports/${notification.report_id}`}
                      {...domIdAttrs(childDomId(prefixedDomId(DOM_ID_PREFIXES.notificationItem, notification.id), 'open-report'))}
                    >
                      Open report
                    </Link>
                  ) : null}
                  {!notification.is_read ? (
                    <button
                      type="button"
                      onClick={() => markNotificationAsRead(notification.id)}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.notificationRead, notification.id))}
                    >
                      Mark as read
                    </button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}

import { FormEvent, useEffect, useState } from 'react';

import { ApiError, apiClient } from '../api/http';
import { DOM_ID_PREFIXES, childDomId, prefixedDomId, domIdAttrs } from '../domIds';
import type { AdminStatisticsDto, CategoryDto, ReferenceDataDto, UserDto, UserRole } from '../types/api';

interface NewUserFormState {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: UserRole;
  category_id: number | null;
  is_active: boolean;
  email_notifications_enabled: boolean;
}

interface EditableUserState {
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  category_id: number | null;
  is_active: boolean;
  email_notifications_enabled: boolean;
}

interface EditableCategoryState {
  name: string;
  is_active: boolean;
}

const initialNewUserForm: NewUserFormState = {
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  role: 'operator',
  category_id: null,
  is_active: true,
  email_notifications_enabled: true,
};

function buildEditableUser(user: UserDto): EditableUserState {
  return {
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    role: user.role,
    category_id: user.category_id,
    is_active: user.is_active,
    email_notifications_enabled: user.email_notifications_enabled,
  };
}

function buildEditableCategory(category: CategoryDto): EditableCategoryState {
  return {
    name: category.name,
    is_active: category.is_active,
  };
}

function buildEditableUsers(users: UserDto[]): Record<number, EditableUserState> {
  const nextState: Record<number, EditableUserState> = {};
  users.forEach((user) => {
    nextState[user.id] = buildEditableUser(user);
  });
  return nextState;
}

function buildEditableCategories(categories: CategoryDto[]): Record<number, EditableCategoryState> {
  const nextState: Record<number, EditableCategoryState> = {};
  categories.forEach((category) => {
    nextState[category.id] = buildEditableCategory(category);
  });
  return nextState;
}

function parseCategoryId(value: string): number | null {
  if (!value) {
    return null;
  }
  const parsedValue = Number(value);
  return Number.isInteger(parsedValue) ? parsedValue : null;
}

function normalizeOperatorCategory(
  role: UserRole,
  categoryId: number | null,
  categories: CategoryDto[],
): number | null {
  if (role !== 'operator') {
    return null;
  }
  if (categoryId !== null) {
    return categoryId;
  }
  return categories[0]?.id ?? null;
}

function renderMetricList(title: string, values: Record<string, number>) {
  const metricListId = prefixedDomId(DOM_ID_PREFIXES.adminMetricItem, title);
  return (
    <div className="metric-column" {...domIdAttrs(metricListId)}>
      <h3 id={childDomId(metricListId, 'title')}>{title}</h3>
      <ul className="clean-list" id={childDomId(metricListId, 'list')}>
        {Object.entries(values).map(([label, value]) => {
          const itemId = childDomId(metricListId, label);
          return (
            <li key={label} {...domIdAttrs(itemId)}>
              {label}: <strong id={childDomId(itemId, 'value')}>{value}</strong>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function AdminPage() {
  const [referenceData, setReferenceData] = useState<ReferenceDataDto | null>(null);
  const [users, setUsers] = useState<UserDto[]>([]);
  const [categories, setCategories] = useState<CategoryDto[]>([]);
  const [statistics, setStatistics] = useState<AdminStatisticsDto | null>(null);
  const [newUserForm, setNewUserForm] = useState<NewUserFormState>(initialNewUserForm);
  const [editedUsers, setEditedUsers] = useState<Record<number, EditableUserState>>({});
  const [newCategoryName, setNewCategoryName] = useState<string>('');
  const [editedCategories, setEditedCategories] = useState<Record<number, EditableCategoryState>>({});
  const [error, setError] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const activeCategories = categories.filter((category) => category.is_active);

  async function loadAdminData(): Promise<void> {
    try {
      const [referencePayload, nextUsers, nextCategories, nextStatistics] = await Promise.all([
        apiClient.getReferenceData(),
        apiClient.getAdminUsers(),
        apiClient.getAdminCategories(),
        apiClient.getAdminStatistics(),
      ]);
      setReferenceData(referencePayload);
      setUsers(nextUsers);
      setCategories(nextCategories);
      setStatistics(nextStatistics);
      setEditedUsers(buildEditableUsers(nextUsers));
      setEditedCategories(buildEditableCategories(nextCategories));
      setNewUserForm((currentValue) => ({
        ...currentValue,
        category_id: normalizeOperatorCategory(currentValue.role, currentValue.category_id, nextCategories.filter((category) => category.is_active)),
      }));
      setError('');
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to load admin data.');
    }
  }

  useEffect(() => {
    loadAdminData();
  }, []);

  function updateEditedUser(user: UserDto, patch: Partial<EditableUserState>): void {
    const currentValue = editedUsers[user.id] ?? buildEditableUser(user);
    setEditedUsers({
      ...editedUsers,
      [user.id]: {
        ...currentValue,
        ...patch,
      },
    });
  }

  function updateEditedCategory(category: CategoryDto, patch: Partial<EditableCategoryState>): void {
    const currentValue = editedCategories[category.id] ?? buildEditableCategory(category);
    setEditedCategories({
      ...editedCategories,
      [category.id]: {
        ...currentValue,
        ...patch,
      },
    });
  }

  async function handleCreateUser(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    try {
      await apiClient.createAdminUser(newUserForm);
      setNewUserForm(initialNewUserForm);
      setStatusMessage('User created.');
      setError('');
      await loadAdminData();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to create user.');
    }
  }

  async function handleUpdateUser(userId: number): Promise<void> {
    try {
      await apiClient.updateAdminUser(userId, editedUsers[userId]);
      setStatusMessage(`User #${userId} updated.`);
      setError('');
      await loadAdminData();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to update user.');
    }
  }

  async function handleCreateCategory(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    try {
      await apiClient.createCategory(newCategoryName);
      setNewCategoryName('');
      setStatusMessage('Category created.');
      setError('');
      await loadAdminData();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to create category.');
    }
  }

  async function handleUpdateCategory(categoryId: number): Promise<void> {
    try {
      await apiClient.updateCategory(categoryId, editedCategories[categoryId]);
      setStatusMessage(`Category #${categoryId} updated.`);
      setError('');
      await loadAdminData();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to update category.');
    }
  }

  return (
    <div className="page-grid" {...domIdAttrs('admin-page')}>
      <section className="card" {...domIdAttrs('admin-summary-section')}>
        <h1 id="admin-title">Admin panel</h1>
        <p className="muted-text" id="admin-description">Administrators manage categories and user accounts, including the category assigned to each operator.</p>
        {statusMessage ? <p className="success-text" {...domIdAttrs('admin-success')}>{statusMessage}</p> : null}
        {error ? <p className="error-text" {...domIdAttrs('admin-error')}>{error}</p> : null}
      </section>

      <section className="split-grid" {...domIdAttrs('admin-create-section')}>
        <div className="card" {...domIdAttrs('admin-create-user-card')}>
          <h2 id="admin-create-user-title">Create user</h2>
          <form className="form-grid compact-grid" onSubmit={handleCreateUser} {...domIdAttrs('admin-user-form')}>
            <label id="admin-new-user-username-label">
              Username
              <input
                type="text"
                value={newUserForm.username}
                onChange={(event) => setNewUserForm({ ...newUserForm, username: event.target.value })}
                {...domIdAttrs('admin-new-user-username')}
                required
              />
            </label>
            <label id="admin-new-user-first-name-label">
              First name
              <input
                type="text"
                value={newUserForm.first_name}
                onChange={(event) => setNewUserForm({ ...newUserForm, first_name: event.target.value })}
                {...domIdAttrs('admin-new-user-first-name')}
                required
              />
            </label>
            <label id="admin-new-user-last-name-label">
              Last name
              <input
                type="text"
                value={newUserForm.last_name}
                onChange={(event) => setNewUserForm({ ...newUserForm, last_name: event.target.value })}
                {...domIdAttrs('admin-new-user-last-name')}
                required
              />
            </label>
            <label id="admin-new-user-email-label">
              Email
              <input
                type="email"
                value={newUserForm.email}
                onChange={(event) => setNewUserForm({ ...newUserForm, email: event.target.value })}
                {...domIdAttrs('admin-new-user-email')}
                required
              />
            </label>
            <label id="admin-new-user-password-label">
              Password
              <input
                type="password"
                value={newUserForm.password}
                onChange={(event) => setNewUserForm({ ...newUserForm, password: event.target.value })}
                {...domIdAttrs('admin-new-user-password')}
                required
              />
            </label>
            <label id="admin-new-user-role-label">
              Role
              <select
                value={newUserForm.role}
                onChange={(event) => {
                  const role = event.target.value as UserRole;
                  setNewUserForm({
                    ...newUserForm,
                    role,
                    category_id: normalizeOperatorCategory(role, newUserForm.category_id, activeCategories),
                  });
                }}
                {...domIdAttrs('admin-new-user-role')}
              >
                {(referenceData?.roles ?? []).map((role) => (
                  <option key={role} value={role} {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminNewUserRoleOption, role))}>{role}</option>
                ))}
              </select>
            </label>
            <label id="admin-new-user-category-label">
              Category
              <select
                value={newUserForm.category_id ?? ''}
                onChange={(event) => setNewUserForm({ ...newUserForm, category_id: parseCategoryId(event.target.value) })}
                disabled={newUserForm.role !== 'operator'}
                {...domIdAttrs('admin-new-user-category')}
              >
                <option value="" {...domIdAttrs('admin-new-user-category-option-none')}>No category</option>
                {activeCategories.map((category) => (
                  <option
                    key={category.id}
                    value={category.id}
                    {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminCategoryOption, category.id))}
                  >
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="checkbox-row" id="admin-new-user-active-label">
              <input
                type="checkbox"
                checked={newUserForm.is_active}
                onChange={(event) => setNewUserForm({ ...newUserForm, is_active: event.target.checked })}
                {...domIdAttrs('admin-new-user-active')}
              />
              Active
            </label>
            <label className="checkbox-row" id="admin-new-user-email-notifications-label">
              <input
                type="checkbox"
                checked={newUserForm.email_notifications_enabled}
                onChange={(event) => setNewUserForm({ ...newUserForm, email_notifications_enabled: event.target.checked })}
                {...domIdAttrs('admin-new-user-email-notifications')}
              />
              Email notifications enabled
            </label>
            <div className="button-row" id="admin-new-user-actions">
              <button type="submit" {...domIdAttrs('admin-new-user-submit')}>Create user</button>
            </div>
          </form>
        </div>

        <div className="card" {...domIdAttrs('admin-create-category-card')}>
          <h2 id="admin-create-category-title">Create category</h2>
          <form className="form-grid compact-grid" onSubmit={handleCreateCategory} {...domIdAttrs('admin-category-form')}>
            <label id="admin-new-category-name-label">
              Category name
              <input
                type="text"
                value={newCategoryName}
                onChange={(event) => setNewCategoryName(event.target.value)}
                {...domIdAttrs('admin-new-category-name')}
                required
              />
            </label>
            <div className="button-row" id="admin-new-category-actions">
              <button type="submit" {...domIdAttrs('admin-new-category-submit')}>Create category</button>
            </div>
          </form>
        </div>
      </section>

      <section className="card" {...domIdAttrs('admin-users-section')}>
        <h2 id="admin-users-title">Users</h2>
        <table className="data-table" {...domIdAttrs('admin-users-table')}>
          <thead id="admin-users-table-head">
            <tr id="admin-users-header-row">
              <th id="admin-users-header-id">ID</th>
              <th id="admin-users-header-identity">Identity</th>
              <th id="admin-users-header-email">Email</th>
              <th id="admin-users-header-role">Role</th>
              <th id="admin-users-header-category">Category</th>
              <th id="admin-users-header-flags">Flags</th>
              <th id="admin-users-header-actions"></th>
            </tr>
          </thead>
          <tbody id="admin-users-table-body">
            {users.map((user) => {
              const editableUser = editedUsers[user.id] ?? buildEditableUser(user);
              const rowId = prefixedDomId(DOM_ID_PREFIXES.adminUserRow, user.id);
              return (
                <tr key={user.id} {...domIdAttrs(rowId)}>
                  <td id={childDomId(rowId, 'id')}>#{user.id}</td>
                  <td id={childDomId(rowId, 'identity')}>
                    <div className="inline-grid" id={childDomId(rowId, 'identity-fields')}>
                      <input
                        type="text"
                        value={editableUser.first_name}
                        onChange={(event) => updateEditedUser(user, { first_name: event.target.value })}
                        {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserFirstName, user.id))}
                      />
                      <input
                        type="text"
                        value={editableUser.last_name}
                        onChange={(event) => updateEditedUser(user, { last_name: event.target.value })}
                        {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserLastName, user.id))}
                      />
                    </div>
                  </td>
                  <td id={childDomId(rowId, 'email-cell')}>
                    <input
                      type="email"
                      value={editableUser.email}
                      onChange={(event) => updateEditedUser(user, { email: event.target.value })}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserEmail, user.id))}
                    />
                  </td>
                  <td id={childDomId(rowId, 'role-cell')}>
                    <select
                      value={editableUser.role}
                      onChange={(event) => {
                        const role = event.target.value as UserRole;
                        updateEditedUser(user, {
                          role,
                          category_id: normalizeOperatorCategory(role, editableUser.category_id, activeCategories),
                        });
                      }}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserRole, user.id))}
                    >
                      {(referenceData?.roles ?? []).map((role) => (
                        <option key={role} value={role} {...domIdAttrs(childDomId(prefixedDomId(DOM_ID_PREFIXES.adminUserRole, user.id), role))}>{role}</option>
                      ))}
                    </select>
                  </td>
                  <td id={childDomId(rowId, 'category-cell')}>
                    <select
                      value={editableUser.category_id ?? ''}
                      onChange={(event) => updateEditedUser(user, { category_id: parseCategoryId(event.target.value) })}
                      disabled={editableUser.role !== 'operator'}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserCategory, user.id))}
                    >
                      <option value="" {...domIdAttrs(childDomId(prefixedDomId(DOM_ID_PREFIXES.adminUserCategory, user.id), 'none'))}>No category</option>
                      {activeCategories.map((category) => (
                        <option
                          key={category.id}
                          value={category.id}
                          {...domIdAttrs(childDomId(prefixedDomId(DOM_ID_PREFIXES.adminUserCategory, user.id), category.id))}
                        >
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td id={childDomId(rowId, 'flags')}>
                    <label className="checkbox-row compact-checkbox" id={childDomId(rowId, 'active-label')}>
                      <input
                        type="checkbox"
                        checked={editableUser.is_active}
                        onChange={(event) => updateEditedUser(user, { is_active: event.target.checked })}
                        {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserStatus, user.id))}
                      />
                      Active
                    </label>
                    <label className="checkbox-row compact-checkbox" id={childDomId(rowId, 'email-notifications-label')}>
                      <input
                        type="checkbox"
                        checked={editableUser.email_notifications_enabled}
                        onChange={(event) => updateEditedUser(user, { email_notifications_enabled: event.target.checked })}
                        {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserEmailNotifications, user.id))}
                      />
                      Email
                    </label>
                  </td>
                  <td id={childDomId(rowId, 'actions')}>
                    <button
                      type="button"
                      onClick={() => handleUpdateUser(user.id)}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminUserSave, user.id))}
                    >
                      Save
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <section className="card" {...domIdAttrs('admin-categories-section')}>
        <h2 id="admin-categories-title">Categories</h2>
        <table className="data-table" {...domIdAttrs('admin-categories-table')}>
          <thead id="admin-categories-table-head">
            <tr id="admin-categories-header-row">
              <th id="admin-categories-header-id">ID</th>
              <th id="admin-categories-header-name">Name</th>
              <th id="admin-categories-header-active">Active</th>
              <th id="admin-categories-header-actions"></th>
            </tr>
          </thead>
          <tbody id="admin-categories-table-body">
            {categories.map((category) => {
              const editableCategory = editedCategories[category.id] ?? buildEditableCategory(category);
              const rowId = prefixedDomId(DOM_ID_PREFIXES.adminCategoryRow, category.id);
              return (
                <tr key={category.id} {...domIdAttrs(rowId)}>
                  <td id={childDomId(rowId, 'id')}>#{category.id}</td>
                  <td id={childDomId(rowId, 'name-cell')}>
                    <input
                      type="text"
                      value={editableCategory.name}
                      onChange={(event) => updateEditedCategory(category, { name: event.target.value })}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminCategoryName, category.id))}
                    />
                  </td>
                  <td id={childDomId(rowId, 'active-cell')}>
                    <label className="checkbox-row compact-checkbox" id={childDomId(rowId, 'active-label')}>
                      <input
                        type="checkbox"
                        checked={editableCategory.is_active}
                        onChange={(event) => updateEditedCategory(category, { is_active: event.target.checked })}
                        {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminCategoryActive, category.id))}
                      />
                      Active
                    </label>
                  </td>
                  <td id={childDomId(rowId, 'actions')}>
                    <button
                      type="button"
                      onClick={() => handleUpdateCategory(category.id)}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.adminCategorySave, category.id))}
                    >
                      Save
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      <section className="card" {...domIdAttrs('admin-statistics-section')}>
        <h2 id="admin-statistics-title">Statistics</h2>
        <div className="stats-grid" {...domIdAttrs('admin-stats-grid')}>
          {statistics ? renderMetricList('Reports by status', statistics.reports_by_status) : null}
          {statistics ? renderMetricList('Reports by type', statistics.reports_by_type) : null}
          {statistics ? renderMetricList('Reports by reporter', statistics.reports_by_reporter) : null}
          {statistics ? renderMetricList('Top 1 percent by type', statistics.top_1_percent_by_type) : null}
          {statistics ? renderMetricList('Top 5 percent by type', statistics.top_5_percent_by_type) : null}
        </div>
      </section>
    </div>
  );
}

export const DOM_ID_PREFIXES = {
  adminCategoryActive: 'admin-category-active-',
  adminCategoryName: 'admin-category-name-',
  adminCategoryOption: 'admin-category-option-',
  adminCategoryRow: 'admin-category-row-',
  adminCategorySave: 'admin-category-save-',
  adminMetricItem: 'admin-metric-item-',
  adminNewUserRoleOption: 'admin-new-user-role-option-',
  adminUserCategory: 'admin-user-category-',
  adminUserEmail: 'admin-user-email-',
  adminUserEmailNotifications: 'admin-user-email-notifications-',
  adminUserFirstName: 'admin-user-first-name-',
  adminUserLastName: 'admin-user-last-name-',
  adminUserRole: 'admin-user-role-',
  adminUserRow: 'admin-user-row-',
  adminUserSave: 'admin-user-save-',
  adminUserStatus: 'admin-user-status-',
  assignedReportNote: 'assigned-report-note-',
  assignedReportRow: 'assigned-report-row-',
  assignedReportStatus: 'assigned-report-status-',
  assignedReportUnread: 'assigned-report-unread-',
  assignedReportUpdate: 'assigned-report-update-',
  categoryOption: 'category-option-',
  messageItem: 'message-item-',
  notificationItem: 'notification-item-',
  notificationRead: 'notification-read-',
  pendingReportAssign: 'pending-report-assign-',
  pendingReportRow: 'pending-report-row-',
  photoItem: 'photo-item-',
  myReportRow: 'my-report-row-',
  publicCategoryStat: 'public-category-stat-',
  publicReportRow: 'public-report-row-',
  publicStatusOption: 'public-status-option-',
  publicTrendStat: 'public-trend-stat-',
  statusHistoryItem: 'status-history-item-',
} as const;

function normalizeDomIdPart(value: string | number): string {
  const normalizedValue = String(value)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return normalizedValue || 'empty';
}

export function prefixedDomId(prefix: string, value: string | number): string {
  return `${prefix}${normalizeDomIdPart(value)}`;
}

export function childDomId(parentId: string, childName: string | number): string {
  return `${parentId}-${normalizeDomIdPart(childName)}`;
}

export function domIdAttrs(id: string): { id: string } {
  return { id };
}

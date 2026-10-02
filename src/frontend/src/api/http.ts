import { API_BASE_URL, BACKEND_BASE_URL } from '../config';
import type {
  AdminStatisticsDto,
  AuthResponseDto,
  CategoryDto,
  MessageDto,
  NotificationDto,
  PublicStatisticsDto,
  ReferenceDataDto,
  ReportDetailDto,
  ReportSummaryDto,
  UserDto,
} from '../types/api';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new ApiError(payload?.error ?? 'Unexpected API error.', response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function requestForm<T>(path: string, formData: FormData, method: 'POST' | 'PUT' = 'POST'): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new ApiError(payload?.error ?? 'Unexpected API error.', response.status);
  }

  return (await response.json()) as T;
}

export function buildMediaUrl(relativeUrl: string | null | undefined): string | null {
  if (!relativeUrl) {
    return null;
  }
  if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) {
    return relativeUrl;
  }
  return `${BACKEND_BASE_URL}${relativeUrl}`;
}

export const apiClient = {
  getReferenceData(): Promise<ReferenceDataDto> {
    return requestJson<ReferenceDataDto>('/meta/reference-data');
  },
  getCategories(): Promise<CategoryDto[]> {
    return requestJson<CategoryDto[]>('/categories');
  },
  getPublicReports(queryString = ''): Promise<ReportSummaryDto[]> {
    return requestJson<ReportSummaryDto[]>(`/reports${queryString}`);
  },
  getReportDetail(reportId: number): Promise<ReportDetailDto> {
    return requestJson<ReportDetailDto>(`/reports/${reportId}`);
  },
  exportReportsUrl(queryString = ''): string {
    return `${API_BASE_URL}/reports/export${queryString}`;
  },
  getPublicStatistics(granularity = 'day'): Promise<PublicStatisticsDto> {
    return requestJson<PublicStatisticsDto>(`/stats/public?granularity=${granularity}`);
  },
  register(payload: Record<string, string>): Promise<AuthResponseDto> {
    return requestJson<AuthResponseDto>('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
  login(identifier: string, password: string): Promise<{ message: string; user: UserDto }> {
    return requestJson<{ message: string; user: UserDto }>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password }),
    });
  },
  logout(): Promise<{ message: string }> {
    return requestJson<{ message: string }>('/auth/logout', { method: 'POST' });
  },
  getCurrentUser(): Promise<UserDto> {
    return requestJson<UserDto>('/users/me');
  },
  updateCurrentUser(formData: FormData): Promise<UserDto> {
    return requestForm<UserDto>('/users/me', formData, 'PUT');
  },
  deleteCurrentUser(): Promise<{ message: string }> {
    return requestJson<{ message: string }>('/users/me', { method: 'DELETE' });
  },
  getMyReports(): Promise<ReportSummaryDto[]> {
    return requestJson<ReportSummaryDto[]>('/users/me/reports');
  },
  getMyNotifications(): Promise<NotificationDto[]> {
    return requestJson<NotificationDto[]>('/users/me/notifications');
  },
  markNotificationAsRead(notificationId: number): Promise<NotificationDto> {
    return requestJson<NotificationDto>(`/users/me/notifications/${notificationId}/read`, { method: 'POST' });
  },
  createReport(formData: FormData): Promise<ReportDetailDto> {
    return requestForm<ReportDetailDto>('/reports', formData, 'POST');
  },
  followReport(reportId: number): Promise<ReportDetailDto> {
    return requestJson<ReportDetailDto>(`/reports/${reportId}/follow`, { method: 'POST' });
  },
  unfollowReport(reportId: number): Promise<ReportDetailDto> {
    return requestJson<ReportDetailDto>(`/reports/${reportId}/follow`, { method: 'DELETE' });
  },
  sendReportMessage(reportId: number, body: string): Promise<MessageDto> {
    return requestJson<MessageDto>(`/reports/${reportId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body }),
    });
  },
  getOperatorPendingReports(): Promise<ReportSummaryDto[]> {
    return requestJson<ReportSummaryDto[]>('/operator/reports/pending');
  },
  getOperatorAssignedReports(): Promise<ReportSummaryDto[]> {
    return requestJson<ReportSummaryDto[]>('/operator/reports/assigned');
  },
  assignReport(reportId: number): Promise<ReportDetailDto> {
    return requestJson<ReportDetailDto>(`/operator/reports/${reportId}/assign`, {
      method: 'POST',
    });
  },
  updateReportStatus(reportId: number, status: string, note: string): Promise<ReportDetailDto> {
    return requestJson<ReportDetailDto>(`/operator/reports/${reportId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, note }),
    });
  },
  getAdminUsers(): Promise<UserDto[]> {
    return requestJson<UserDto[]>('/admin/users');
  },
  createAdminUser(payload: object): Promise<UserDto> {
    return requestJson<UserDto>('/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
  updateAdminUser(userId: number, payload: object): Promise<UserDto> {
    return requestJson<UserDto>(`/admin/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
  getAdminCategories(): Promise<CategoryDto[]> {
    return requestJson<CategoryDto[]>('/admin/categories');
  },
  createCategory(name: string): Promise<CategoryDto> {
    return requestJson<CategoryDto>('/admin/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
  },
  updateCategory(categoryId: number, payload: object): Promise<CategoryDto> {
    return requestJson<CategoryDto>(`/admin/categories/${categoryId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
  getAdminStatistics(): Promise<AdminStatisticsDto> {
    return requestJson<AdminStatisticsDto>('/admin/stats');
  },
};

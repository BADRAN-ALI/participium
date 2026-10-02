export type UserRole = 'citizen' | 'operator' | 'admin';

export interface ApiErrorPayload {
  error?: string;
}

export interface UserDto {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  category_id: number | null;
  category: CategoryDto | null;
  is_active: boolean;
  is_email_verified: boolean;
  email_notifications_enabled: boolean;
  profile_picture_path: string | null;
  profile_picture_url: string | null;
  created_at: string | null;
}

export interface CategoryDto {
  id: number;
  name: string;
  is_active: boolean;
  created_at: string | null;
}

export interface MessagePartyDto {
  id: number | null;
  display_name: string;
  role: UserRole | null;
}

export interface MessageDto {
  id: number;
  report_id: number;
  body: string;
  sender: MessagePartyDto;
  recipient: MessagePartyDto;
  created_at: string | null;
}

export interface NotificationDto {
  id: number;
  type: string;
  title: string;
  body: string;
  report_id: number | null;
  is_read: boolean;
  created_at: string | null;
}

export interface PhotoDto {
  id: number;
  file_path: string;
  url: string | null;
  original_filename: string;
  content_type: string | null;
}

export interface ReportPartyDto {
  id: number | null;
  display_name: string;
  role?: UserRole | null;
}

export interface ReportStatusHistoryDto {
  id: number;
  previous_status: string | null;
  new_status: string;
  note: string | null;
  changed_by: ReportPartyDto;
  created_at: string | null;
}

export interface ReportSummaryDto {
  id: number;
  title: string;
  description: string;
  category: CategoryDto;
  status: string;
  rejection_reason: string | null;
  is_anonymous: boolean;
  reporter: ReportPartyDto;
  latitude: number;
  longitude: number;
  photos: PhotoDto[];
  followers_count: number;
  is_followed_by_current_user: boolean;
  is_public: boolean;
  created_at: string | null;
  updated_at: string | null;
  unread_message_count?: number;
}

export interface ReportDetailDto extends ReportSummaryDto {
  can_access_messages: boolean;
  status_history: ReportStatusHistoryDto[];
  messages?: MessageDto[];
}

export interface PublicStatisticsDto {
  reports_by_category: Record<string, number>;
  trends: Record<string, number>;
  total_reports: number;
}

export interface AdminStatisticsDto {
  reports_by_status: Record<string, number>;
  reports_by_type: Record<string, number>;
  reports_by_type_and_status: Record<string, number>;
  reports_by_reporter: Record<string, number>;
  reports_by_reporter_and_type: Record<string, number>;
  reports_by_reporter_type_and_status: Record<string, number>;
  top_1_percent_by_type: Record<string, number>;
  top_5_percent_by_type: Record<string, number>;
}

export interface AuthResponseDto {
  user: UserDto;
  verification_url?: string;
}

export interface ReferenceDataDto {
  roles: UserRole[];
  report_statuses: string[];
  public_report_statuses: string[];
}

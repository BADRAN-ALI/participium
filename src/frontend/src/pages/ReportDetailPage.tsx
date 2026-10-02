import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError, apiClient, buildMediaUrl } from '../api/http';
import { MapPanel } from '../components/MapPanel';
import { useAuth } from '../hooks/useAuth';
import { DOM_ID_PREFIXES, childDomId, prefixedDomId, domIdAttrs } from '../domIds';
import type { ReportDetailDto } from '../types/api';

function formatDateTime(value: string | null): string {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleString();
}

export function ReportDetailPage() {
  const { reportId } = useParams();
  const { user } = useAuth();
  const [report, setReport] = useState<ReportDetailDto | null>(null);
  const [messageBody, setMessageBody] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  async function loadReport(): Promise<void> {
    if (!reportId) {
      setError('Missing report id.');
      setLoading(false);
      return;
    }
    try {
      const nextReport = await apiClient.getReportDetail(Number(reportId));
      setReport(nextReport);
      setError('');
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to load report detail.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, [reportId]);

  async function handleFollowToggle(): Promise<void> {
    if (!report) {
      return;
    }
    try {
      const nextReport = report.is_followed_by_current_user
        ? await apiClient.unfollowReport(report.id)
        : await apiClient.followReport(report.id);
      setReport(nextReport);
      setError('');
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to update follow status.');
    }
  }

  async function handleMessageSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!report) {
      return;
    }
    setIsSubmitting(true);
    try {
      await apiClient.sendReportMessage(report.id, messageBody);
      setMessageBody('');
      await loadReport();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to send the message.');
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return <section className="card" {...domIdAttrs('report-detail-loading')}>Loading report...</section>;
  }

  if (!report) {
    return (
      <section className="card" {...domIdAttrs('report-detail-page')}>
        <h1 id="report-detail-unavailable-title">Report detail</h1>
        <p className="error-text" {...domIdAttrs('report-detail-error')}>{error || 'Report not available.'}</p>
      </section>
    );
  }

  return (
    <div className="page-grid" {...domIdAttrs('report-detail-page')}>
      <section className="card" {...domIdAttrs('report-detail-summary-section')}>
        <div className="title-row" id="report-detail-title-row">
          <div id="report-detail-title-block">
            <h1 id="report-detail-title">{report.title}</h1>
            <p className="muted-text" {...domIdAttrs('report-detail-status')}>Status: {report.status}</p>
          </div>
          {user?.role === 'citizen' && report.is_public ? (
            <button type="button" onClick={handleFollowToggle} {...domIdAttrs('follow-button')}>
              {report.is_followed_by_current_user ? 'Unfollow report' : 'Follow report'}
            </button>
          ) : null}
        </div>
        <p {...domIdAttrs('report-detail-description')}>{report.description}</p>
        {report.rejection_reason ? <p className="error-text" {...domIdAttrs('report-detail-rejection-reason')}>Rejection reason: {report.rejection_reason}</p> : null}
        {error ? <p className="error-text" {...domIdAttrs('report-detail-error')}>{error}</p> : null}
        <div className="detail-grid" {...domIdAttrs('report-detail-metadata')}>
          <div {...domIdAttrs('report-detail-category')}>
            <strong id="report-detail-category-label">Category</strong>
            <p id="report-detail-category-value">{report.category.name}</p>
          </div>
          <div {...domIdAttrs('report-detail-reporter')}>
            <strong id="report-detail-reporter-label">Reporter</strong>
            <p id="report-detail-reporter-value">{report.reporter.display_name}</p>
          </div>
          <div {...domIdAttrs('report-detail-followers')}>
            <strong id="report-detail-followers-label">Followers</strong>
            <p id="report-detail-followers-value">{report.followers_count}</p>
          </div>
          <div {...domIdAttrs('report-detail-created')}>
            <strong id="report-detail-created-label">Created</strong>
            <p id="report-detail-created-value">{formatDateTime(report.created_at)}</p>
          </div>
          <div {...domIdAttrs('report-detail-updated')}>
            <strong id="report-detail-updated-label">Updated</strong>
            <p id="report-detail-updated-value">{formatDateTime(report.updated_at)}</p>
          </div>
        </div>
      </section>

      <section className="split-grid" {...domIdAttrs('report-detail-media-section')}>
        <div className="card" {...domIdAttrs('report-detail-map-card')}>
          <h2 id="report-detail-map-title">Location</h2>
          <MapPanel reports={[report]} mapId="report-detail-map" />
        </div>
        <div className="card" {...domIdAttrs('report-detail-photos-card')}>
          <h2 id="report-detail-photos-title">Photos</h2>
          <div className="photo-grid" {...domIdAttrs('report-detail-photo-grid')}>
            {report.photos.length === 0 ? <p {...domIdAttrs('report-detail-no-photos')}>No photos uploaded.</p> : null}
            {report.photos.map((photo) => {
              const mediaUrl = buildMediaUrl(photo.url);
              const photoId = prefixedDomId(DOM_ID_PREFIXES.photoItem, photo.id);
              return mediaUrl ? (
                <img key={photo.id} className="detail-photo" src={mediaUrl} alt={photo.original_filename} {...domIdAttrs(photoId)} />
              ) : null;
            })}
          </div>
        </div>
      </section>

      <section className="split-grid" {...domIdAttrs('report-detail-activity-section')}>
        <div className="card" {...domIdAttrs('status-history-card')}>
          <h2 id="status-history-title">Status history</h2>
          <ul className="stack-list" {...domIdAttrs('status-history-list')}>
            {report.status_history.map((item) => {
              const itemId = prefixedDomId(DOM_ID_PREFIXES.statusHistoryItem, item.id);
              return (
                <li key={item.id} className="list-card" {...domIdAttrs(itemId)}>
                  <div className="list-card-header" id={childDomId(itemId, 'header')}>
                    <strong id={childDomId(itemId, 'status')}>{item.new_status}</strong>
                    <span id={childDomId(itemId, 'created')}>{formatDateTime(item.created_at)}</span>
                  </div>
                  <p id={childDomId(itemId, 'changed-by')}>Changed by: {item.changed_by.display_name}</p>
                  {item.note ? <p id={childDomId(itemId, 'note')}>{item.note}</p> : null}
                </li>
              );
            })}
          </ul>
        </div>

        <div className="card" {...domIdAttrs('messages-card')}>
          <h2 id="messages-title">Conversation</h2>
          {!report.can_access_messages ? <p className="muted-text" {...domIdAttrs('messages-unavailable')}>No message thread is available for the current user.</p> : null}
          {report.can_access_messages ? (
            <>
              <ul className="stack-list" {...domIdAttrs('messages-list')}>
                {(report.messages ?? []).map((message) => {
                  const messageId = prefixedDomId(DOM_ID_PREFIXES.messageItem, message.id);
                  return (
                    <li key={message.id} className="list-card" {...domIdAttrs(messageId)}>
                      <div className="list-card-header" id={childDomId(messageId, 'header')}>
                        <strong id={childDomId(messageId, 'sender')}>{message.sender.display_name}</strong>
                        <span id={childDomId(messageId, 'created')}>{formatDateTime(message.created_at)}</span>
                      </div>
                      <p id={childDomId(messageId, 'body')}>{message.body}</p>
                    </li>
                  );
                })}
              </ul>
              <form className="form-grid compact-grid" onSubmit={handleMessageSubmit} {...domIdAttrs('report-message-form')}>
                <label id="report-message-body-label">
                  New message
                  <textarea
                    rows={4}
                    value={messageBody}
                    onChange={(event) => setMessageBody(event.target.value)}
                    {...domIdAttrs('report-message-body')}
                    required
                  />
                </label>
                <div className="button-row" id="report-message-actions">
                  <button type="submit" disabled={isSubmitting} {...domIdAttrs('report-message-submit')}>
                    {isSubmitting ? 'Sending...' : 'Send message'}
                  </button>
                </div>
              </form>
            </>
          ) : null}
        </div>
      </section>
    </div>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { ApiError, apiClient } from '../api/http';
import { DOM_ID_PREFIXES, childDomId, prefixedDomId, domIdAttrs } from '../domIds';
import type { ReferenceDataDto, ReportSummaryDto } from '../types/api';

export function OperatorPage() {
  const [referenceData, setReferenceData] = useState<ReferenceDataDto | null>(null);
  const [pendingReports, setPendingReports] = useState<ReportSummaryDto[]>([]);
  const [assignedReports, setAssignedReports] = useState<ReportSummaryDto[]>([]);
  const [statusByReportId, setStatusByReportId] = useState<Record<number, string>>({});
  const [noteByReportId, setNoteByReportId] = useState<Record<number, string>>({});
  const [error, setError] = useState<string>('');

  async function loadOperatorData(): Promise<void> {
    try {
      const [referencePayload, nextPendingReports, nextAssignedReports] = await Promise.all([
        apiClient.getReferenceData(),
        apiClient.getOperatorPendingReports().catch(() => []),
        apiClient.getOperatorAssignedReports(),
      ]);
      setReferenceData(referencePayload);
      setPendingReports(nextPendingReports);
      setAssignedReports(nextAssignedReports);
      setStatusByReportId((currentValue) => {
        const nextValue = { ...currentValue };
        nextAssignedReports.forEach((report) => {
          nextValue[report.id] = nextValue[report.id] ?? report.status;
        });
        return nextValue;
      });
      setError('');
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to load operator dashboard.');
    }
  }

  useEffect(() => {
    loadOperatorData();
  }, []);

  const availableStatuses = useMemo(() => {
    const allStatuses = referenceData?.report_statuses ?? [];
    return allStatuses.filter((status) => status !== 'Pending Approval');
  }, [referenceData]);

  async function handleAssignReport(reportId: number): Promise<void> {
    try {
      await apiClient.assignReport(reportId);
      await loadOperatorData();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to assign the report.');
    }
  }

  async function handleUpdateStatus(reportId: number): Promise<void> {
    try {
      await apiClient.updateReportStatus(reportId, statusByReportId[reportId] ?? '', noteByReportId[reportId] ?? '');
      await loadOperatorData();
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to update the report status.');
    }
  }

  return (
    <div className="page-grid" {...domIdAttrs('operator-page')}>
      <section className="card" {...domIdAttrs('operator-summary-section')}>
        <h1 id="operator-title">Operator dashboard</h1>
        <p className="muted-text" id="operator-description">Operators manage reports belonging to their category, while administrators can see the full workflow.</p>
        {error ? <p className="error-text" {...domIdAttrs('operator-error')}>{error}</p> : null}
      </section>

      {pendingReports.length > 0 ? (
        <section className="card" {...domIdAttrs('pending-reports-section')}>
          <h2 id="pending-reports-title">Pending reports</h2>
          <table className="data-table" {...domIdAttrs('pending-reports-table')}>
            <thead id="pending-reports-table-head">
              <tr id="pending-reports-header-row">
                <th id="pending-reports-header-id">ID</th>
                <th id="pending-reports-header-title">Title</th>
                <th id="pending-reports-header-category">Category</th>
                <th id="pending-reports-header-actions"></th>
              </tr>
            </thead>
            <tbody id="pending-reports-table-body">
              {pendingReports.map((report) => {
                const rowId = prefixedDomId(DOM_ID_PREFIXES.pendingReportRow, report.id);
                return (
                  <tr key={report.id} {...domIdAttrs(rowId)}>
                    <td id={childDomId(rowId, 'id')}>#{report.id}</td>
                    <td id={childDomId(rowId, 'title')}>{report.title}</td>
                    <td id={childDomId(rowId, 'category')}>{report.category.name}</td>
                    <td id={childDomId(rowId, 'actions')}>
                      <button
                        type="button"
                        onClick={() => handleAssignReport(report.id)}
                        {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.pendingReportAssign, report.id))}
                      >
                        Assign
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      ) : null}

      <section className="card" {...domIdAttrs('assigned-reports-section')}>
        <h2 id="assigned-reports-title">Assigned reports</h2>
        <table className="data-table" {...domIdAttrs('assigned-reports-table')}>
          <thead id="assigned-reports-table-head">
            <tr id="assigned-reports-header-row">
              <th id="assigned-reports-header-id">ID</th>
              <th id="assigned-reports-header-title">Title</th>
              <th id="assigned-reports-header-category">Category</th>
              <th id="assigned-reports-header-status">Status</th>
              <th id="assigned-reports-header-unread">Unread messages</th>
              <th id="assigned-reports-header-note">Note</th>
              <th id="assigned-reports-header-actions"></th>
            </tr>
          </thead>
          <tbody id="assigned-reports-table-body">
            {assignedReports.map((report) => {
              const rowId = prefixedDomId(DOM_ID_PREFIXES.assignedReportRow, report.id);
              return (
                <tr key={report.id} {...domIdAttrs(rowId)}>
                  <td id={childDomId(rowId, 'id')}>#{report.id}</td>
                  <td id={childDomId(rowId, 'title-cell')}>
                    <div id={childDomId(rowId, 'title')}>{report.title}</div>
                    <Link to={`/reports/${report.id}`} {...domIdAttrs(childDomId(rowId, 'open-detail'))}>Open detail</Link>
                  </td>
                  <td id={childDomId(rowId, 'category')}>{report.category.name}</td>
                  <td id={childDomId(rowId, 'status-cell')}>
                    <select
                      value={statusByReportId[report.id] ?? report.status}
                      onChange={(event) => setStatusByReportId({ ...statusByReportId, [report.id]: event.target.value })}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.assignedReportStatus, report.id))}
                    >
                      {availableStatuses.map((status) => (
                        <option
                          key={status}
                          value={status}
                          {...domIdAttrs(childDomId(prefixedDomId(DOM_ID_PREFIXES.assignedReportStatus, report.id), status))}
                        >
                          {status}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.assignedReportUnread, report.id))}>{report.unread_message_count ?? 0}</td>
                  <td id={childDomId(rowId, 'note-cell')}>
                    <input
                      type="text"
                      value={noteByReportId[report.id] ?? ''}
                      onChange={(event) => setNoteByReportId({ ...noteByReportId, [report.id]: event.target.value })}
                      placeholder="Optional note"
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.assignedReportNote, report.id))}
                    />
                  </td>
                  <td id={childDomId(rowId, 'actions')}>
                    <button
                      type="button"
                      onClick={() => handleUpdateStatus(report.id)}
                      {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.assignedReportUpdate, report.id))}
                    >
                      Update
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}

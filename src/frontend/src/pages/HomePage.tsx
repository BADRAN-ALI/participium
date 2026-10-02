import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { ApiError, apiClient, buildMediaUrl } from '../api/http';
import { MapPanel } from '../components/MapPanel';
import { DOM_ID_PREFIXES, childDomId, prefixedDomId, domIdAttrs } from '../domIds';
import type { CategoryDto, PublicStatisticsDto, ReferenceDataDto, ReportSummaryDto } from '../types/api';

interface FilterState {
  categoryId: string;
  status: string;
  dateFrom: string;
  dateTo: string;
  sort: 'asc' | 'desc';
}

const initialFilters: FilterState = {
  categoryId: '',
  status: '',
  dateFrom: '',
  dateTo: '',
  sort: 'desc',
};

function buildQueryString(filters: FilterState): string {
  const params = new URLSearchParams();
  if (filters.categoryId) params.set('category_id', filters.categoryId);
  if (filters.status) params.set('status', filters.status);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.sort) params.set('sort', filters.sort);
  const queryString = params.toString();
  return queryString ? `?${queryString}` : '';
}

export function HomePage() {
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const [granularity, setGranularity] = useState<string>('day');
  const [categories, setCategories] = useState<CategoryDto[]>([]);
  const [referenceData, setReferenceData] = useState<ReferenceDataDto | null>(null);
  const [reports, setReports] = useState<ReportSummaryDto[]>([]);
  const [stats, setStats] = useState<PublicStatisticsDto | null>(null);
  const [error, setError] = useState<string>('');

  const queryString = useMemo(() => buildQueryString(filters), [filters]);

  useEffect(() => {
    Promise.all([apiClient.getCategories(), apiClient.getReferenceData()])
      .then(([nextCategories, nextReferenceData]) => {
        setCategories(nextCategories);
        setReferenceData(nextReferenceData);
      })
      .catch(() => setError('Unable to load categories.'));
  }, []);

  useEffect(() => {
    Promise.all([
      apiClient.getPublicReports(queryString),
      apiClient.getPublicStatistics(granularity),
    ])
      .then(([nextReports, nextStats]) => {
        setReports(nextReports);
        setStats(nextStats);
        setError('');
      })
      .catch((apiError: unknown) => {
        setError(apiError instanceof ApiError ? apiError.message : 'Unable to load public data.');
      });
  }, [queryString, granularity]);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    setFilters((currentFilters) => ({ ...currentFilters }));
  }

  return (
    <div className="page-grid" {...domIdAttrs('home-page-grid')}>
      <section className="hero-card card" {...domIdAttrs('home-page')}>
        <div id="home-hero-copy">
          <h1 id="home-hero-title">Participium public portal</h1>
          <p className="muted-text" id="home-hero-description">
            Browse published reports, inspect progress and export the public report list.
          </p>
        </div>
        <div className="hero-actions" id="home-hero-actions">
          <Link className="primary-link" to="/register" {...domIdAttrs('register-link')}>Create account</Link>
          <Link className="secondary-link" to="/login" {...domIdAttrs('login-link')}>Login</Link>
        </div>
      </section>

      <section className="card" {...domIdAttrs('public-filter-section')}>
        <h2 id="public-filter-title">Filter published reports</h2>
        <form className="form-grid compact-grid" onSubmit={handleSubmit} {...domIdAttrs('public-filter-form')}>
          <label id="public-filter-category-label">
            Category
            <select
              value={filters.categoryId}
              onChange={(event) => setFilters({ ...filters, categoryId: event.target.value })}
              {...domIdAttrs('public-filter-category')}
            >
              <option value="" {...domIdAttrs('public-filter-category-option-all')}>All</option>
              {categories.map((category) => (
                <option
                  key={category.id}
                  value={category.id}
                  {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.categoryOption, category.id))}
                >
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label id="public-filter-status-label">
            Status
            <select
              value={filters.status}
              onChange={(event) => setFilters({ ...filters, status: event.target.value })}
              {...domIdAttrs('public-filter-status')}
            >
              <option value="" {...domIdAttrs('public-filter-status-option-all')}>All public statuses</option>
              {(referenceData?.public_report_statuses ?? []).map((status) => (
                <option
                  key={status}
                  value={status}
                  {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.publicStatusOption, status))}
                >
                  {status}
                </option>
              ))}
            </select>
          </label>
          <label id="public-filter-date-from-label">
            Date from
            <input
              type="datetime-local"
              value={filters.dateFrom}
              onChange={(event) => setFilters({ ...filters, dateFrom: event.target.value })}
              {...domIdAttrs('public-filter-date-from')}
            />
          </label>
          <label id="public-filter-date-to-label">
            Date to
            <input
              type="datetime-local"
              value={filters.dateTo}
              onChange={(event) => setFilters({ ...filters, dateTo: event.target.value })}
              {...domIdAttrs('public-filter-date-to')}
            />
          </label>
          <label id="public-filter-sort-label">
            Order
            <select
              value={filters.sort}
              onChange={(event) => setFilters({ ...filters, sort: event.target.value as 'asc' | 'desc' })}
              {...domIdAttrs('public-filter-sort')}
            >
              <option value="desc" {...domIdAttrs('public-filter-sort-option-desc')}>Newest first</option>
              <option value="asc" {...domIdAttrs('public-filter-sort-option-asc')}>Oldest first</option>
            </select>
          </label>
          <label id="public-stat-granularity-label">
            Trend granularity
            <select
              value={granularity}
              onChange={(event) => setGranularity(event.target.value)}
              {...domIdAttrs('public-stat-granularity')}
            >
              <option value="day" {...domIdAttrs('public-stat-granularity-option-day')}>Day</option>
              <option value="week" {...domIdAttrs('public-stat-granularity-option-week')}>Week</option>
              <option value="month" {...domIdAttrs('public-stat-granularity-option-month')}>Month</option>
            </select>
          </label>
          <div className="button-row" id="public-filter-actions">
            <button type="submit" {...domIdAttrs('public-filter-submit')}>Apply filters</button>
            <a className="secondary-link" href={apiClient.exportReportsUrl(queryString)} target="_blank" rel="noreferrer" {...domIdAttrs('public-export-link')}>Export CSV</a>
          </div>
        </form>
        {error ? <p className="error-text" {...domIdAttrs('public-filter-error')}>{error}</p> : null}
      </section>

      <section className="split-grid" {...domIdAttrs('public-overview-section')}>
        <div className="card" {...domIdAttrs('public-map-card')}>
          <h2 id="public-map-title">Map</h2>
          <MapPanel reports={reports} mapId="public-map" />
        </div>
        <div className="card" {...domIdAttrs('public-statistics-card')}>
          <h2 id="public-statistics-title">Public statistics</h2>
          <div className="stats-grid" {...domIdAttrs('public-statistics-grid')}>
            <div className="metric-box" {...domIdAttrs('public-total-reports-metric')}>
              <span id="public-total-reports-label">Total published reports</span>
              <strong id="public-total-reports-value">{stats?.total_reports ?? 0}</strong>
            </div>
            <div {...domIdAttrs('public-category-statistics')}>
              <h3 id="public-category-statistics-title">Reports by category</h3>
              <ul className="clean-list" {...domIdAttrs('public-category-statistics-list')}>
                {Object.entries(stats?.reports_by_category ?? {}).map(([category, value]) => (
                  <li key={category} {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.publicCategoryStat, category))}>
                    {category}: <strong id={childDomId(prefixedDomId(DOM_ID_PREFIXES.publicCategoryStat, category), 'value')}>{value}</strong>
                  </li>
                ))}
              </ul>
            </div>
            <div {...domIdAttrs('public-trend-statistics')}>
              <h3 id="public-trend-statistics-title">Trend</h3>
              <ul className="clean-list" {...domIdAttrs('public-trend-statistics-list')}>
                {Object.entries(stats?.trends ?? {}).map(([bucket, value]) => (
                  <li key={bucket} {...domIdAttrs(prefixedDomId(DOM_ID_PREFIXES.publicTrendStat, bucket))}>
                    {bucket}: <strong id={childDomId(prefixedDomId(DOM_ID_PREFIXES.publicTrendStat, bucket), 'value')}>{value}</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="card" {...domIdAttrs('public-report-section')}>
        <h2 id="public-report-title">Published reports</h2>
        <table className="data-table" {...domIdAttrs('public-report-table')}>
          <thead id="public-report-table-head">
            <tr id="public-report-header-row">
              <th id="public-report-header-id">ID</th>
              <th id="public-report-header-title">Title</th>
              <th id="public-report-header-status">Status</th>
              <th id="public-report-header-category">Category</th>
              <th id="public-report-header-photo">Photo</th>
              <th id="public-report-header-actions"></th>
            </tr>
          </thead>
          <tbody id="public-report-table-body">
            {reports.map((report) => {
              const firstPhotoUrl = buildMediaUrl(report.photos[0]?.url ?? null);
              const rowId = prefixedDomId(DOM_ID_PREFIXES.publicReportRow, report.id);
              return (
                <tr key={report.id} {...domIdAttrs(rowId)}>
                  <td id={childDomId(rowId, 'id')}>#{report.id}</td>
                  <td id={childDomId(rowId, 'title')}>{report.title}</td>
                  <td id={childDomId(rowId, 'status')}>{report.status}</td>
                  <td id={childDomId(rowId, 'category')}>{report.category.name}</td>
                  <td id={childDomId(rowId, 'photo')}>
                    {firstPhotoUrl ? (
                      <img
                        className="table-thumbnail"
                        src={firstPhotoUrl}
                        alt={report.title}
                        {...domIdAttrs(childDomId(rowId, 'photo-image'))}
                      />
                    ) : 'No photo'}
                  </td>
                  <td id={childDomId(rowId, 'actions')}>
                    <Link to={`/reports/${report.id}`} {...domIdAttrs(childDomId(rowId, 'open-link'))}>Open</Link>
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

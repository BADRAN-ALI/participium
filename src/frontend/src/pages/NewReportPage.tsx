import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiError, apiClient } from '../api/http';
import { MapPanel } from '../components/MapPanel';
import { DOM_ID_PREFIXES, prefixedDomId, domIdAttrs } from '../domIds';
import type { CategoryDto } from '../types/api';

interface ReportFormState {
  title: string;
  description: string;
  categoryId: string;
  latitude: string;
  longitude: string;
  isAnonymous: boolean;
}

const initialForm: ReportFormState = {
  title: '',
  description: '',
  categoryId: '',
  latitude: '45.0703',
  longitude: '7.6869',
  isAnonymous: false,
};

export function NewReportPage() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<CategoryDto[]>([]);
  const [form, setForm] = useState<ReportFormState>(initialForm);
  const [photos, setPhotos] = useState<File[]>([]);
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    apiClient.getCategories()
      .then((items) => {
        setCategories(items);
        if (items.length > 0) {
          setForm((currentForm) => ({
            ...currentForm,
            categoryId: currentForm.categoryId || String(items[0].id),
          }));
        }
      })
      .catch(() => setError('Unable to load categories.'));
  }, []);

  const selectedLocation = useMemo(() => {
    const latitude = Number(form.latitude);
    const longitude = Number(form.longitude);
    if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
      return null;
    }
    return { latitude, longitude };
  }, [form.latitude, form.longitude]);

  function handlePhotoChange(event: ChangeEvent<HTMLInputElement>): void {
    const selectedPhotos = Array.from(event.target.files ?? []);
    if (selectedPhotos.length > 3) {
      setError('A report can contain at most 3 photos. Only the first 3 have been selected.');
    } else {
      setError('');
    }
    setPhotos(selectedPhotos.slice(0, 3));
  }

  function updateLocation(latitude: number, longitude: number): void {
    setForm((currentForm) => ({
      ...currentForm,
      latitude: latitude.toFixed(6),
      longitude: longitude.toFixed(6),
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = new FormData();
      payload.append('title', form.title);
      payload.append('description', form.description);
      payload.append('category_id', form.categoryId);
      payload.append('latitude', form.latitude);
      payload.append('longitude', form.longitude);
      payload.append('is_anonymous', String(form.isAnonymous));
      photos.forEach((photo) => payload.append('photos', photo));

      const report = await apiClient.createReport(payload);
      setError('');
      navigate(`/reports/${report.id}`);
    } catch (apiError: unknown) {
      setError(apiError instanceof ApiError ? apiError.message : 'Unable to create the report.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-grid" {...domIdAttrs('new-report-page')}>
      <section className="card" {...domIdAttrs('new-report-form-section')}>
        <h1 id="new-report-title">Create new report</h1>
        <p className="muted-text" id="new-report-description">The form stays intentionally simple and explicit so that automated tests can target it reliably.</p>
        <form className="form-grid" onSubmit={handleSubmit} {...domIdAttrs('new-report-form')}>
          <label id="report-title-label">
            Title
            <input
              type="text"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              {...domIdAttrs('report-title')}
              required
            />
          </label>
          <label id="report-description-label">
            Description
            <textarea
              rows={5}
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              {...domIdAttrs('report-description')}
              required
            />
          </label>
          <label id="report-category-label">
            Category
            <select
              value={form.categoryId}
              onChange={(event) => setForm({ ...form, categoryId: event.target.value })}
              {...domIdAttrs('report-category')}
              required
            >
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
          <div className="inline-grid" id="report-location-fields">
            <label id="report-latitude-label">
              Latitude
              <input
                type="number"
                step="0.000001"
                value={form.latitude}
                onChange={(event) => setForm({ ...form, latitude: event.target.value })}
                {...domIdAttrs('report-latitude')}
                required
              />
            </label>
            <label id="report-longitude-label">
              Longitude
              <input
                type="number"
                step="0.000001"
                value={form.longitude}
                onChange={(event) => setForm({ ...form, longitude: event.target.value })}
                {...domIdAttrs('report-longitude')}
                required
              />
            </label>
          </div>
          <label className="checkbox-row" id="report-anonymous-label">
            <input
              type="checkbox"
              checked={form.isAnonymous}
              onChange={(event) => setForm({ ...form, isAnonymous: event.target.checked })}
              {...domIdAttrs('report-anonymous')}
            />
            Publish as anonymous citizen
          </label>
          <label id="report-photos-label">
            Photos (1 to 3)
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handlePhotoChange}
              {...domIdAttrs('report-photos')}
              required
            />
          </label>
          <div className="button-row" id="new-report-actions">
            <button type="submit" disabled={isSubmitting} {...domIdAttrs('new-report-submit')}>
              {isSubmitting ? 'Submitting...' : 'Submit report'}
            </button>
          </div>
        </form>
        {error ? <p className="error-text" {...domIdAttrs('new-report-error')}>{error}</p> : null}
        <p className="muted-text" {...domIdAttrs('new-report-selected-photos')}>Selected photos: {photos.length}</p>
      </section>

      <section className="card" {...domIdAttrs('new-report-map-section')}>
        <h2 id="new-report-map-title">Location picker</h2>
        <p className="muted-text" id="new-report-map-description">Click on the map to update latitude and longitude.</p>
        <MapPanel
          selectedLocation={selectedLocation}
          onPickLocation={updateLocation}
          mapId="new-report-map"
        />
      </section>
    </div>
  );
}

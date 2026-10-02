import { useEffect, useRef } from 'react';
import L from 'leaflet';

import { DOM_ID_PREFIXES, childDomId, prefixedDomId, domIdAttrs } from '../domIds';
import type { ReportSummaryDto } from '../types/api';

interface MapPanelProps {
  reports?: ReportSummaryDto[];
  selectedLocation?: { latitude: number; longitude: number } | null;
  onPickLocation?: (latitude: number, longitude: number) => void;
  mapId: string;
}

export function MapPanel({ reports = [], selectedLocation = null, onPickLocation, mapId }: MapPanelProps) {
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerLayerRef = useRef<L.LayerGroup | null>(null);
  const pickMarkerRef = useRef<L.CircleMarker | null>(null);

  function applyLayerDomId(layer: L.CircleMarker, domId: string): void {
    const element = layer.getElement();
    if (element) {
      element.setAttribute('id', domId);
    }
  }

  useEffect(() => {
    if (!mapElementRef.current || mapRef.current) {
      return;
    }

    mapRef.current = L.map(mapElementRef.current).setView([45.0703, 7.6869], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(mapRef.current);
    markerLayerRef.current = L.layerGroup().addTo(mapRef.current);

    if (onPickLocation) {
      mapRef.current.on('click', (event: L.LeafletMouseEvent) => {
        onPickLocation(event.latlng.lat, event.latlng.lng);
      });
    }

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [onPickLocation]);

  useEffect(() => {
    if (!markerLayerRef.current) {
      return;
    }
    markerLayerRef.current.clearLayers();
    reports.forEach((report) => {
      const markerId = prefixedDomId(DOM_ID_PREFIXES.publicReportRow, report.id);
      const popupContent = document.createElement('span');
      popupContent.id = childDomId(markerId, 'map-popup');
      popupContent.textContent = `${report.title} - ${report.status}`;

      const marker = L.circleMarker([report.latitude, report.longitude], {
        radius: 8,
        color: '#0a7f6f',
        fillColor: '#0a7f6f',
        fillOpacity: 0.7,
      })
        .bindPopup(popupContent)
        .addTo(markerLayerRef.current as L.LayerGroup);
      applyLayerDomId(marker, childDomId(markerId, 'map-marker'));
    });
  }, [reports]);

  useEffect(() => {
    if (!mapRef.current || !selectedLocation) {
      return;
    }
    if (!pickMarkerRef.current) {
      pickMarkerRef.current = L.circleMarker([selectedLocation.latitude, selectedLocation.longitude], {
        radius: 9,
        color: '#102a43',
        fillColor: '#102a43',
        fillOpacity: 0.8,
      }).addTo(mapRef.current);
    } else {
      pickMarkerRef.current.setLatLng([selectedLocation.latitude, selectedLocation.longitude]);
    }
    applyLayerDomId(pickMarkerRef.current, childDomId(mapId, 'selected-marker'));
    mapRef.current.setView([selectedLocation.latitude, selectedLocation.longitude], 14);
  }, [mapId, selectedLocation]);

  return <div className="map-panel" ref={mapElementRef} {...domIdAttrs(mapId)} />;
}

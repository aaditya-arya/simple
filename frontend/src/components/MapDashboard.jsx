import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Circle, Polygon, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Video, AlertTriangle } from 'lucide-react';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Gujarat Geographic Bounding Box (Locked to Gujarat)
const GUJARAT_BOUNDS = [
  [19.8, 68.0], // South-West
  [24.9, 74.6]  // North-East
];

const CITY_COORDINATES = {
  "Ahmedabad": [23.0305, 72.5714],
  "Gandhinagar": [23.2156, 72.6369],
  "Surat": [21.1959, 72.8302],
  "Vadodara": [22.3072, 73.1812],
  "Rajkot": [22.3039, 70.8022],
  "Bhavnagar": [21.7645, 72.1519],
  "Jamnagar": [22.4707, 70.0577],
  "all": [22.3500, 71.8000]
};

function ChangeMapView({ city }) {
  const map = useMap();
  useEffect(() => {
    if (city && CITY_COORDINATES[city]) {
      const zoomLevel = city === "all" ? 7.5 : 12;
      map.flyTo(CITY_COORDINATES[city], zoomLevel, { duration: 1.0 });
    }
  }, [city, map]);
  return null;
}

function getMarkerColor(p, showAgeingAlerts) {
  // If Sentinel Real 30 Live Feed -> Pure White Pin
  if (p.is_sentinel_live) {
    return '#ffffff';
  }
  if (showAgeingAlerts && p.is_ageing_alert) {
    return '#f59e0b';
  }
  if (p.connectivity_status === 'online') return '#10b981';
  if (p.connectivity_status === 'offline') return '#ef4444';
  if (p.connectivity_status === 'intermittent') return '#f59e0b';
  return '#94a3b8';
}

function getZoneColor(severity) {
  if (severity === 'Critical Gap') return '#dc2626';
  if (severity === 'Moderate Gap') return '#d97706';
  return '#059669';
}

export function MapDashboard({ 
  geoData, 
  gapData,
  selectedCity,
  selectedCamera, 
  onSelectCamera,
  onOpenLiveStream,
  showCoverageBuffers,
  showGapZones,
  showAgeingAlerts
}) {
  const initialCenter = [22.3500, 71.8000];

  return (
    <div style={{ flex: 1, position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer
        center={initialCenter}
        zoom={7.5}
        minZoom={7}
        maxZoom={18}
        maxBounds={GUJARAT_BOUNDS}
        maxBoundsViscosity={1.0}
        preferCanvas={true}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <ChangeMapView city={selectedCity} />

        {/* Clean Standard OpenStreetMap Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* 1. Visual Gap Analysis Municipal Zone Polygons */}
        {showGapZones && gapData?.identified_gap_zones?.map((zone) => {
          if (!zone.coordinates_polygon || zone.coordinates_polygon.length === 0) return null;
          const latLngs = zone.coordinates_polygon.map(coord => [coord[1], coord[0]]);
          const zoneColor = getZoneColor(zone.gap_severity);

          return (
            <Polygon
              key={zone.zone_id}
              positions={latLngs}
              pathOptions={{
                color: zoneColor,
                fillColor: zoneColor,
                fillOpacity: 0.15,
                weight: 2,
                dashArray: '5, 5'
              }}
            >
              <Popup>
                <div style={{ fontSize: '12px', padding: '4px', fontFamily: 'sans-serif' }}>
                  <div style={{ fontWeight: '700', fontSize: '13px', color: '#0f172a', marginBottom: '4px' }}>
                    {zone.zone_name}
                  </div>
                  <div style={{ color: '#475569' }}>Estimated Area: <strong>{zone.estimated_area_sq_km} km²</strong></div>
                  <div style={{ color: '#475569' }}>Active Cameras: <strong>{zone.active_cameras_count}</strong></div>
                  <div style={{ color: zoneColor, fontWeight: '700', marginTop: '4px' }}>
                    Coverage Density: {zone.coverage_percentage}% ({zone.gap_severity})
                  </div>
                  <div style={{ color: '#2563eb', fontSize: '11px', marginTop: '4px', fontWeight: '600' }}>
                    💡 Required New Cameras: {zone.recommended_new_cameras}
                  </div>
                </div>
              </Popup>
            </Polygon>
          );
        })}

        {/* 2. Optical Lens Coverage Buffers (ST_Buffer Radii around cameras) */}
        {showCoverageBuffers && geoData?.features?.map((feature) => {
          const coords = feature.geometry?.coordinates;
          if (!coords || coords.length < 2) return null;
          const lat = Number(coords[1]);
          const lon = Number(coords[0]);
          if (isNaN(lat) || isNaN(lon)) return null;

          const p = feature.properties;
          const radius = Number(p.coverage_radius_meters) || 75;
          const isSentinel = p.is_sentinel_live;

          return (
            <Circle
              key={`buffer-${p.camera_id}`}
              center={[lat, lon]}
              radius={radius}
              pathOptions={{
                color: isSentinel ? '#2563eb' : '#3b82f6',
                fillColor: isSentinel ? '#60a5fa' : '#93c5fd',
                fillOpacity: isSentinel ? 0.25 : 0.12,
                weight: isSentinel ? 1.5 : 1
              }}
            />
          );
        })}

        {/* 3. Camera Point Markers */}
        {geoData?.features?.map((feature) => {
          const coords = feature.geometry?.coordinates;
          if (!coords || coords.length < 2) return null;
          const lat = Number(coords[1]);
          const lon = Number(coords[0]);
          if (isNaN(lat) || isNaN(lon)) return null;

          const p = feature.properties;
          const isSelected = selectedCamera?.properties?.camera_id === p.camera_id;
          const isSentinel = p.is_sentinel_live;
          const isOffline = p.connectivity_status === 'offline';
          const markerColor = getMarkerColor(p, showAgeingAlerts);

          return (
            <CircleMarker
              key={`cam-${p.camera_id}`}
              center={[lat, lon]}
              radius={isSelected ? 10 : isSentinel ? 8 : (showAgeingAlerts && p.is_ageing_alert) ? 7 : 5.5}
              pathOptions={{
                fillColor: markerColor,
                fillOpacity: 1.0,
                color: isSentinel ? '#0f172a' : isSelected ? '#2563eb' : (showAgeingAlerts && p.is_ageing_alert) ? '#78350f' : '#ffffff',
                weight: isSentinel ? 2.5 : isSelected ? 3 : 1.2,
              }}
              eventHandlers={{
                click: () => onSelectCamera(feature),
              }}
            >
              <Popup>
                <div style={{ fontSize: '12px', minWidth: '230px', fontFamily: 'sans-serif' }}>
                  {isSentinel && (
                    <div style={{
                      display: 'inline-block',
                      backgroundColor: '#eff6ff',
                      color: '#1d4ed8',
                      border: '1px solid #bfdbfe',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: '700',
                      marginBottom: '4px'
                    }}>
                      ⚡ REAL SENTINEL LIVE FEED
                    </div>
                  )}

                  {isOffline && (
                    <div style={{
                      display: 'inline-block',
                      backgroundColor: '#fef2f2',
                      color: '#dc2626',
                      border: '1px solid #fecaca',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: '700',
                      marginBottom: '4px'
                    }}>
                      ⛔ CONNECTION REFUSED: ASSET OFFLINE
                    </div>
                  )}

                  <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '13px', marginBottom: '2px' }}>
                    {p.name}
                  </div>
                  <div style={{ color: '#64748b', fontSize: '11px', marginBottom: '6px' }}>
                    {p.department_name} • {p.city}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '11px', backgroundColor: '#f8fafc', padding: '6px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                    <div><strong>Status:</strong> <span style={{ color: isOffline ? '#dc2626' : markerColor, fontWeight: '700' }}>{p.connectivity_status}</span></div>
                    <div><strong>VMS:</strong> {p.vms_vendor_id}</div>
                    <div><strong>Type:</strong> {p.camera_type}</div>
                    <div><strong>Age:</strong> {p.age_years || '1.5'} yr</div>
                  </div>

                  <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
                    <button
                      onClick={() => onSelectCamera(feature)}
                      style={{
                        flex: 1,
                        backgroundColor: '#f1f5f9',
                        color: '#1e293b',
                        border: '1px solid #cbd5e1',
                        borderRadius: '4px',
                        padding: '6px 8px',
                        fontSize: '11px',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Model 3 Specs
                    </button>

                    {isOffline ? (
                      <button
                        disabled
                        title="Live streaming is disabled because this camera is physically offline"
                        style={{
                          flex: 1.2,
                          backgroundColor: '#f1f5f9',
                          color: '#94a3b8',
                          border: '1px solid #e2e8f0',
                          borderRadius: '4px',
                          padding: '6px 8px',
                          fontSize: '11px',
                          fontWeight: '700',
                          cursor: 'not-allowed',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '4px'
                        }}
                      >
                        ⛔ Stream Offline
                      </button>
                    ) : (
                      <button
                        onClick={() => onOpenLiveStream(feature)}
                        style={{
                          flex: 1.2,
                          backgroundColor: '#2563eb',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '6px 8px',
                          fontSize: '11px',
                          fontWeight: '700',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '4px',
                          boxShadow: '0 1px 3px rgba(37, 99, 235, 0.3)'
                        }}
                      >
                        <Video size={12} color="#ffffff" />
                        Live Stream
                      </button>
                    )}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

      </MapContainer>

      {/* Floating Clean Light Map Legend */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #cbd5e1',
        borderRadius: '8px',
        padding: '12px 16px',
        zIndex: 500,
        fontSize: '11px',
        backdropFilter: 'blur(6px)',
        color: '#0f172a',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ fontWeight: '700', marginBottom: '8px', textTransform: 'uppercase', color: '#475569', fontSize: '10px' }}>
          Map Legend
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ffffff', border: '2.5px solid #0f172a', boxShadow: '0 0 4px rgba(0,0,0,0.3)' }} />
            <span style={{ fontWeight: '700', color: '#0f172a' }}>30 Real Sentinel Live Feeds (White)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span>Online Asset (Live Stream Available)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ef4444' }} />
            <span>Offline Asset (Stream Disabled)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
            <span>Intermittent / Maintenance</span>
          </div>
          {showAgeingAlerts && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f59e0b', border: '1px solid #78350f' }} />
              <span style={{ color: '#92400e', fontWeight: '700' }}>Ageing Equipment (&gt;5yr)</span>
            </div>
          )}
          {showGapZones && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderTop: '1px solid #e2e8f0', paddingTop: '6px', marginTop: '2px' }}>
              <span style={{ width: '10px', height: '10px', border: '2px dashed #dc2626', backgroundColor: 'rgba(220, 38, 38, 0.2)' }} />
              <span style={{ color: '#dc2626', fontWeight: '600' }}>Critical Blind Spot (&lt;10%)</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

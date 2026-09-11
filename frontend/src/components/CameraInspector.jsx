import React from 'react';
import { X, Video, Cpu, MapPin, Layers, ShieldCheck, AlertOctagon, Radio, Globe, AlertTriangle, ShieldX } from 'lucide-react';

export function CameraInspector({ camera, onClose, onOpenLiveStream }) {
  if (!camera) return null;

  const p = camera.properties;
  const coords = camera.geometry.coordinates;
  const isOnline = p.connectivity_status === 'online';
  const isOffline = p.connectivity_status === 'offline';
  const isAgeing = p.age_years && p.age_years >= 5.0;
  const isSentinel = p.is_sentinel_live;

  return (
    <aside style={{
      width: '380px',
      backgroundColor: '#ffffff',
      borderLeft: '1px solid #e2e8f0',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      zIndex: 1000,
      boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.08)',
      overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        backgroundColor: '#f8fafc'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isOnline ? '#10b981' : isOffline ? '#ef4444' : '#f59e0b',
              boxShadow: isOnline ? '0 0 6px #10b981' : isOffline ? '0 0 6px #ef4444' : '0 0 6px #f59e0b'
            }} />
            <span style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: isOnline ? '#059669' : isOffline ? '#dc2626' : '#b45309' }}>
              {p.connectivity_status} • {p.operational_status}
            </span>

            {isSentinel && (
              <span style={{
                fontSize: '10px',
                fontWeight: '700',
                backgroundColor: '#eff6ff',
                color: '#1d4ed8',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid #bfdbfe'
              }}>
                SENTINEL REAL FEED
              </span>
            )}
          </div>

          <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#0f172a', lineHeight: 1.25 }}>
            {p.name}
          </h2>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
            Ref: <code>{p.external_reference}</code> • {p.city}
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          <X size={18} />
        </button>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* On-Demand Live Stream Launch Button / Offline Refusal State */}
        {isOffline ? (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#b91c1c', fontWeight: '700', fontSize: '12px' }}>
              <ShieldX size={16} />
              Connection Refused: Asset Offline
            </div>
            <div style={{ fontSize: '11px', color: '#7f1d1d' }}>
              This physical CCTV unit is unreachable on the network switch. Live RTSP / HLS video streaming is disabled until telemetry reconnects.
            </div>
          </div>
        ) : (
          <button
            onClick={() => onOpenLiveStream(camera)}
            style={{
              backgroundColor: '#2563eb',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 14px',
              fontSize: '13px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 2px 8px rgba(37, 99, 235, 0.35)'
            }}
          >
            <Video size={16} color="#ffffff" />
            🎥 Open Live Stream Player (Model 3)
          </button>
        )}

        {/* Real Sentinel Sandbox Integration Card (if Sentinel camera) */}
        {isSentinel && (
          <div style={{
            backgroundColor: '#eff6ff',
            borderRadius: '8px',
            padding: '12px',
            border: '1px solid #bfdbfe'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              <Radio size={15} color="#2563eb" />
              <h3 style={{ fontSize: '11px', fontWeight: '700', color: '#1d4ed8', textTransform: 'uppercase' }}>
                Sentinel Grid Ingestion Contract
              </h3>
            </div>
            <div style={{ fontSize: '11px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div><strong>RTSP (TCP):</strong> <code>{p.sentinel_rtsp_url}</code></div>
              <div><strong>WebRTC (WHEP):</strong> <code>{p.sentinel_webrtc_url}</code></div>
              <div><strong>HLS M3U8:</strong> <code>{p.sentinel_hls_url}</code></div>
              <div style={{ marginTop: '4px', color: '#1e40af', fontSize: '10px' }}>
                ✓ Frame PTS monotonic timing enforced • Single-feed decode
              </div>
            </div>
          </div>
        )}

        {/* Model 3 VMS Federation Primitives */}
        <div style={{
          backgroundColor: '#f8fafc',
          borderRadius: '8px',
          padding: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <Cpu size={15} color="#2563eb" />
            <h3 style={{ fontSize: '11px', fontWeight: '700', color: '#1e40af', textTransform: 'uppercase' }}>
              Model 3 VMS Federation Primitives
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>VMS Vendor</span>
              <span style={{ fontWeight: '700', color: '#0f172a', textTransform: 'capitalize' }}>
                {p.vms_vendor_id}
              </span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>Stream Protocol</span>
              <span style={{ fontWeight: '700', color: '#0284c7', textTransform: 'uppercase' }}>
                {p.vms_stream_protocol}
              </span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>External VMS ID</span>
              <span style={{ fontWeight: '600', color: '#334155' }}>
                {p.external_camera_id || 'N/A'}
              </span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>Adapter Channel</span>
              <span style={{ fontWeight: '600', color: '#334155' }}>
                {p.adapter_channel || 'ch-01'}
              </span>
            </div>
          </div>
        </div>

        {/* Location & PostGIS Coordinates */}
        <div style={{
          backgroundColor: '#f8fafc',
          borderRadius: '8px',
          padding: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <MapPin size={15} color="#059669" />
            <h3 style={{ fontSize: '11px', fontWeight: '700', color: '#047857', textTransform: 'uppercase' }}>
              PostGIS Spatial Point
            </h3>
          </div>
          <div style={{ fontSize: '12px', color: '#334155', lineHeight: '1.4' }}>
            <div><strong>Lat:</strong> {coords[1].toFixed(6)} | <strong>Lon:</strong> {coords[0].toFixed(6)}</div>
            <div style={{ color: '#64748b', fontSize: '11px', marginTop: '4px' }}>{p.address}</div>
          </div>
        </div>

        {/* Optical Lens Coverage Specs */}
        <div style={{
          backgroundColor: '#f8fafc',
          borderRadius: '8px',
          padding: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Layers size={15} color="#7c3aed" />
            <h3 style={{ fontSize: '11px', fontWeight: '700', color: '#6d28d9', textTransform: 'uppercase' }}>
              Optical Lens Coverage (ST_Buffer)
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>Coverage Radius</span>
              <span style={{ fontWeight: '700', color: '#0f172a' }}>
                {p.coverage_radius_meters} meters
              </span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>Field of View (FOV)</span>
              <span style={{ fontWeight: '700', color: '#0f172a' }}>
                {p.coverage_angle_degrees}°
              </span>
            </div>
          </div>
        </div>

        {/* Ageing & AMC Maintenance Lifecycle */}
        <div style={{
          backgroundColor: isAgeing ? '#fef3c7' : '#f0fdf4',
          borderRadius: '8px',
          padding: '12px',
          border: isAgeing ? '1px solid #f59e0b' : '1px solid #bbf7d0'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            {isAgeing ? <AlertOctagon size={15} color="#d97706" /> : <ShieldCheck size={15} color="#059669" />}
            <h3 style={{ fontSize: '11px', fontWeight: '700', color: isAgeing ? '#92400e' : '#166534', textTransform: 'uppercase' }}>
              {isAgeing ? "Ageing Hardware Alert (>5yr)" : "Hardware Lifecycle Status"}
            </h3>
          </div>
          <div style={{ fontSize: '12px', color: isAgeing ? '#78350f' : '#166534' }}>
            <div><strong>Equipment Age:</strong> {p.age_years || '1.5'} years</div>
            <div><strong>Installed Date:</strong> {p.installed_at || '2023-06-01'}</div>
            <div style={{ marginTop: '4px', fontSize: '11px', color: isAgeing ? '#b45309' : '#15803d' }}>
              {isAgeing 
                ? "⚠️ AMC Warranty Expired: Recommended for Planned Overhaul / EOL Replacement."
                : "✅ Active OEM Warranty & Active AMC Coverage."}
            </div>
          </div>
        </div>

        {/* Department Ownership */}
        <div style={{ fontSize: '12px', color: '#64748b', borderTop: '1px solid #e2e8f0', paddingTop: '12px' }}>
          <div><strong>Department:</strong> {p.department_name} ({p.department_code})</div>
          <div><strong>Access Classification:</strong> {p.access_class}</div>
          <div><strong>Camera Type:</strong> {p.camera_type.toUpperCase()}</div>
        </div>

      </div>
    </aside>
  );
}

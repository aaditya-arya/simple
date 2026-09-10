import React from 'react';
import { Eye, AlertTriangle, Upload, BarChart3, Radio, Shield } from 'lucide-react';

export function Navbar({ 
  selectedPersona, 
  onPersonaChange, 
  selectedCity,
  onCityChange,
  totalCameras, 
  onOpenBulkUpload, 
  onOpenGapModal,
  showCoverageBuffers,
  setShowCoverageBuffers,
  showGapZones,
  setShowGapZones,
  showAgeingAlerts,
  setShowAgeingAlerts
}) {
  return (
    <header style={{
      height: '60px',
      backgroundColor: '#ffffff',
      borderBottom: '1px solid #e2e8f0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      zIndex: 1000,
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)'
    }}>
      {/* Clean Brand Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 6px rgba(37, 99, 235, 0.3)'
        }}>
          <Eye size={20} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '15px', fontWeight: '700', letterSpacing: '-0.3px', color: '#0f172a', margin: 0 }}>
            CCTV Grid Intelligence
          </h1>
          <div style={{ fontSize: '11px', color: '#64748b' }}>
            {totalCameras} Active Camera Nodes Connected
          </div>
        </div>
      </div>

      {/* Layer Toggles & Action Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Toggle 1: Lens Coverage Radii (ST_Buffer visual) */}
        <button
          onClick={() => setShowCoverageBuffers(!showCoverageBuffers)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            border: '1px solid',
            backgroundColor: showCoverageBuffers ? '#dbeafe' : '#f8fafc',
            borderColor: showCoverageBuffers ? '#3b82f6' : '#cbd5e1',
            color: showCoverageBuffers ? '#1e40af' : '#475569',
            transition: 'all 0.15s ease'
          }}
          title="Toggle 75m-150m Optical Lens Coverage Radii (ST_Buffer)"
        >
          <Radio size={14} color={showCoverageBuffers ? '#1e40af' : '#64748b'} />
          Coverage Lenses
        </button>

        {/* Toggle 2: Visual Gap-Analysis Zones */}
        <button
          onClick={() => setShowGapZones(!showGapZones)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            border: '1px solid',
            backgroundColor: showGapZones ? '#fee2e2' : '#f8fafc',
            borderColor: showGapZones ? '#ef4444' : '#cbd5e1',
            color: showGapZones ? '#991b1b' : '#475569',
            transition: 'all 0.15s ease'
          }}
          title="Highlight Municipal Uncovered Zones & Critical Gap Polygons"
        >
          <AlertTriangle size={14} color={showGapZones ? '#991b1b' : '#64748b'} />
          Gap-Analysis Overlay
        </button>

        {/* Toggle 3: Ageing Hardware Filter */}
        <button
          onClick={() => setShowAgeingAlerts(!showAgeingAlerts)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            border: '1px solid',
            backgroundColor: showAgeingAlerts ? '#fef3c7' : '#f8fafc',
            borderColor: showAgeingAlerts ? '#f59e0b' : '#cbd5e1',
            color: showAgeingAlerts ? '#92400e' : '#475569',
            transition: 'all 0.15s ease'
          }}
          title="Highlight cameras > 5 years old nearing AMC expiration"
        >
          <Shield size={14} color={showAgeingAlerts ? '#92400e' : '#64748b'} />
          Ageing Hardware (&gt;5yr)
        </button>

        {/* Action: Gap Report Modal */}
        <button
          onClick={onOpenGapModal}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: '#059669',
            borderColor: '#047857',
            color: '#ffffff',
            border: '1px solid #059669',
            boxShadow: '0 1px 4px rgba(5, 150, 105, 0.2)'
          }}
        >
          <BarChart3 size={14} color="#ffffff" />
          Gap Analysis Matrix
        </button>

        {/* Action: Bulk Onboarding */}
        <button
          onClick={onOpenBulkUpload}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: '#2563eb',
            borderColor: '#1d4ed8',
            color: '#ffffff',
            border: 'none',
            boxShadow: '0 2px 6px rgba(37, 99, 235, 0.3)'
          }}
        >
          <Upload size={14} color="#ffffff" />
          Bulk Onboard (CSV)
        </button>
      </div>

      {/* Right Side: City Filter & Persona Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* City Filter */}
        <div>
          <div style={{ fontSize: '10px', color: '#64748b', fontWeight: '700' }}>CITY FILTER</div>
          <select
            value={selectedCity}
            onChange={(e) => onCityChange(e.target.value)}
            style={{
              backgroundColor: '#f8fafc',
              color: '#0f172a',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            <option value="all">🗺️ All Gujarat (Statewide)</option>
            <option value="Ahmedabad">Ahmedabad</option>
            <option value="Gandhinagar">Gandhinagar</option>
            <option value="Surat">Surat</option>
            <option value="Vadodara">Vadodara</option>
            <option value="Rajkot">Rajkot</option>
            <option value="Bhavnagar">Bhavnagar</option>
            <option value="Jamnagar">Jamnagar</option>
          </select>
        </div>

        {/* Persona Switcher */}
        <div>
          <div style={{ fontSize: '10px', color: '#64748b', fontWeight: '700' }}>DEPARTMENT VIEW</div>
          <select
            value={selectedPersona}
            onChange={(e) => onPersonaChange(e.target.value)}
            style={{
              backgroundColor: '#f8fafc',
              color: '#0f172a',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            <option value="all">🏢 Super Admin (All Assets)</option>
            <option value="1">🚦 Traffic Police Department</option>
            <option value="2">🏛️ Municipal Corporation (AMC/SMC)</option>
            <option value="4">👮 State Police Surveillance</option>
            <option value="3">🚌 State Transport & Transit</option>
            <option value="5">🏙️ GUDA Gandhinagar</option>
          </select>
        </div>
      </div>
    </header>
  );
}

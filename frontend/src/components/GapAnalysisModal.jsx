import React, { useEffect, useState } from 'react';
import { X, BarChart3, AlertOctagon, TrendingUp, Shuffle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { fetchGapAnalysis } from '../services/api';

export function GapAnalysisModal({ isOpen, onClose, selectedDeptId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchGapAnalysis(selectedDeptId === 'all' ? null : selectedDeptId).then((res) => {
        setData(res);
        setLoading(false);
      });
    }
  }, [isOpen, selectedDeptId]);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.65)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2500,
      backdropFilter: 'blur(5px)'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #cbd5e1',
        borderRadius: '12px',
        width: '840px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#f8fafc'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: '#059669',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <BarChart3 size={18} color="#ffffff" />
            </div>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#0f172a' }}>
                Spatial Gap-Analysis & Multi-Department Surveillance Matrix
              </h2>
              <p style={{ fontSize: '12px', color: '#64748b' }}>
                Statewide Gujarat Coverage Densities, Blind-Spot Buffers & Department Redundancies
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
          
          {loading || !data ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontSize: '14px' }}>
              Computing PostGIS ST_Buffer intersection density across Gujarat cities...
            </div>
          ) : (
            <>
              {/* Metric Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                <div style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', display: 'block', textTransform: 'uppercase' }}>
                    State Surveillance Area
                  </span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: '#0f172a', marginTop: '2px', display: 'block' }}>
                    {data.total_surveillance_area_sq_km} km²
                  </span>
                </div>

                <div style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', display: 'block', textTransform: 'uppercase' }}>
                    Optical Covered Area
                  </span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: '#059669', marginTop: '2px', display: 'block' }}>
                    {data.total_covered_area_sq_km} km²
                  </span>
                </div>

                <div style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', display: 'block', textTransform: 'uppercase' }}>
                    Average City Density
                  </span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: '#2563eb', marginTop: '2px', display: 'block' }}>
                    {data.overall_city_coverage_percentage}%
                  </span>
                </div>

                <div style={{ backgroundColor: '#fef3c7', padding: '14px', borderRadius: '8px', border: '1px solid #fde68a' }}>
                  <span style={{ fontSize: '11px', color: '#92400e', fontWeight: '700', display: 'block', textTransform: 'uppercase' }}>
                    Ageing Assets (&gt;5yr)
                  </span>
                  <span style={{ fontSize: '20px', fontWeight: '800', color: '#b45309', marginTop: '2px', display: 'block' }}>
                    {data.ageing_risk_summary?.over_5_years_amc_expired || 124}
                  </span>
                </div>
              </div>

              {/* Zone Breakdown Table with High Readability */}
              <div>
                <h3 style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', textTransform: 'uppercase', marginBottom: '10px', letterSpacing: '0.3px' }}>
                  Municipal & Highway Surveillance Zone Matrix
                </h3>
                <div style={{ border: '1px solid #cbd5e1', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                    <thead style={{ backgroundColor: '#f1f5f9', color: '#334155', borderBottom: '1px solid #cbd5e1' }}>
                      <tr>
                        <th style={{ padding: '10px 14px', fontWeight: '700' }}>Surveillance Corridor / Zone</th>
                        <th style={{ padding: '10px 14px', fontWeight: '700' }}>Area</th>
                        <th style={{ padding: '10px 14px', fontWeight: '700' }}>Active Cams</th>
                        <th style={{ padding: '10px 14px', fontWeight: '700', width: '170px' }}>Coverage Density</th>
                        <th style={{ padding: '10px 14px', fontWeight: '700' }}>Status</th>
                        <th style={{ padding: '10px 14px', fontWeight: '700' }}>Required Expansion</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.identified_gap_zones?.map((zone, idx) => {
                        const isCrit = zone.gap_severity === 'Critical Gap';
                        const isMod = zone.gap_severity === 'Moderate Gap';
                        const rowBg = idx % 2 === 0 ? '#ffffff' : '#f8fafc';

                        return (
                          <tr key={zone.zone_id} style={{ borderTop: '1px solid #e2e8f0', backgroundColor: rowBg }}>
                            <td style={{ padding: '12px 14px', fontWeight: '700', color: '#0f172a' }}>
                              {zone.zone_name}
                            </td>
                            <td style={{ padding: '12px 14px', color: '#475569' }}>
                              {zone.estimated_area_sq_km} km²
                            </td>
                            <td style={{ padding: '12px 14px', color: '#0f172a', fontWeight: '600' }}>
                              {zone.active_cameras_count}
                            </td>
                            <td style={{ padding: '12px 14px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{
                                  flex: 1,
                                  height: '8px',
                                  borderRadius: '4px',
                                  backgroundColor: '#e2e8f0',
                                  overflow: 'hidden'
                                }}>
                                  <div style={{
                                    height: '100%',
                                    width: `${Math.min(100, zone.coverage_percentage)}%`,
                                    backgroundColor: isCrit ? '#dc2626' : isMod ? '#f59e0b' : '#10b981',
                                    borderRadius: '4px'
                                  }} />
                                </div>
                                <span style={{
                                  fontSize: '11px',
                                  fontWeight: '700',
                                  color: isCrit ? '#dc2626' : isMod ? '#b45309' : '#047857',
                                  minWidth: '35px'
                                }}>
                                  {zone.coverage_percentage}%
                                </span>
                              </div>
                            </td>
                            <td style={{ padding: '12px 14px' }}>
                              <span style={{
                                padding: '4px 8px',
                                borderRadius: '999px',
                                fontSize: '11px',
                                fontWeight: '700',
                                backgroundColor: isCrit ? '#fee2e2' : isMod ? '#fef3c7' : '#d1fae5',
                                color: isCrit ? '#991b1b' : isMod ? '#92400e' : '#065f46',
                                border: isCrit ? '1px solid #fecaca' : isMod ? '1px solid #fde68a' : '1px solid #a7f3d0'
                              }}>
                                {zone.gap_severity}
                              </span>
                            </td>
                            <td style={{ padding: '12px 14px', fontWeight: '600', color: isCrit ? '#dc2626' : '#475569' }}>
                              + {zone.recommended_new_cameras} cameras
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Department Overlap & Redundancy Matrix */}
              <div style={{
                backgroundColor: '#eff6ff',
                borderRadius: '8px',
                padding: '16px',
                border: '1px solid #bfdbfe'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                  <Shuffle size={18} color="#2563eb" />
                  <h3 style={{ fontSize: '13px', fontWeight: '700', color: '#1e40af', textTransform: 'uppercase' }}>
                    Multi-Department Redundancy vs Zero-Coverage Matrix (Model 3 Justification)
                  </h3>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {data.department_overlaps?.map((ov, i) => (
                    <div key={i} style={{
                      backgroundColor: '#ffffff',
                      padding: '10px 14px',
                      borderRadius: '6px',
                      border: '1px solid #e2e8f0',
                      fontSize: '12px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <strong style={{ color: '#0f172a' }}>{ov.zone_name}</strong>
                        <span style={{
                          color: ov.overlapping_camera_count > 0 ? '#b45309' : '#dc2626',
                          fontWeight: '700',
                          backgroundColor: ov.overlapping_camera_count > 0 ? '#fef3c7' : '#fee2e2',
                          padding: '2px 8px',
                          borderRadius: '4px'
                        }}>
                          {ov.status} ({ov.overlapping_camera_count} cameras)
                        </span>
                      </div>
                      <div style={{ color: '#475569', fontSize: '11px' }}>
                        {ov.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </>
          )}

        </div>
      </div>
    </div>
  );
}
